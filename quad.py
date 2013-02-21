#!/usr/bin/python
import os
import sys
from math import log10 as log
from getopt import getopt
from fnmatch import fnmatch

_names=[]
_diskusage={}
_baseurl = 'https://192.168.178.1/wiki/doku.php?id='
_root = '.'
accept = filter_hidden
_glob = '*'
_delimiter = os.sep
_out = sys.stdout

# http://wiki.python.org/moin/HowTo/Sorting/ 
# http://stackoverflow.com/questions/955941/how-to-identify-whether-a-file-is-normal-file-or-directory-using-python
# http://stackoverflow.com/questions/1392413/calculating-a-directory-size-using-python

# Print help message
def print_help():
	print '{0} <directory> [OPTIONS] [-n|--name] [<glob>]'.format(sys.argv[0])
	print '''
	OPTIONS:
			-a, --all
					Display hidden files.

			-o, --output
					Instead of printing to STDOUT, save output to file.

			-d, --delimiter
					When using paths in hyperlinks, replace the system's file separator with
					custom delimiter.

			-m, --max-depth
					Limit displayed content to subdirectories within given depth.

			-h, --help
					Show this help message and quit.

			-n, --name
					Supplies a Unix shell-style wildcard expression (e.g. *.txt)
					that determines which files will be represented in HTML output
	'''

# Parse command-line arguments
def read_argv():
	if len(sys.argv) > 1:
		_root = sys.argv[1]
		if not os.path.isdir(_root):
			print >> sys.stderr, 'Error: not a directory'
			print >> sys.stderr, 'First argument must specify the directory to work with'
			exit()
		# process through command line arguments
		# using getopt, because unlike argparse, its in stdlib of Python 2.6.6
		try:
			opts, args = getopt(sys.argv[2:], "ham:d:o:", 
				["name=", "output=", "delimiter=", "help", "all"])
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
				# accept not only not-hidden files, but all
				accept = union(accept, true)
			elif opt in ('-n', '--name'):
				# filter filenames, accept only files that match expression
				# default is '*'
				accept = intersect(accept, filter)
				_glob = arg
			elif opt in ('-m', '--max-depth'):
				# assign passed number to _depth (maximum depth to render)
				_depth = int(arg)
			elif opt in ('-d', '--delimiter'):
				# change custom delimiter for full-path labels/links 
				# from OS file separator to passed character
				_delimiter = arg[0]
			elif opt in ('-o', '--output'):
				# assign output destination (filename or whatever...)
				# default is sys.stdout
				_out = arg
			elif opt in ('-u', '--baseurl'):
				# pass a URL that hyperlinks in output will be modeled on
				pass



# Filter those filenames that don't match a given expression
# Returns True if filename matches expression (which is a glob)
def filter(filename):
	return fnmatch(filename, glob)


# Method testing file/directory names on starting with a '.'
# Can be used to filter hidden files. Returns False if file/dir is hidden.
def filter_hidden(filename):
	return not filename.startswith('.')

# Dummy filter function, returning True no matter what
true = lambda x: True

# Returns a function that represents the intersection of two boolean
# functions f and g, which means these two are combined by an AND operator.
def intersect(f, g):
	return lambda x: f(x) and g(x)

# Returns a function that represents the union of two boolean
# functions, i.e. the combination of both by OR
def union(f, g):
	return lambda x: f(x) or g(x)


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

def largest(dirname):
	return filter(lambda x:x[0] == dirname or is_child(dirname, x), _names)


def disk_usage(path):
	if os.path.isdir(path):
		return _diskusage.get(path, 0)
	else:
		return os.path.getsize(path)


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
			results.append((dirname, fn.split('.txt')[0], filesize))
		results.append((dirname, '', du+1))
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
	path, filename, size = items.pop(0)
	print indent(level)+'<table width="100%" height="100%" class="tooltip" dir="{0}">'.format(['RTL', 'LTR'][level%2])
	namespaces = dirname.split(os.sep)
	if len(namespaces) > 1:
		print indent(level+1)+'<span><a href="{0}">{0}</a></span>'.format(namespaces[-1])
	full = size
	# loop through items / tr/td
	# each tr contains two td
	level += 1
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
	print indent(level)+'</table>'

def compute(dirname):
	_names = resources(dirname)
	partition(dirname)


#initialize variables, read command-line arguments
read_argv()
		
# compute list of files and directories, their hierarchy and disk usage amount
_names = resources(root)

# assembe HTML output
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
		.tooltip > span {
			display: none;
		}
		.tooltip:hover > span {
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
print '''<table width="100%" height="600">
<tr><td>'''
tableh(root, 0)
print '''</td></tr></table>
</div>
</body>'''
	


