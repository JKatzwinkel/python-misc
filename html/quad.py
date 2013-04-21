#!/usr/bin/python
import os
import sys
import re
from math import log as log_nat
from getopt import gnu_getopt
from fnmatch import fnmatch
from time import time

# Global variables holding input data
_names=[] # list of contents
_diskusage={} # computed consumptions of disk space
_baseurl = 'file://' #'https://192.168.178.1/wiki/doku.php?id=' # prefix URL for links
_root = '.' # root directory, where visualization recursion begins
# dictionary of Unix-shell wildcards, one of which filenames must match
# Unix wildcards (globs) passed as command line arguments are used as keys,
# storing their respective function as values. Those would be:
#             include   exclude
# match dir     2         3
# match file    4         5
# match both    6         7
# so if the lowest bit is set, it means filter out, second and third bit
# indicate that it is about directories or files respectively.
# TODO this means we need an additional option to specify wildcards
# for files/firectories to exclude with
_globs = {'.*': 7} # default: filter out hidden files and directories
_delimiter = os.sep # alternative delimiter as replacement for OS filesep
_out = sys.stdout # output destination
_maxdepth = 10 # max depth within which directories and files are display candidates
# table dimensions
table_width=800
table_height=600
# pre-calculate file size to font class mapping on log scale 
# (font size ranges from 1 to 7 inclusive)
# not necessary! drink less!
# fontsize_classes=[0]+[2**i for i in range(8,20,2)]


# ======== USER INPUT SECTION ======== #

# Print help message
def print_help():
	#TODO: options for including and excluding both files and directories
	# by passing multiple wildcards respectively
	#TODO: proper handling of Hyperlink template
	#TODO: baseurl default: file://
	print 'USAGE:'
	print '	{0} <directory> [OPTIONS] [<glob>]'.format(sys.argv[0])
	print '''
OPTIONS:
	-a, --all
		Display hidden files.

	-o, --output <file>
		Instead of printing to STDOUT, save output to file.

	-d, --delimiter C
		When using paths in hyperlinks, replace the system's file separator with
		custom delimiter C.

	-m, --max-depth N
		Limit displayed content to subdirectories within given depth N.
		Default is 10.

	-h, --help
		Show this help message and quit.

	-n, --name <glob>
		Supplies a Unix shell-style wildcard expression (e.g. *.txt)
		that determines which files will be represented in HTML output.
		This option is not required for specifying file name patterns.
		Wildcard expressions may be listed as sole arguments as well.

	-o, --output <file>
		Write output to <file> instead of STDOUT

	--width <pixel|percent%>
		Sets width of generated table to passed argument.

	--height <pixel>
		Sets height of generated table to passed argument.
		Because table doesn't inherit its height attribute, percentage
		values are not appliable here.
	'''

