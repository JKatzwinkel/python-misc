#!/usr/bin/python

import re
from PIL import Image as pil
import os
from random import choice
from math import sqrt as sqr

import util.statistics as stat
import util.measures as measure
import util.inout as inout
import weave.picture as picture
import weave.tumblr as tumblr
import weave.crawler as crawler

idex=re.compile('_(\w{19})_')

# search for images similar to each other, link them
def simpairs():
	print 'Begin computing image similarities'
	res=[]
	imgs=picture.pictures()
	for i in range(len(imgs)):
		for j in range(i+1,len(imgs)):
			p=imgs[i]
			q=imgs[j]
			sim=p.similarity(q)
			if sim>.5:
				res.append((p,q,sim))
				picture.connect(p,q,sim)
		if i%100==0:
			print '\t{}\t/\t{}'.format(i, len(imgs)),
	print '\tDone!\t\t\t'
	f=open('html/.twins.html','w')
	f.write('<html>\n<body>')
	res.sort(key=lambda t:t[2], reverse=True)
	for p,q,sim in res[:500]:
		if sim > .9:
			f.write('<h4>{} and {}: {}</h4>\n'.format(p.name,q.name,sim))
			f.write('<b>{} versus {}: </b><br/>\n'.format(p.info,q.info,))
			if len(p.sources)>0 and len(q.sources)>0:
				f.write('<i>{} and {}: </i><br/>\n'.format(p.origin.name,q.origin.name,))
			f.write('<img src="../{}"/><img src="../{}"/><br/>\n'.format(
				p.location, q.location))
	f.write('</body>\n</html>\n')
	f.close()
	return res




def stumblr(seed, filename):
	f=open(os.sep.join(['html', filename]), 'w')
	f.write('<html>\n<body>')
	p = seed
	cnt = 0
	visited={}
	pos=0
	try:
		while p != None and cnt < 400:
			visited[p]=True
			f.write(' <img src="../{}" height="540"/>\n'.format(p.location))
			pos+=p.size[0]*540/p.size[1]
			if pos>980:
				f.write(' <br/>\n')
				pos=0
			cnt+=1
			similar = sorted(p.relates.items(), key=lambda x:x[1], reverse=True)
			chc=0
			while chc < len(similar) and visited.get(similar[chc][0]) != None:
				chc+=1
			if chc < len(similar):
				p = similar[chc][0]
			else:
				break
	except Exception, e:
		f.write(' <b>{}</b>\n'.format(e.message))
	f.write('</body>\n</html>\n')
	f.close()



#TODO sollte eigentlich nach util.inout
# craft html page for groups of images
def savegroups(groups, filename):
	f=open(os.sep.join(['html', filename]), 'w')
	f.write('<html>\n<body>')
	for group in groups[:50]:
		f.write(' <div>\n')
		f.write('  <h3>{} Members</h3/>\n'.format(len(group)))
		p=group.pop(0)
		f.write('  <table height="{}">\n'.format(p.size[1]))
		f.write('   <tr><td rowspan="2">\n')
		f.write('    <img src="../{}"/><br/>\n'.format(p.location))
		f.write('   </td>\n')
		thmbsize=min(p.size[1]/2, 300)
		rowheight=thmbsize+10
		for i,s in enumerate(group):
			f.write('     <td height="{}" valign="top">\n'.format(rowheight))
			f.write('      <img src="../{}" height="{}"><br/>\n'.format(s.location, thmbsize))
			if (s.origin):
				f.write('      {}\n'.format(s.origin.name))
			f.write('     </td>\n')
			if i+1==len(group)/2:
				f.write('    </tr><tr>\n')
				rowheight=p.size[1]-rowheight
		f.write('   </tr>\n  </table>\n')
		f.write(' </div>\n')
	f.write('</body>\n</html>\n')
	f.close()


# all known images
def pictures():
	return picture.pictures()


# kraeucht und flaeucht
def crawl(seed, num=10):
	crawler.crawl(seed, n=num)


# speichere bildersammlung als XML
def saveXML(images, filename):
	inout.saveXML(images, filename)


