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
	res=[]
	imgs=picture.pictures()
	print 'Begin computing similarities between {} images'.format(
		len(imgs))
	# BEGIN
	for i in range(len(imgs)):
		for j in range(i+1,len(imgs)):
			p=imgs[i]
			q=imgs[j]
			sim=p.similarity(q)
			if sim>.5:
				res.append((p,q,sim))
				picture.connect(p,q,sim)
		#if i%100==0:
			#print '\t{}\t/\t{}'.format(i, len(imgs)),
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
	print 'Done'
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
			while visited.get(similar[chc][0]) != None or similar[chc][0].path == None:
				chc+=1
			if chc < len(similar):
				p = similar[chc][0]
			else:
				break
	except Exception, e:
		f.write(' <b>{}</b>\n'.format(e.message))
	f.write('</body>\n</html>\n')
	f.close()


##############################################################
##############################################################
##############################################################


# all known images
def pictures():
	return picture.pictures()

# all known blogs
def blogs():
	return tumblr.blogs()


# kraeucht und flaeucht
def crawl(seed, num=10):
	crawler.crawl(seed, n=num)


##############################################################
####             Images / Blog IO                      #######
##############################################################

# speichere bildersammlung als XML
def saveImages(images, filename):
	inout.saveImages(images, filename)


# load XML dump
def loadImages(filename):
	records = inout.loadImages(filename)
	imgs = [picture.opendump(rec) for rec in records]
	return imgs

# speichere bildersammlung als XML
def saveBlogs(blogs, filename):
	inout.saveBlogs(blogs, filename)

# load XML dump
def loadBlogs(filename):
	records = inout.loadBlogs(filename)
	blgs = [tumblr.opendump(rec) for rec in records]
	# replace string identifiers in image sources lists
	# with newly created Blog instances
	#imgs = picture.pictures()
	#for p in imgs:
		#p.clean_sources()
	return blgs

# try to load images and blogs from default files
def load():
	if os.path.exists('images.xml'):
		loadImages('images.xml')
	if os.path.exists('blogs.xml'):
		loadBlogs('blogs.xml')
	# Check if images are still on disk!!
	picture.sync() #TODO
	# clean image sources
	for p in pictures():
		clean_sources(p)


# save imgs and blogs to default files
def save():
	saveImages(picture.Pict.imgs.values(), 'images.xml')
	saveBlogs(blogs(), 'blogs.xml')

# goes through the given images list and changes neighbour
# string identifiers into image instances
# has to be done after importing XML dunp
def reify(array):
	res = [picture.get(a) for a in array]
	return res

# remove string identifiers from an image's link list, either by
# replacing them with their corresponding instance, or 
# by --deleting-- creating them
def clean_sources(p):
	src = []
	for s in p.sources:
		if s and not isinstance(s, tumblr.Blog):
			obj = tumblr.get(s)
			if obj:
				src.append(obj)
			else:
				obj = tumblr.create('{}.tumblr.com'.format(s))
				obj.assign_img(p)
				src.append(obj)
	p.sources = src


# craft html page for groups of images
def savegroups(groups, filename):
	inout.savegroups(groups, filename)
