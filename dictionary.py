#!/usr/bin/python

import re


def show(lvl, pref=''):
	for c,l in lvl.items():
		if not c == '\n':
			show(l, pref+c)
		elif l > 0:
			print('{}: {}x'.format(pref,l))


def ranks(lvl, pref=''):
	items = []
	for c,l in lvl.items():
		if not c == '\n':
			dwnlvl = (ranks(l, pref=pref+c))
			if len(dwnlvl)>0:
				items.extend(dwnlvl)
		elif l > 0:
			items.append((pref,l))
	return items



wdex = re.compile('^[A-Za-z][a-z]{2,20}$') #, re.I)
voc = {}
dep = 0
for word in open('/usr/share/dict/american-english', 'r'):
	word = word.strip()
	m = wdex.match(word)
	if m:
		lvl = voc
		d = 0
		for c in word:
			if not c in lvl:
				lvl[c] = {}
			lvl = lvl.get(c)
			d += 1
		lvl['\n'] = 0
		dep = max(d, dep)

print('dict top level keys: {}; depth: {}.'.format(len(voc), dep))

#s = "hello&^uevfehello!`.<hellohow*howdhAreyou..."
s=' '.join([line for line in open('text.txt', 'r')])

found = []
for i in range(len(s)-2):
	lvl = voc
	rec = ''
	for c in s[i:i+20].lower():
		if c in lvl:
			rec += c
		else:
			if '\n' in lvl:
				found.append(rec)
				lvl['\n'] = lvl.get('\n', 0) + 1
			break
		lvl = lvl.get(c)

#print(found)

#show(voc)
scores = ranks(voc)
freq = 0
line = []
for t,f in sorted(scores, key=lambda t:t[1], reverse=True):
	if f > 0:
		if f != freq:
			print('\n   '.join([' '.join(line[i:i+8]) for i in range(0,len(line), 8)]))
			freq = f
			line = ['{} times:'.format(f)]
		line += ['{}'.format(t)]
print('\n   '.join([' '.join(line[i:i+8]) for i in range(0,len(line), 8)]))
#print scores
#print voc

