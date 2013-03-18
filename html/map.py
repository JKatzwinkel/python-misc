#!/usr/bin/python
import os
import sys
import cgi
from math import log10 as log

_names=[]
_diskusage={}
_baseurl = 'https://192.168.178.1/wiki/doku.php?id='
_documentroot = '/var/lib/dokuwiki/data/pages'

# http://wiki.python.org/moin/HowTo/Sorting/
# http://stackoverflow.com/questions/955941/how-to-identify-whether-a-file-is-normal-file-or-directory-using-python
# http://stackoverflow.com/questions/1392413/calculating-a-directory-size-using-python

def is_child_dir(namespace, entry):
	# entry is subdirectory if and only if no separators remain
	# after removing prepending higher directory path
	if entry[1] == '':
		if namespace==':':
			namespace=''
			if not entry[0].startswith(':'):
				entry[0] = ':'+entry[0]
		if entry[0].startswith(namespace+':'):
			return len(':'.join(entry[0].split(namespace+':')[1:]).split(':')) is 1
	return False

# For the specified directory, return a list of the contained files ans
# immediate subdirectories, sorted by disk space consumption and
# beginning with the directory itself, followed by its largest child
def largest(dirname):
	return filter(lambda x:x[0] == dirname or is_child_dir(dirname, x), _names)

# Return disk space consumption of the resource under the given path.
# If referencing a directory, the return value is computed by summing up
# the disk_usage values of the contained resources recursively.
# (That is, look up in the dictionary that has been populated during
# the initial bottom-up tree walk in resources())
# If it is a file, simply return its file size.
def disk_usage(path):
	if os.path.isdir(path):
		return _diskusage.get(path, 0)
	else:
		return os.path.getsize(path)


# makes the given path relative to _documentroot
def relpath(path):
	res = os.path.relpath(path, _documentroot)
	if res == '.':
		return ':'
	return ':'.join(['']+res.split(os.sep))


def resources(dirname):
	results=[]
	if not os.path.isdir(dirname):
		return results
	# walk bottom-up
	for dirname, subdirs, files in os.walk(dirname, topdown=False):
		du = 0
		# disk usage of sub directories
		for sd in subdirs:
			filesize = disk_usage(os.path.join(dirname, sd))
			du += filesize
		 #disk usage of contained files
		for fn in filter(lambda x:x.endswith('.txt'), files):
			filesize = disk_usage(os.path.join(dirname, fn))
			du += filesize
			results.append( (relpath(dirname), fn.split('.txt')[0], filesize) )
		results.append( (relpath(dirname), '', du+1) )
		# save directory disk use in dictionary
		_diskusage[dirname] = du+1
	return sorted(results, key=lambda x:x[2], reverse=True)


def partition(dirname, level=0):
	partitions = largest(dirname)
	if len(partitions) < 1:
		print dirname
		return
	full = partitions[0][2]
	#print " "*level, dirname, full
	for part in partitions[1:]:
		size = part[2]
		if part[1] == '':
			try:
				partition(part[0], level+1)
			except Exception:
				print part, dirname
		else:
			print " "*(level+1), part[1], 100*size/full
		full -= size


# ========== RENDERING SECTION =========== #
# returns a whitespace-only string of a certain length that can be used
# to indent output
def indent(level):
	return '  '*level

# format and echo a label for given path, filename, size of disk usage, and
# indentation level
def label((path, filename, diskuse), level):
	ns = ':'.join(path.split(':')[1:]+[''])
	link = '<a href="{0}">{1}</a>'
	href = _baseurl + ns + filename
	label = filename
	if diskuse == 0:
		diskuse = 10
	cell_content=link.format(href, label)
	if diskuse>1024:
		if diskuse>1024*1024:
			cell_content += ' ({0} MB)'.format(str(diskuse/1024/1024))
		else:
			cell_content += ' ({0} kB)'.format(str(diskuse/1024))
	element = '<font size="{0}pt" dir="LTR">{1}</font>'.format(
								log(diskuse)/2, cell_content)
	print indent(level)+'<span dir="LTR">{0}</span>'.format(filename)
	print indent(level)+element


# recurse:
# If recursion did not arrive a leaf node (file) yet, decide which layout
# the nested table is supposed to be aligned in (horizontal or vertical).
# If further recursion is not possible, create label indicating which leaf
# recursion terminates.
def recurse(entry, level, space_h, space_v):
	if entry[1] == '':
		# space_h and space_v
		table(entry[0], level+2, space_h, space_v)
	else:
		label(entry, level+1)


