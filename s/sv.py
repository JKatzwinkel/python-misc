#!/usr/local/bin/python

import socket
import sys
import sqlite3 as sql
import time


dbcon = sql.connect('list.db')
dbcsr = dbcon.cursor()
items = {}

def fmtitem(item):
	lct = time.gmtime(item[1])
	#return '  {} [{}]'.format(item[0],
		#time.strftime('%Y-%m-%d', lct))
	return '  {}'.format(item[0])

def shoppinglist():
	return u'\n'.join(['Einkaufen:']+[fmtitem(i) for i in itemschron()]+[''])

def splitline(line):
	return {i.strip():time.time() for i in line.split(' ') if len(i)>0}

def itemschron(asc=False):
	return sorted(items.items(), key=lambda t:t[1], reverse=not asc)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
	s.bind(('', 10000))
except:
	print('Socket already in use.')
	s.close()
	sys.exit(1)

s.listen(0)

while 1:
	connection, addr = s.accept()
	print(addr)
	data = b''
	data = connection.recv(1024)
	while data:
		data = data.decode('utf-8')
		print(u'[{0}]'.format(data))
		if data.startswith('GET'):
			#connection.sendall('\n'.join([line for line in open('index.html')]))
			connection.sendall(bytes(shoppinglist(), 'utf-8'))
			break
		items.update(splitline(data))
		data = connection.recv(1024)
# close connection
	connection.close()
# if item list was received
	if len(items) > 0:
		for i in items:
			print('[{}]'.format(i))
# otherwise
#else:
#s.connect(addr)
	#s.sendall('Liste:\nstuff')
s.shutdown(socket.SHUT_RDWR)
s.close()


#s.connect(('', 10000))



