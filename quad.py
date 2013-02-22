#!/usr/bin/python
import os
import sys
from math import log10 as log
from getopt import gnu_getopt
from fnmatch import fnmatch

# Global variables holding input data
_names=[] # list of contents
_diskusage={} # computed consumptions of disk space
_baseurl = '' #'https://192.168.178.1/wiki/doku.php?id=' # prefix URL for links
_root = '.' # root directory, where visualization recursion begins
# accept = None # combined boolean functions for filtering files
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

# http://wiki.python.org/moin/HowTo/Sorting/
# http://stackoverflow.com/questions/955941/how-to-identify-whether-a-file-is-normal-file-or-directory-using-python
# http://stackoverflow.com/questions/1392413/calculating-a-directory-size-using-python


# ======== USER INPUT SECTION ======== #

# Print help message
def print_help():
	#TODO: implement options for height/width of computed HTML table
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
	'''

# Parse command-line arguments
def read_argv(argv):
	# default filename filter allow all but hidden files.
	# accept = filter_hidden
	# Check if there are actually any arguments at all:
	if len(argv) > 1:
		_root = argv[1]
		# remove trailing file separator
		if _root.endswith(os.sep):
			_root = _root[:-1]
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
				["name=", "output=", "delimiter=", "help", "all"])
			# TODO: options for width/height of HTML table rendering
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
				#accept = union(accept, original)
				# deactivate hidden-file wildcard
				_globs['.*'] = 0
			elif opt in ('-n', '--name'):
				# filter filenames, accept only files that match expression
				# default is '*'
				#accept = intersect(accept, filter_fn)
				# set 'file bit' for retrieved wildcard
				glob = _globs.get(arg, 0)
				if glob & 4 != 4:
					_globs[arg] = glob+4
			elif opt in ('-m', '--max-depth'):
				# assign passed number to _maxdepth (maximum depth to render)
				globals()['_maxdepth'] = int(arg)
			elif opt in ('-d', '--delimiter'):
				# change custom delimiter for full-path labels/links
				# from OS file separator to passed character
				_delimiter = arg[0]
			elif opt in ('-o', '--output'):
				# assign output destination (filename or whatever...)
				# default is sys.stdout
				globals()['_out'] = arg
			elif opt in ('-u', '--baseurl'):
				# pass a URL that hyperlinks in output will be modeled on
				pass
		# assume that standalone arguments are meant to be file name wildcards
		if len(args) > 0:
			#if len(_globs) < 1:
				# TODO
				#accept = intersect(accept, filter_fn)
			# consider remaining arguments wildcards passed to include files
			for arg in args:
				glob = _globs.get(arg, 0)
				if glob & 4 != 4:
					_globs[arg] = glob+4
		init_wildcards()

		#globals()['accept'] = accept
		globals()['_root'] = _root
		#globals()['_out'] = _out






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

	print >> sys.stderr, "discard dirnames: ", discard_dir_globs
	print  >> sys.stderr, "preserve dirnames: ", keep_dir_globs
	print  >> sys.stderr, "discard filenames: ", discard_file_globs
	print  >> sys.stderr, "preserve filenames: ", keep_file_globs


# ODO obviously, this cannot stay like this. Populating a new list
# with each time identical outcome, on every single call, really
# isn't very efficient. But the problem is that at this position
# in the module, these assignments are done before the command line
# arguments are read in. We, however, need to adapt the changes
# brought by the command line arguments, at least those on the
# _globs{} dictionary. We will have to find a way to initiate these
# lists as static lists,, without provoking global namespace trouble

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
# TODO: don't forget to delete the () when changing those glob functions
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



# Filter those os.walk()-style triples out off a list
# that don't match any of the givens patterns
# Returns list of triples whose filenames match at least one expression
# These patterns are Unix-shell wildcards, like *.txt.
def filter_fn(entries):
	if len(_globs) < 1:
		return entries
	result = []
	# check each entry (directory) in list
	for dir, subs, files in entries:
		# keep only files that are matching one ore more of our Unix-wildcards
		matchingfiles = \
			filter(lambda fn:any(map(lambda glob: fnmatch(fn, glob), _globs)), files)
		result.append( (dir, subs, matchingfiles) )
	return result
	# return any(map(lambda glob: fnmatch(filename, glob), _globs))

# Boolean function acting as a filter matching visible files
is_visible=lambda p: not p.startswith('.')

# Boolean function, checking on every directory occuring in a path for hidden name
is_path_visible=lambda x: not any([p.startswith('.') for p in x.split(os.sep)[1:]])

# Filters a [(dir, subdirs[], files[]), ...] list like os.walk() returns
# Filters hidden files/directories from an os.walk()-style result set.
def filter_hidden(entries):
	result = []
	#dirs_visible = filter(lambda entry: not entry[0].startswith(_root+os.sep+'.'), entries)
	dirs_visible = filter(lambda e: is_path_visible(e[0]), entries)
	for dir, subs, files in dirs_visible:
		subs_visible = filter(is_visible, subs)
		files_visible = filter(is_visible, files)
		result.append( (dir, subs_visible, files_visible) )
	return result

# Dummy filter function, returning the same list that is passed as argument
original = lambda x: x

# Returns a function that represents the intersection of lists returned by
# functions f and g. The resulting function will be g(f(x))
def intersect(f, g):
	# return lambda x: f(x) and g(x)
	return lambda x: g(f(x))

# Returns a function that represents the union of two functions that
# are returning lists. The resulting function will build a list containing
# all elements of f(x) plus all of g(x)
def union(f, g):
	# return lambda x: f(x) or g(x)
	# return lambda x: f(x)+g(x)
	# return lambda x: list(set(f(x)+g(x)))
	return lambda x: list(set(f(x) + g(x)))





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
		results.append((dirname, '', du+1))
		# save directory disk use in dictionary
		# Because of the recursive disk space computation, even directories that
		# are nested too deep to be displayed have tp register their size
		# TODO Or Have They?? Will those files approved for displayal reach
		# their parent directory's detected disk space consumption???
		#
		# save disk space consumption value in dictionary for lookup by parent
		# +1 : ensure subdirectories are not listed before any of their parents
		_diskusage[dirname] = du+1
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

# returns a whitespace-only string of a certain length that can be used
# to indent output
def indent(level):
	return '  '*level

# format and echo a label for given path, filename, size of disk usage, and
# indentation level
def label((path, filename, diskuse), level):
	if filename == '':
		tableh(path, level+2)
	else:
		ns = _delimiter.join(path.split(os.sep)[1:]+[''])
		link = '<a href="{0}">{1}</a>'
		href = _baseurl + ns + filename
		label = filename
		if diskuse == 0:
			diskuse = 10
		element = '<font size="{0}pt">{1}</font>'.format(log(diskuse)-1, link.format(href, label))
		print '<span>{0}</span>'.format(filename)
		print indent(level+2)+element


# http://stackoverflow.com/questions/9725836/css-keep-table-cell-from-expanding-and-truncate-long-text
# http://stackoverflow.com/questions/2736021/super-simple-css-tooltip-in-a-table-why-is-it-not-displaying-and-can-i-make-it
# construe a table optimized for horizontal alignment, that is, the table 
# is expected to be wider than it is high.
# assuming that it is like this, cells are positioned in one column containing 
# the lists head next to a second column representing the rest, recursively
def tableh(dirname, level):
	items = largest(dirname)
	if len(items) < 1:
		print "None"
		return
	path, filename, size = items.pop(0)
	print indent(level)+'<table width="100%" height="100%" class="tooltip" dir="{0}">'.format(['RTL', 'LTR'][level%2])
	namespaces = dirname.split(os.sep)
	if len(namespaces) > 1:
		print indent(level+1)+'<span><a href="{0}">{0}</a></span>'.format(namespaces[-1])
	full = size
	# loop through items / tr/td
	# each tr contains two td
	level += 1 #indent
	remainder_h = 100.
	remainder_v = 100.

	while len(items)>0:
		rowspan = int(round(len(items)/2.))
		path, filename, size = items.pop(0)
		print indent(level)+'<tr>'

		# first td
		covering = size * remainder_h / full
		remainder_h -= covering
		full -= size
		print indent(level+1)+'<td class="tooltip" rowspan="{0}" width="{1}%" height="{2}%">'.format(rowspan, covering, remainder_v)
		label((path, filename, size), level)
		print indent(level+1)+'</td>'

		# second td
		if len(items) > 0:
			colspan = int(round(len(items)/2.))
			path, filename, size = items.pop(0)
			covering = size * remainder_v / full
			remainder_v -= covering
			full -= size
			print indent(level+1)+'<td class="tooltip" colspan="{0}" width="{2}%" height="{1}%">'.format(colspan, covering, remainder_h)
			label((path, filename, size), level)
			print indent(level+1)+'</td>'

		print indent(level)+'</tr>'
	level -= 1 # unindent
	print indent(level)+'</table>'


# print text-based nested list representation of file tree under dirname
def compute(dirname):
	_names = resources(dirname)
	partition(dirname)









# ===== MAIN PART ======

# === Begin Processing input data ===
# Assign Variables, read Command-line Arguments
read_argv(sys.argv)

# compute list of files and directories, their hierarchy and disk usage amount
_names = resources(_root)

print >> sys.stderr, _out
print >> sys.stderr, _maxdepth

if _out != sys.stdout:
	outputfile = open(_out, 'w')
	sys.stdout = outputfile

# assemble HTML output
print '''<!doctype html>
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
			table-layout: fixed;
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
		table:hover[class~=tooltip] > span {
			background-color: #FDD;
		}
	</style>
</head>
<body>
<div width="100%" height="600" align="center">'''
print '<h4>Showing contents of: "{0}"</h4>'.format(_root)
print '<i>{0}</i>'.format(sys.argv)
print '''<table width="100%" height="600">
<tr><td>'''
tableh(_root, 0)
print '''</td></tr></table>
</div>
</body>'''

if outputfile:
	outputfile.close()
