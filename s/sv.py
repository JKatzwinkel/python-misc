#!/usr/local/bin/python

import socket
import sys
import sqlite3 as sql
import time


# connect to database
db = sql.connect('list.db')
dbc = db.cursor()
# initialize if necessary
dbc.execute('''create table if not exists needs (name text,
time int)''')

items = {}
# read item list from db, if possible
for row in dbc.execute('select * from needs'):
	k,v = row
	items[k] = float(v)


# returns single line in formatted string
def fmtitem(item):
	lct = time.gmtime(item[1])
	#return '  {} [{}]'.format(item[0],
		#time.strftime('%Y-%m-%d', lct))
	return '  {}'.format(item[0])

# assemble text output for shopping list
def shoppinglist():
	return u'\n'.join(['Einkaufen:']+[fmtitem(i) for i in itemschron()]+[''])

# split string into single items and put in dict along timestamps
def splitline(line):
	return {i.strip():time.time() for i in line.split(' ') if len(i)>0}

# sort items dictionary chronologically
def itemschron(asc=False):
	return sorted(items.items(), key=lambda t:t[1], reverse=not asc)

# open socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# bind port and let listen
try:
	s.bind(('', 10000))
except:
	print('Socket already in use.')
	s.close()
	sys.exit(1)
s.listen(0)

while 1:
	# establish connection once request comes in
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
		items_new = splitline(data)
		# update items dict with newly read items
		items.update(items_new)
		# update data base
		for k, v in items_new.items():
			dbc.execute('''insert into needs values ('{}', {})'''.format(
				k, int(v)))
		# socket read on
		data = connection.recv(1024)
	# comit database queries
	db.commit()
	# close connection
	connection.close()


# shutdown socket
s.shutdown(socket.SHUT_RDWR)
s.close()

# shutdown db conneection
db.close()
#s.connect(('', 10000))



