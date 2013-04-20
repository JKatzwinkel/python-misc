#!/usr/bin/python
import os
import sys
import cgi
from math import log as log_nat

_names=[]
_diskusage={}
_baseurl = 'https://192.168.178.1/wiki/doku.php?id='
_documentroot = '/media/Data/Codes/Python/python-misc/'
_filetypes=['txt', 'xml', 'py', 'html']

# http://wiki.python.org/moin/HowTo/Sorting/
# http://stackoverflow.com/questions/955941/how-to-identify-whether-a-file-is-normal-file-or-directory-using-python
# http://stackoverflow.com/questions/1392413/calculating-a-directory-size-using-python

# is extension of given file of interest?
def valid_filetype(filename):
	return any(map(lambda ext:filename.endswith('.'+ext), _filetypes))

# checks if any of the path nodes is a hidden dir
def valid_dir(path):
	return not any(map(lambda x:x.startswith('.'), path.split(os.sep)))

# return filename without extension
def basename(filename):
	if filename.count('.')>0:
		return '.'.join(filename.split('.')[:-1])
	return filename

# returns contents of directory, including directory itself
def dir_contents(dirname):
        res=[]
        if dirname==':':
                dirname=''
        for d, f, s in _names:
                if f=='':
                        if d.startswith(dirname):
                                subs=d[len(dirname):]
                                if subs.count(':') == 1:
                                        res.append((d,f,s))
                if d==dirname:
                        res.append((d,f,s))
        return res


# For the specified directory, return a list of the contained files ans
# immediate subdirectories, sorted by disk space consumption and
# beginning with the directory itself, followed by its largest child
def largest(dirname):
        res = sorted(dir_contents(dirname), key=lambda x:x[1] != '')
        return res


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
		if valid_dir(dirname):
			du = 0
			# disk usage of sub directories
			for sd in filter(valid_dir, subdirs):
				filesize = disk_usage(os.path.join(dirname, sd))
				du += filesize
			 #disk usage of contained files
			for fn in filter(valid_filetype, files):
				filesize = disk_usage(os.path.join(dirname, fn))
				du += filesize
				results.append( (relpath(dirname), basename(fn), filesize) )
			results.append( (relpath(dirname), '', du) )
			# save directory disk use in dictionary
			_diskusage[dirname] = du
	limite=sorted([x[2] for x in results if not x[1]==''])
	globals()['_min_size'] = limite[0]
	globals()['_max_size'] = limite[-1]
	return sorted(results, key=lambda x:x[2], reverse=True)



# ========== RENDERING SECTION =========== #
# return logarithm on base 2
def log(x):
	return log_nat(x)/log_nat(2)


_font_classes=5.
# prepare global constraints for file size <-> font size mapping
# scale
# map 10 steps in font size to file sizes
def init_log_scale():
	globals()['_log_scale']=_font_classes/(log(_max_size)-log(_min_size)+1)
	globals()['_min_size']=log(_min_size)
	globals()['_max_size']=log(_max_size)
	globals()['_font_sizes']=[i+9 for i in range(0,11)]


# returns a whitespace-only string of a certain length that can be used
# to indent output
def indent(level):
	return '  '*level


# return font size in which a file of given size will be labeled in html
def font_size(diskuse):
	#return int(min(8,max(0,log(diskuse)/2-3)+1))
	return 1+int((log(diskuse)-_min_size)*_log_scale)


# return the css font class in which a label for a file of given size should be printed
def font_class(diskuse):
	return 'size{0}'.format(font_size(diskuse)-1)


# format and echo a label for given path, filename, size of disk usage, and
# indentation level
def label((path, filename, diskuse), level, visible=2):
	ns = ':'.join(path.split(':')[1:]+[''])
	link = '<a href="{0}">{1}</a>'
	href = _baseurl + ns + filename
	if visible>1:
		label = filename
	else:
		if visible>0:
			if len(filename)>6:
				label = '{0}..{1}'.format(filename[:3], filename[-2:])
			elif len(filename)>4:
				label = filename[:2]+'..'
			else:
				label = filename
		else:
			label='.'
	if diskuse == 0:
		diskuse = 10
	cell_content=link.format(href, label)
	if diskuse>1024:
		if diskuse>1024*1024:
			cell_diskuse = '{0:.1f} MB'.format(diskuse/1024./1024)
		else:
			cell_diskuse = '{0:.1f} KB'.format(diskuse/1024.)
	else:
		cell_diskuse = '{0} B'.format(str(diskuse))
	if diskuse > 1024*500: 
		cell_content = "{0} ({1})".format(cell_content, cell_diskuse)
	else:
		cell_content = "{0}".format(cell_content)
	if visible>0:
		element = '<span dir="LTR" class="{1}">{0}</span>'.format(cell_content, font_class(diskuse))
