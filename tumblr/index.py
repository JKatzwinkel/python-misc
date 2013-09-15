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
		p=imgs[i]
		for j in range(i+1,len(imgs)):
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
	return crawler.crawl(seed, n=num)


# run page rank thingie
def scores(n):
	return tumblr.dist_scores(n=n)

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
	print 'read in xml...'
	records = inout.loadBlogs(filename)
	print 'instantiate blog objects from imported records...'
	blgs = [tumblr.opendump(rec) for rec in records]
	# replace string identifiers in image sources lists
	# with newly created Blog instances
	#imgs = picture.pictures()
	#for p in imgs:
		#p.clean_sources()
	return blgs

# remove string identifiers from an image's link list, either by
# replacing them with their corresponding instance, or 
# by --deleting-- creating them
def clean_sources(p):
	src = p.sources[:]
	p.sources = []
	for s in src:
		if s:
			if isinstance(s, tumblr.Blog):
				t = s
			else:
				t = tumblr.get(s)
			if not t:
				t = tumblr.create(s)
			t.assign_img(p)

# clean image ref lists of blog objs
def clean_img_refs(t):
	imgs = list(t.images)
	t.images = set()
	for i in imgs:
		if i:
			if isinstance(i, picture.Pict):
				p = i
			else:
				p = picture.get(i)
			#t.assign_img(p)
			t.images.add(p)


# recover img dir
# tries to instantiate Pict obj for all img files that are not
# represented yet
def recover_imgs():
	print 'starting img recovery attempt'
	ff = os.listdir('images')
	picts = pictures()
	print 'local imgs: {}; fully initialized instances from db: {}'.format(
		len(ff), len(picts))
	pn = [('.'.join(f.split('.')[:-1]),f) for f in ff]
	# orphan img files
	orph = []
	for n,f in pn:
		p = picture.get(n)
		if not p:
			orph.append((n,f))
		else:
			if not p.path:
				orph.append((n,f))
	#orph = [(n,f) for n,f in pn if insuff(n)]
	if len(orph)>0:
		print 'Orphan img files in images/ dir: {}'.format(
			len(orph))
		res = []
		for n,f in orph:
			pict = picture.openfile('images', f, name=n)
			if pict:
				res.append(pict)
		print 'returning {} recovered img objs.'.format(
			len(res))
		#print 'existing instances improved by recovered data: {}'.format(
			#len([p for p in res if p in picts]))
		return res
	print 'no recovery needed.'


# try to load images and blogs from default files
def load(recover=False):
	print 'loading images.xml'
	if os.path.exists('images.xml'):
		loadImages('images.xml')
	print 'loading blogs.xml'
	if os.path.exists('blogs.xml'):
		loadBlogs('blogs.xml')
	# Check if images are still on disk!!
	print 'checking local image copies, resolve inter img refs'
	picture.sync() #TODO
	if recover:
		# untracked local img files recovery attempt
		print 'try to recover img instances from local img files'
		recover_imgs()
	# clean image sources
	print 'resolving image source links'
	for p in picture.Pict.imgs.values():
		clean_sources(p)
	print 'resolving blog image links'
	for t in blogs():
		clean_img_refs(t)
	# yeah! done!
	print 'ok'
	print 'imported {} images, {} of which are locally present ({}%),'.format(
		len(picture.Pict.imgs), len(pictures()), 
		100*len(pictures())/len(picture.Pict.imgs))
	known = [t for t in blogs() if t.seen > 0]
	print 'and {} blogs, {} of which we have actually been at ({}%).'.format(
		len(blogs()), len(known),
		100*len(known)/len(blogs()))
	newsies = [p for p in pictures() if p.reviewed < 1]
	if len(newsies)>0:
		print '{} images are on disk, but are still to'.format(
			len(newsies)),
		print 'be reviewed.'
	popsies=[p for p in pictures() if len(p.sources)>1]
	if len(popsies)>0:
		popsies=sorted(popsies, key=lambda p:len(p.sources))
		print '{} images have been found at more than one source;'.format(
			len(popsies))
		print 'the one of highest frequency is {} with {} sources.'.format(
			popsies[-1].name, len(popsies[-1].sources))
	orphies = [p for p in pictures() if len(p.sources)<1]
	if len(orphies)>0:
		print '{} images without information about any origin.'.format(
			len(orphies))
	offline=[p for p in pictures() if p.url==None]
	if len(offline)>0:
		print '{} images can\'t be assigned to their source url.'.format(
			len(offline))




# save imgs and blogs to default files
def save():
	saveImages(picture.Pict.imgs.values(), 'images.xml')
	saveBlogs(blogs(), 'blogs.xml')


# craft html page for groups of images
def savegroups(groups, filename):
	inout.savegroups(groups, filename)