# Parse command-line arguments
def read_argv(argv):
	# default filename filter allow all but hidden files.
	# Check if there are actually any arguments at all:
	if len(argv) > 1:
		_root = os.path.abspath(argv[1])
		# remove trailing file separator
		# if path doesn't point to a directory, terminate
		if not os.path.isdir(_root):
			print >> sys.stderr, 'Error: not a directory'
			print >> sys.stderr, 'First argument must specify the directory to work with'
			print_help()
			exit(2)
		# process through command line arguments
		# using getopt, because unlike argparse, its in stdlib of Python 2.6.6
		# getopt function gnu_getopt allows to mix options and non-option arguments
		# (getopt.getopt aborts parsing when non-option arguments occur)
		try:
			opts, args = gnu_getopt(argv[2:], "ham:d:o:",
				["name=", "output=", "delimiter=", "help", "all", "width=", "height="])
		except:
			print_help()
			exit(2)
		# loop through known options and their arguments
		for opt, arg in opts:
			if opt in ('-h', '--help'):
				# help message, terminate
				print_help()
				exit()
			elif opt in ('-a', '--all'):
				# accept hidden files
				# deactivate hidden-file wildcard
				_globs['.*'] = 0
			elif opt in ('-n', '--name'):
				# filter filenames, accept only files that match expression
				# default is '*'
				# set 'file bit' for retrieved wildcard
				glob = _globs.get(arg, 0)
				if glob & 4 != 4:
					_globs[arg] = glob+4
			elif opt in ('-m', '--max-depth'):
				# assign passed number to _maxdepth (maximum depth to render)
				globals()['_maxdepth'] = len(_root.split(os.sep)) + int(arg)
			elif opt in ('-d', '--delimiter'):
				# change custom delimiter for full-path labels/links
				# from OS file separator to passed character
				globals()['delimiter'] = arg[0]
			elif opt in ('-o', '--output'):
				# assign output destination (filename or whatever...)
				# default is sys.stdout
				globals()['_out'] = arg
			elif opt in ('-u', '--baseurl'):
				# pass a URL that hyperlinks in output will be modeled on
				pass
			elif opt == '--width':
				globals()['table_width'] = arg
			elif opt == '--height':
				globals()['table_height'] = arg
		# assume that standalone arguments are meant to be file name wildcards
		if len(args) > 0:
			# consider remaining arguments wildcards passed to include files
			for arg in args:
				glob = _globs.get(arg, 0)
				if glob & 4 != 4:
					_globs[arg] = glob+4

		globals()['_root'] = _root






# ===== FILE/DIRECTORY FILTERING SECTION ======
#            preserve  discard
# match dir     2         3
# match file    4         5
# match both    6         7

# populates four lists with specific subsets of the known
# wildcards, thus making it easier to access the relevant
# wildcard sets for tests like if a filename may be shown
# or has to be hid or similar.
# these lists, while locally created, are written to the global
# namespace directly, to ensure the dependent functions will
# find them
def init_wildcards():
	ns=globals()
	# list of all wildcards which will remove matching directories
	ns['discard_dir_globs'] = [glob for glob, mode in _globs.items() if mode & 3 == 3]
	#list of all wildcards which will preserve matching directories
	ns['keep_dir_globs'] = [glob for glob, mode in _globs.items() if mode & 3 == 2]
	# List of all wildcards which will remove matching files
	ns['discard_file_globs'] = [glob for glob, mode in _globs.items() if mode & 5 == 5]
	# List of wildcards that will preserve matching files
	ns['keep_file_globs'] = [glob for glob, mode in _globs.items() if mode & 5 == 4]

	#print >> sys.stderr, "discard dirnames: ", discard_dir_globs
	#print  >> sys.stderr, "preserve dirnames: ", keep_dir_globs
	#print  >> sys.stderr, "discard filenames: ", discard_file_globs
	#print  >> sys.stderr, "preserve filenames: ", keep_file_globs


# Determinde whether a directory will be discarded or not.
# First, check if its name matches any preserving wildcards, if it does,
# or if there are no preserving wildcards,
# check if dir name matches any discarding wildcards. If it does, it
# will be discarded.
def discard_dir(dirname):
	return len(keep_dir_globs)>0 and \
		all(map(lambda glob: not fnmatch(dirname, glob), keep_dir_globs)) or \
		any(map(lambda glob: fnmatch(dirname, glob), discard_dir_globs))

# Determine whether an entire path has to be omitted.
# tests every dir name in a path against discarding conditions.
# If any of those apply, the path will be discarded.
# One of said conditions is exceeding the maximal depth.
# TODO formerly, monitoring the path depth was done during the file tree
# traversal for a reason; like this, the disk space consumption
# of deeper directories is not taken into account...
def discard_path(path):
	dirs = path.split(os.sep)[1:]
	return len(dirs) >= _maxdepth or any(map(lambda d: discard_dir(d), dirs))