# optimized layout
def table(dirname, level=0, width='100%', height='100%'):
	items = largest(dirname)
	if len(items) < 1:
		print "None"
		return
	table_tag = '<table width="100%" height="100%" class="tooltip" dir="{0}">'
	print indent(level)+table_tag.format(['RTL', 'LTR'][level%2])
	# handling default dimensions
	# TODO: move size handling stuff somewhere else?
	numeral = lambda s: float(re.findall('[0-9.]*', s)[0])
	# TODO: also, prevent incompatible units: mixing percentage and pixel values
	# should be dismissed
	if type(width) == str:
		width = numeral(width)
	if type(height) == str:
		height = numeral(height)
	# register root table width:
	if globals().get('table_width',0) == 0 or type(globals()['table_width']) == str:
		globals()['table_width'] = float(width)
	if globals().get('table_height',0) == 0 or type(globals()['table_height']) == str:
		globals()['table_height'] = float(width)
	# label table:
	namespaces = dirname.split(':')
	if len(namespaces) > 1 and level > 0:
		print indent(level+1)+'<span><a href="{0}">{1}</a></span>'.format(
			_baseurl+':'.join(namespaces[1:]), namespaces[-1])
	# Generate table layout
	if len(items)>1:
		compute_layout(items, level+1, width, height)
	print indent(level)+'</table>'


# precompute cells layout optimized for space use,
# then actually write html output with according span attributes
# pass [(path, filename, size), ] list as items
def compute_layout(items, level, width, height):
	# process variables
	stack = []
	space_h = 1.
	space_v = 1.
	# horizontal layout in favor at small tables
	# TODO: adjust
	h_favor = 4.-3.*(width / globals()['table_width'])
	print indent(level), '<!--', h_favor, width, globals()['table_width'], '-->'
	# output templates
	tag_column='<td class="tooltip" {0}width="{1}%">'
	tag_row = '<td class="tooltip" {0}height="{1}%">'
	tr_tag_open=False
	# determining total namespace sapce
	directory, _, full_size = items.pop(0)

	# precompute cell layout and size
	for path, filename, size in items:
		ratio = float(size) / full_size
		if space_h*width > space_v*height*h_favor and space_h*width*ratio>len(filename)*6:
			cover = space_h * ratio
			space_h -= cover
			stack.append( ('td', cover) )
		else:
			cover = space_v * ratio
			space_v -= cover
			stack.append( ('tr', cover) )
		full_size -= size
	stack[-1]=('tr', stack[-1][1])

	# write cell layout HTML output
	for item in items:
		tag, dim = stack.pop(0)
		print indent(level), '<!--', item, tag, dim, '-->'
		if tag == 'td':
			if not tr_tag_open:
				tr_tag_open=True
				print indent(level)+'<tr>'
			# TODO: optimize for speed?
			rspan = len(filter(lambda cell:cell[0]=='tr', stack))
			span = ('', 'rowspan="{0}" '.format(rspan))[int(rspan>1)]
			print indent(level+1)+tag_column.format(span, dim*100)
			recurse(item, level+1, dim*width, dim*height)
			print indent(level+1)+'</td>'
		else:
			if not tr_tag_open:
				print indent(level)+'<tr>'
			cspan = len(filter(lambda cell:cell[0]=='td', stack)) + 1
			span = ('', 'colspan="{0} "'.format(cspan))[int(cspan>1)]
			print indent(level+1)+tag_row.format(span, dim*100)
			recurse(item, level+1, dim*width, dim*height)
			print indent(level+1)+'</td>'
			tr_tag_open=False
			print indent(level)+'</tr>'
	# done:
	if tr_tag_open:
		print indent(level)+'</tr>'



# === BEGIN PROCESSING ===

fields = cgi.FieldStorage()
try:
	root = fields['id'].value
	namespaces = root.split(':')
	if len(namespaces) > 2:
		if namespaces[0] == '':
			namespaces.pop(0)
except:
	root = ''
	namespaces=[]

path = os.sep.join(namespaces)
_names = resources(os.path.join(_documentroot, path))

print '''Content-Type: text/html

<!doctype html>
<head>
	<style type="text/css">
		td {
			border: 1px solid;
			background-color: white;
			text-align:center;
			font-family: 'Arial', 'sans serif';
			color: #A33;
			display: table-cell;
			white-space: nowrap;
			word-wrap: break-word;
			text-overflow: ellipsis;
			overflow:hidden;
		}
		a {
			color: #3A3;
			text-decoration: none;
		}
		a:visited, a:hover {
			color: #171;
		}
		td:hover {
			background-color: #F0FFE0;
		}
		table {
			background-color: white;
			padding: 0px;
			margin:0px;
			table-layout: auto;
			cellspacing: 5px;
		}
		table:hover {
			background-color: #F0E0FF;
		}
		table.namespace {
			background-color: #99D;
		}
		table.namespace:hover {
			background-color: #C0C0FF;
		}
		.tooltip > span,
		.tooltip > span > a {
			display: none;
		}
		.tooltip:hover > span,
		.tooltip:hover > span > a {
			display: block;
			position: absolute;
			font-size: 7pt;
			background-color: #FFF;
			border: 1px solid #CCC;
			margin: 20px 10px;
		}
		.tooltip:hover > span a {
			text-decoration: none;
			color: #33A;
		}
	</style>
</head>
<body>
<div width="100%" height="600" align="center">'''
#print '<h3>Namespace {0} ({1})</h4>'.format(root, path)
print '''<table width="800" height="600">
<tr><td>'''
table(':'+root, 0, 800, 600)
print '''</td></tr></table>
</div>
</body>'''



