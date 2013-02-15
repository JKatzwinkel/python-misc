#!/usr/bin/python
import os

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
			background-color: #DCF;
			text-align:center;
			font-family: 'Arial', 'sans serif';
			color: #A33;
		}
		td:hover {
			background-color: #EDF;
		}
		tr {
			background-color: #FCD;
			padding: 0px;
			margin: 0px;
		}
		table {
			width: 100%;
			padding: 0px;
			background-color: #DFD;
			margin:0px;
		}
		table.namespace {
			background-color: #BBF;
		}
		table:hover {
			background-color: #ADA;
		}
	</style>
</head>
<body>
<table width="1000" height="800">
<tr><td>'''
# print table_horizontal(largest('.'), 
tagg(largest('.'))
print '''</td></tr></table>
</body>
</html>'''
	