# Check if filename has to be discarded
# If preserving wildcards are set and we still don't match a single one of them,
# discard.
# Otherwise, and if only one of the discarding wildcards matches, discard.
# back to lists
def discard_file(filename):
	return len(keep_file_globs) > 0 and \
		all(map(lambda glob: not fnmatch(filename, glob), keep_file_globs)) or \
		any(map(lambda glob: fnmatch(filename, glob), discard_file_globs))


# Filters a [(path, subdirs[], files[]), ...] list like os.walk() returns.
# Entries on paths that contain forbidden dir names are removed.
# The remaining will have their subdirs and files lists checked and
# cleared out accordingly.
def filtered(entries):
	results = []
	remaining = filter(lambda entry: not discard_path(entry[0]), entries)
	for path, subdirs, files in remaining:
		subdirs = filter(lambda dir: not discard_dir(dir), subdirs)
		files = filter(lambda fn: not discard_file(fn), files)
		results.append( (path, subdirs, files) )
	return results



# ====== FILE TREE PARSING FUNCTIONS ======
#TODO: clean up!

# returns contents of directory, including directory itself
def dir_contents(dirname):
        res=[]
        #print dirname
        for d, f, s, mt in _names:
                if f=='':
                        if d.startswith(dirname+os.sep):
                                subs=d[len(dirname)+1:]
                                if subs.count(os.sep) < 1:
                                        res.append((d,f,s,mt))
                if d==dirname:
                        res.append((d,f,s,mt))
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

# Populates and returns a list of all files and directories found under
# the given directory, which match the chosen requirements (hidden files
# yes/no, only files that match Unix wildcards, only files within a
# certain depth, ...).
# The resulting list is sorted by disk space consumption, starting with
# the largest item.
#TODO: unicode stuff
def resources(dirname):
	results=[]
	# if not a directory, return here
	if not os.path.isdir(dirname):
		return results
	# traverse directory tree:
	# walk bottom-up
	# http://docs.python.org/2/library/os.html#os.walk
	for dirname, subdirs, files in filtered(os.walk(dirname, topdown=False)):
		# if directory is located deeper in the file hierarchy that allowed by
		# the command-line argument -m/--max-depth, don't enlist its content,
		# only sum up disk space used. So, check on nesting depth:
		# depth = len(dirname.split(os.sep))
		du = 0
		# compute directory size by summing up disk usage of sub directories
		for sd in subdirs:
			filesize = disk_usage(os.path.join(dirname, sd))
			du += filesize
		# Consider only files satisfying all requirements set
		for fn in files:
			# Summing up disk usage of contained files
			filepath=os.path.join(dirname, fn)
			filesize = disk_usage(filepath)
			du += filesize
			# TODO: reproduce option for stripping filetype extensions or even
			# TODO: label/link/url formatting using field placeholders
			# like %F filename, %f without extension, %s size, %p path etc.
			#
			# only list files if the depth of this directory in the tree is OK
			#if depth < _maxdepth:
			results.append((dirname, fn, filesize, os.path.getmtime(filepath)))
		# only list directory if the depth of its location is small enough
		#if depth <= _maxdepth:
		results.append((dirname, '', du+1, os.path.getmtime(dirname)))
		# save directory disk use in dictionary
		# Because of the recursive disk space computation, even directories that
		# are nested too deep to be displayed have tp register their size
		# TODO Or Have They?? Will those files approved for displayal reach
		# their parent directory's detected disk space consumption???
		#
		# save disk space consumption value in dictionary for lookup by parent
		# +1 : ensure subdirectories are not listed before any of their parents
		_diskusage[dirname] = du+1
	# register disk use of smallest and largest file
	limite=sorted([x[2] for x in results if not x[1]==''])
	globals()['_min_size'] = limite[0]
	globals()['_max_size'] = limite[-1]
	limite=sorted([x[3] for x in results])
	globals()['_oldest'] = limite[0]
	globals()['_newest'] = limite[-1]
	thresh = _oldest+(_newest-_oldest)*19/20
	globals()['_time_threshold'] = filter(lambda x:x>thresh, limite)[0]
	return sorted(results, key=lambda x:x[2], reverse=True)