#	elif visible>0:
#		element = '<span dir="LTR" class="size0">{0}</span>'.format(cell_content)
	else:
		element = '<span dir="LTR" class="dots">{0}</span>'.format(cell_content)
	print indent(level)+'<ul class="hidden"><li><span dir="LTR" class="size3">{0}</span></li>'.format(filename)
	print indent(level)+'<li><span dir="LTR" class="size2">{0}</span></li></ul>'.format(cell_diskuse)
	print indent(level)+element


# recurse:
# If recursion did not arrive a leaf node (file) yet, decide which layout
# the nested table is supposed to be aligned in (horizontal or vertical).
# If further recursion is not possible, create label indicating which leaf
# recursion terminates.
def recurse(entry, level, width, height):
	if entry[1] == '':
		# space_h and space_v
		table(entry[0], level+2, width, height)
	else:
		fs=_font_sizes[font_size(entry[2])-1]
		show=2
		if len(entry[1])*fs*.7 > width:
			show=1
		if width<fs*min(len(entry[1]),7)*.5:
			show=0
		if fs*1.7 > height:
			show=0
		label(entry, level+1, visible=show)


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
		globals()['table_height'] = float(height)
	# label table:
	namespaces = dirname.split(':')
	if len(namespaces) > 1 and level > 0:
		print indent(level+1)+'<span class="hidden"><a href="{0}">{1}</a></span>'.format(
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
	tag_column='<td class="tooltip" {0}width="{1:.0f}%">'
	tag_row = '<td class="tooltip" {0}height="{1:.0f}%">'
	tr_tag_open=False
	# determining total namespace sapce
	directory, _, full_size = items.pop(0)

	# precompute cell layout and size
	for path, filename, size in items:
		ratio = float(size) / full_size
		if space_h*width > space_v*height*h_favor and space_h*width*ratio > len(filename)*font_size(size)*.7:
			cover = space_h * ratio
			space_h -= cover
			stack.append( ('td', cover) )
		else:
			cover = space_v * ratio
			space_v -= cover
			stack.append( ('tr', cover) )
		full_size -= size
	if len(stack)>1:# and 
		if stack[-2][0] == 'td' and stack[-1][0] != 'td':
			stack[-1]=('td', 1.-sum([x[1] for x in stack if x[0]=='td'])) #stack[-1][1])
		else:
			if stack[-1][0] != 'tr':
				stack[-1]=('tr', 1.-sum([x[1] for x in stack if x[0]=='tr']))

	space_h=1.
	space_v=1.
	# write cell layout HTML output
	for item in items:
		tag, dim = stack.pop(0)
		print indent(level), '<!--', item, tag, dim, '-->'
		if tag == 'td':
			if not tr_tag_open:
				tr_tag_open=True
				upcoming_rows=filter(lambda x:x[0]=='tr',stack)
				if len(upcoming_rows)>0:
					row_dim=upcoming_rows[0][1]
				else:
					row_dim=space_v
				print indent(level)+'<tr height="{0:.0f}%">'.format(row_dim*100)
			# TODO: optimize for speed?
			rspan = len(filter(lambda cell:cell[0]=='tr', stack))+1
			span = ('', 'rowspan="{0}" '.format(rspan))[int(rspan>1)]
			print indent(level+1)+tag_column.format(span, dim*100)
			recurse(item, level+1, dim*width, space_v*height)
			space_h-=dim
			print indent(level+1)+'</td>'
		else:
			if not tr_tag_open:
				print indent(level)+'<tr>'
			cspan = len(filter(lambda cell:cell[0]=='td', stack))+1
			span = ('', 'colspan="{0}" '.format(cspan))[int(cspan>1)]
			print indent(level+1)+tag_row.format(span, dim*100)
			recurse(item, level+1, space_h*width, dim*height)
			space_v-=dim
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
init_log_scale() # set up log scale for label font sizes

print '''Content-Type: text/html

<!doctype html>
<head>
	<style type="text/css">'''
for i,px in enumerate(_font_sizes):
	print '		.size{0} {{'.format(i)
	print '			font-size: {0}px;'.format(px)
	print '		}'
print '''
		span.dots {
			line-height: 1px;
			height: 3px;
			display: block;
		}
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
			background-color: #C0E0FF;
		}
		table.namespace {
			background-color: #99D;
		}
		table.namespace:hover {
			background-color: #B0A0FF;
		}
		ul.hidden {
			list-style-type:none;
			align: left;
		}
		.tooltip > .hidden,
		.tooltip > .hidden > a {
			display: none;
		}
		.tooltip:hover > .hidden,
		.tooltip:hover > .hidden > a	{
			display: block;
			position: absolute;
			font-size: 8pt;
			background-color: #FFF;
			border: 1px solid #CCC;
			margin: 20px 10px;
		}
		.tooltip:hover > span.hidden a {
			text-decoration: none;
			color: #33A;
		}
		table:hover[class~=tooltip] > span.hidden {
			background-color: #FDD;
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



