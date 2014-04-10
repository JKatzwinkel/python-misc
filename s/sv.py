#!/usr/local/bin/python

import socket
import sys




s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
	s.bind(('', 10000))
except:
	print 'Socket already in use.'
	s.close()
	sys.exit(1)


s.listen(0)
connection, addr = s.accept()
print addr

items = []
while 1:
	data = connection.recv(1024)
	if not data:
		break
	print '[{0}]'.format(data)
	if data.startswith('GET'):
		#connection.sendall('\n'.join([line for line in open('index.html')]))
		connection.sendall('OK.\n')
		break
	items.extend([i.strip() for i in data.split(' ') if len(i)>0])
# close connection
connection.close()
# if item list was received
if len(items) > 0:
	for i in items:
		print i
# otherwise
#else:
#s.connect(addr)
	#s.sendall('Liste:\nstuff')
s.shutdown(socket.SHUT_RDWR)
s.close()


#s.connect(('', 10000))