# simple recursive function that prints the items collected by resources()
# as nested list hierarchical tree representation
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
#TODO: find solution for fucked-up table height rendering in Opera
# could easily be done by setting absolute table height attribute values
#TODO: find solution for unused spaces after last put elements in Chrome
# but how?
#TODO: remaining blank spaces actually occur in Epiphany, too. Only firefox
#fills available space? but anyways, cell dimensions still don't fit!
#TODO: WHY????

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
	globals()['_font_sizes']=[int(round(i**2/2.+8)) for i in range(0,11)]

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

_now = time()
# if file was modified recently, compute marking color
def mark_cell(item):
	if item[3]>=_time_threshold:
		sign = (item[3]-_time_threshold)/(_newest-_time_threshold)
		sign = sign**4
		red = 255
		#print >> sys.stderr, item[3]-_time_threshold
		blue=int(255-80*sign)
		green=int(255-120*sign)
		return 'style="background-color:#{0}{1}{2};"'.format(hex(red)[2:], 
			hex(blue)[2:], hex(green)[2:])
	return ''

# format and echo a label for given path, filename, size of disk usage, and
# indentation level
# TODO: implement template system for custom label formatting via command line
# TODO: implement wrapper method decorate(...space_v...) to print empty cells
# without labels inside
def label((path, filename, diskuse, modtime), level, visible=2):
	ns = _delimiter.join(path.split(os.sep)+[''])
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
	#TODO: 
	# http://stackoverflow.com/questions/2922295/calculating-the-pixel-size-of-a-string-with-python
	# if cell too narrow, shorten label!
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
	#element = '<font size="{0}pt" dir="LTR">{1}</font>'.format(
	#							font_size(diskuse), cell_content)
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
		#TODO: calculate actual text size with PIL
		show=2
		if len(entry[1])*fs*.7 > width:
			show=1
		if width<fs*min(len(entry[1]),7)*.3:
			show=0
		if fs*1.7 > height:
			show=0
		label(entry, level+1, visible=show)


# optimized layout
# TODO: think about placing file items reverly, thus
# beginning with the smallest files and granting the largest one
# whatever is left in the layout space. That way, unplanned
# table extension by overflowing text output wouldn't lead to
# the smallest file item ending up with the most space sometimes.
def table(dirname, level=0, width='100%', height='100%'):
	items = largest(dirname)
	if len(items) < 1:
		print "None"
		return
	print indent(level), '<!--', width, height, '-->'
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
	namespaces = dirname.split(os.sep)
	if len(namespaces) > 1 and level > 0:
		print indent(level+1)+'<span class="hidden"><a href="{0}">{1}</a></span>'.format(
			'/'.join(namespaces), namespaces[-1])
	# Generate table layout
	if len(items)>1:
		compute_layout(items, level+1, width, height)
	print indent(level)+'</table>'


