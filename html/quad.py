#!/usr/bin/python
import os
import sys
import re
from math import log as log_nat
from getopt import gnu_getopt
from fnmatch import fnmatch

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
table_width=1000
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

# Returns True if triple entry represents a directory,
# i.e. looks sth like ('path', '', xL), which is a direct
# subdirectory of directory dirname. False otherwise.
def is_child(dirname, entry):
	# entry is subdirectory if and only if no file seperators remain
	# after removing prepending higher directory path
	if entry[1] == '':
		if entry[0].startswith(dirname+os.sep):
			return len(entry[0].split(dirname+os.sep)[1].split(os.sep)) is 1
	return False

# For the specified directory, return a list of the contained files ans
# immediate subdirectories, sorted by disk space consumption and
# beginning with the directory itself, followed by its largest child
def largest(dirname):
	return filter(lambda x:x[0] == dirname or is_child(dirname, x), _names)

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
			filesize = disk_usage(os.path.join(dirname, fn))
			du += filesize
			# TODO: reproduce option for stripping filetype extensions or even
			# TODO: label/link/url formatting using field placeholders
			# like %F filename, %f without extension, %s size, %p path etc.
			#
			# only list files if the depth of this directory in the tree is OK
			#if depth < _maxdepth:
			results.append((dirname, fn, filesize))
		# only list directory if the depth of its location is small enough
		#if depth <= _maxdepth:
		results.append((dirname, '', du+1)) #TODO: is this save?
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

# return logarithm on base 2
def log(x):
	return log_nat(x)/log_nat(2)

# prepare global constraints for file size <-> font size mapping
# scale
# map 10 steps in font size to file sizes
def init_log_scale():
	globals()['_log_scale']=10./(log(_max_size)-log(_min_size))
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
# TODO: implement template system for custom label formatting via command line
# TODO: implement wrapper method decorate(...space_v...) to print empty cells
# without labels inside
def label((path, filename, diskuse), level, visible=True):
	ns = _delimiter.join(path.split(os.sep)+[''])
	link = '<a href="{0}">{1}</a>'
	href = _baseurl + ns + filename
	label = filename
	if diskuse == 0:
		diskuse = 10
	cell_content=link.format(href, label)
	#TODO: 
	# http://stackoverflow.com/questions/2922295/calculating-the-pixel-size-of-a-string-with-python
	# if cell too narrow, shorten label!
	if diskuse>1024:
		if diskuse>1024*1024:
			cell_diskuse = '{:.1f} MB'.format(diskuse/1024./1024)
		else:
			cell_diskuse = '{:.1f} kB'.format(diskuse/1024.)
	if visible:
		cell_content = "{0} ({1})".format(cell_content, cell_diskuse)
		element = '<span dir="LTR" class="{1}">{0}</span>'.format(cell_content, font_class(diskuse))
	else:
		cell_content = '{0}..{1}'.format(label[:3], label[-3:])
		element = '<span dir="LTR" class="size0">{0}</span>'.format(cell_content)
	#element = '<font size="{0}pt" dir="LTR">{1}</font>'.format(
	#							font_size(diskuse), cell_content)
	# <font> has been deprecated since HTML 4.0! We will use css style as of now
	print indent(level)+'<span dir="LTR" class="hidden size3">{0}</span>'.format(filename)
	print indent(level)+element
	print indent(level)+'<span dir="LTR" class="hidden size2">{0}</span>'.format(cell_diskuse)


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
		#TODO: should decision made here, if cell gets a label or
		# if it's too small?
		fs=_font_sizes[font_size(entry[2])-1]
		#TODO: calculate actual text size with PIL
		if len(entry[1])*fs/3>space_h or fs>space_v:
			show=False
		else:
			show=True
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
	h_favor = 4.-3.*(width / globals()['table_width'])
	print indent(level), '<!--', h_favor, width, globals()['table_width'], '-->'
	# output templates
	tag_column='<td class="tooltip" {0}width="{1}%">'
	tag_row = '<td class="tooltip" {0}height="{1}%">'
	tr_tag_open=False
	# determining total namespace sapce
	directory, _, full_size = items.pop(0)

	# precompute cell layout and size
	#TODO: also precompute cell labels to know if cell will be wide enough
	for path, filename, size in items:
		ratio = float(size) / full_size
		print "<!-- ", path, filename, size, full_size, ratio, "-->"
		if space_h*width > space_v*height*h_favor and space_h*width*ratio>len(filename)*6:
			cover = space_h * ratio
			space_h -= cover
			stack.append( ('td', cover) )
			print "<!--", space_h, cover, "-->"
		else:
			cover = space_v * ratio
			space_v -= cover
			stack.append( ('tr', cover) )
			print "<!--", space_v, cover, "-->"
		full_size -= size
	stack[-1]=('tr', stack[-1][1])

	# write cell layout HTML output
	for item in items:
		tag, dim = stack.pop(0)
		# do not assign dimension value to last item
		# TODO: cell dimensions don't fit relative files sizes
		if len(stack) < 1:
			dim=0
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
		.tooltip > span.hidden,
		.tooltip > span.hidden > a {
			display: none;
		}
		.tooltip:hover > span.hidden,
		.tooltip:hover > span.hidden > a {
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
print '<h4>Showing contents of: "{0}"</h4>'.format(_root)
print '<i>{0}</i>'.format(sys.argv)
# print 'smallest: {0}, largest: {1}, scale: {2}'.format(_min_size, _max_size, _log_scale)
# TODO: handle default height value, since table does not inherit height
print '<table width="{0}" height="{1}"><tr><td>'.format(table_width, table_height)
table(_root, 0, table_width, table_height)
print '</td></tr></table>'
print '''</div>
</body>'''
