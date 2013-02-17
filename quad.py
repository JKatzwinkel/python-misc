#!/usr/bin/python
import os
from random import randrange as rnd
from math import log10 as log

_names=[]
_diskusage={}
_depth=40

# http://wiki.python.org/moin/HowTo/Sorting/ 
# http://stackoverflow.com/questions/955941/how-to-identify-whether-a-file-is-normal-file-or-directory-using-python
# http://stackoverflow.com/questions/1392413/calculating-a-directory-size-using-python

def is_subdir(dirname, entry):
	# entry is subdirectory if and only if no file seperators remain
	# after removing prepending higher directory path
	if entry[1] == '':
		if entry[0].startswith(dirname+os.sep):
			return len(entry[0].split(dirname+os.sep)[1].split(os.sep)) is 1
	return False

def largest(dirname):
	return filter(lambda x:x[0] == dirname or is_subdir(dirname, x), _names)

	
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

def indent(level):
	return '  '*level
	

def table_horizontal(items, full, level, attributes=''):
	if len(items) < 1:
		return
	if len(items) < 2:
		if items[0][0] != '':
			print indent(level)+items[0][1]
			return
	print indent(level)+'<table width="100%" height="100%" {0}>'.format(attributes)
	print indent(level+1)+'<tr>'
	size = items[0][2]
	print indent(level+2)+'<td width="{}%">'.format(size * 100 // full)
	if items[0][1] == '':
		if level < _depth:
			sub_items = largest(items[0][0])
			table_vertical(sub_items[1:], sub_items[0][2], level+3, attributes='class="namespace"')
		else:
			print indent(level+3)+items[0][0]
	else:
		print indent(level+3)+items[0][1]
	print indent(level+2)+'</td>'
	print indent(level+2)+'<td>'
	if level < _depth:
		table_vertical(items[1:], full - size, level+3)
	else:
		pass
		#print indent(level+3)+items[1][1]
	print indent(level+2)+'</td>'
	print indent(level+1)+'</tr>'
	print indent(level)+'</table>'
	
	
def table_vertical(items, full, level, attributes=''):
	if len(items) < 1:
		return
	if len(items) < 2:
		if items[0][0] != '':
			print indent(level)+items[0][1]
			return
	print indent(level)+'<table width="100%" height="100%" {0}>'.format(attributes)
	size = items[0][2]
	print indent(level+1)+'<tr height="{}%">'.format(size * 100 // full)
	print indent(level+2)+'<td>'
	if items[0][1] == '':
		if level < _depth:
			sub_items = largest(items[0][0])
			table_horizontal(sub_items[1:], sub_items[0][2], level+3, attributes='class="namespace"')
		else:
			print indent(level+3)+items[0][0]
	else:
		print indent(level+3)+items[0][1]
	print indent(level+2)+'</td>'
	print indent(level+1)+'</tr>'
	print indent(level+1)+'<tr>'
	print indent(level+2)+'<td>'
	if level < _depth:
		table_horizontal(items[1:], full - size, level+3)
	else:
		pass
		#print indent(level+3)+items[1][1]
	print indent(level+2)+'</td>'
	print indent(level+1)+'</tr>'
	print indent(level)+'</table>'
	
	
def label((path, filename, diskuse), level):
	if filename == '':
		tableh(path, level+2)
	else:
		ns = ':'.join(path.split(os.sep)[1:]+[''])
		link = '<a href="{0}">{1}</a>'
		baseurl = 'https://wiki.linie/doku.php?id='
		href = baseurl + ns + filename
		label = filename
		element = '<font size="{0}">{1}</font>'.format(1+log(diskuse)-1, link.format(href, label))
		print '<span>{0}</span>'.format(filename)
		print indent(level+2)+element

# http://stackoverflow.com/questions/9725836/css-keep-table-cell-from-expanding-and-truncate-long-text
# http://stackoverflow.com/questions/2736021/super-simple-css-tooltip-in-a-table-why-is-it-not-displaying-and-can-i-make-it
def tableh(dirname, level):
	items = largest(dirname)
	path, filename, size = items.pop(0)
	print indent(level)+'<table height="100%" class="tooltip" dir="{0}">'.format(['RTL', 'LTR'][level%2])
	print indent(level+1)+'<span>{0}</span>'.format(dirname.split(os.sep)[-1])
	#print indent(level+1)+'<caption>{0}</caption>'.format(directory[0].split(os.sep)[-1])
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


def tagg(items):
	full = items[0][2]
	table_horizontal(items[1:], full, 0)

def compute(dirname):
	_names = resources(dirname)
	partition(dirname)

_names = resources('.')
#for t in _names:
#	print t

			#border-collapse:collapse;

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
		td:hover {
			background-color: #DCF;
		}
		table {
			width: 100%;
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
			background-color: #FFF;
			border: 1px solid #CCC;
			margin: 2px 10px;
		}
		table:hover[class~=tooltip] > span {
			background-color: #FDD;
		}
	</style>
</head>
<body>
<table width="800" height="600">
<tr><td>'''
# print table_horizontal(largest('.'), 
#tagg(largest('.'))
tableh('.', 0)
print '''</td></tr></table>
</body>
</html>'''
	