# precompute cells layout optimized for space use,
# then actually write html output with according span attributes
# pass [(path, filename, size), ] list as items
#TODO: find out why final items are shown in wrong size
#TODO: think about grid layout for items of similar size
def compute_layout(items, level, width, height):
	# process variables
	stack = []
	space_h = 1.
	space_v = 1.
	# horizontal layout in favor at small tables
	# TODO: adjust
	h_favor = 4.-2.7*(width / globals()['table_width'])
	print indent(level), '<!--', h_favor, width, globals()['table_width'], height, '-->'
	# determining total namespace sapce
	directory, _, full_size, _ = items.pop(0)

	# precompute cell layout and size
	#TODO: also precompute cell labels to know if cell will be wide enough
	for path, filename, size, modtime in items:
		ratio = float(size) / full_size
		print "<!-- ", path, filename, size, full_size, 'ratio:', ratio, "-->"

		if space_h*width > space_v*height*h_favor and space_h*width*ratio > len(filename)*font_size(size)*.7:
			cover = space_h * ratio
			print indent(level), "<!-- horizontal space available: {0}; being covered: {1} -->".format(space_h, cover)
			space_h -= cover
			stack.append( ('td', cover) )
		else:
			cover = space_v * ratio
			print indent(level), "<!-- vertical space available: {0}; being covered: {1} -->".format(space_v, cover)
			space_v -= cover
			stack.append( ('tr', cover) )
		full_size -= size
	#print indent(level), '<!-- ', full_size, '-->'
	if len(stack)>1:# and 
		if stack[-2][0] == 'td' and stack[-1][0] != 'td':
			stack[-1]=('td', 1.-sum([x[1] for x in stack if x[0]=='td'])) #stack[-1][1])
		else:
			if stack[-1][0] != 'tr':
				stack[-1]=('tr', 1.-sum([x[1] for x in stack if x[0]=='tr']))

	space_h=1.
	space_v=1.
	# output templates
	#TODO: make class extendable
	tag_column='<td class="tooltip" {0}width="{1:.0f}%">'
	tag_row = '<td class="tooltip" {0}height="{1:.0f}%">'
	tr_tag_open=False
	# write cell layout HTML output
	for item in items:
		tag, dim = stack.pop(0)
		# do not assign dimension value to last item
		# TODO: cell dimensions don't fit relative files sizes
#		if len(stack) < 1:
#			tag='td'
		print indent(level), '<!--', space_h, space_v, '-->'
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
			span+=mark_cell(item)
			print indent(level+1)+tag_column.format(span, dim*100)
			recurse(item, level+1, dim*width, space_v*height)
			space_h-=dim
			print indent(level+1)+'</td>'
		else:
			if not tr_tag_open:
				print indent(level)+'<tr>'# height={0:.0f}>'.format(dim*height)
			cspan = len(filter(lambda cell:cell[0]=='td', stack))+1
			span = ('', 'colspan="{0}" '.format(cspan))[int(cspan>1)]
			span+=mark_cell(item)
			print indent(level+1)+tag_row.format(span, dim*100)
			recurse(item, level+1, space_h*width, dim*height)
			space_v-=dim
			print indent(level+1)+'</td>'
			tr_tag_open=False
			print indent(level)+'</tr>'
	# done:
	if tr_tag_open:
		print indent(level)+'</tr>'










# ===== MAIN PART ======

# === Begin Processing input data ===
# Assign Variables, read Command-line Arguments
read_argv(sys.argv)
init_wildcards() # set up environment for resource name matching with wildcards

# compute list of files and directories, their hierarchy and disk usage amount
_names = resources(_root)
init_log_scale() # set up log scale for label font sizes

if _out != sys.stdout: # set output destination
	outputfile = open(_out, 'w')
	sys.stdout = outputfile


# assemble HTML output
print '''<!doctype html>
<head>
	<style type="text/css">'''
#TODO: read number of font size classes from argv?
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
  		display: block;
  		line-height: 4px;
		}
		a:visited, a:hover {
			color: #171;
		}
		td:hover {
			background-color: #F0FFE0;
		}
		td.modified:hover {
			background-color: #F0C0D0;
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
<div width="100%" height="600" align="center" style="padding:30px">'''
#print '<!--', _names, '-->'
print '<h4>Showing contents of: "{0}"</h4>'.format(_root)
print '<i>{0}</i>'.format(sys.argv)
# print 'smallest: {0}, largest: {1}, scale: {2}'.format(_min_size, _max_size, _log_scale)
# TODO: handle default height value, since table does not inherit height
print '<table width="{0}" height="{1}"><tr><td>'.format(table_width, table_height)
table(_root, 0, table_width, table_height)
print '</td></tr></table>'
print '''</div>
</body>'''
