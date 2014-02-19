#!/usr/bin/python

import re
from PIL import Image as pil
import os
from random import choice, randrange
from math import sqrt as sqr

import util.statistics as stat
import util.measures as measure
import util.inout as inout
import util.cluster as cluster
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


# search reasonable paths between selected images
def chain(query=None):
	stars = sorted(pictures(), key=lambda p:p.rating, reverse=True)
	if not query:
		query = stars[:6]
	else:
		query = query[:]
	tolerance = 0
	#print ', '.join([p.name for p in query])
	# only very similar imgs are neighbours
	neighbours = lambda p: [i for i in p.relates.items() if i[1]>.4]
	# neighbour order: beginning with most similar
	best = lambda p: sorted(neighbours(p), key=lambda tt:1-tt[1])
	# putting nearest neighbours in straight row. nearest is left
	front = lambda p: [k for (k,v) in best(p)]
	# resulting path
	res = []
	# go!
	p = query.pop(randrange(len(query))) #stars[randrange(len(stars))]
	# loop
	while len(query)>0:
		tolerance+=1
		steps = {p:(None, 0)} # node, predecessor, cost
		frontier = [p] # way to go!
		i = 0 # step in search
		# alrighty
		while i<len(frontier):
			# make one step forward
			p = frontier[i]
			# checkpoint?
			if p in query:
				# yay!
				query.remove(p)
				pb = p # walk backwards
				path = []
				while pb:
					path.insert(0,pb)
					pb = steps.get(pb)[0] # get predecessor
				steps = {p:(None, 0)}
				frontier = [p]
				i = 0
				if len(res)>0:
					if res[-1] == path[0]:
						path.pop(0)
				res.extend(path) # ok. new search
			# what will be appended to todo list next?
			neigh = front(p)
			if tolerance>5:
				neigh.extend([stars.pop(0) for x in range(tolerance-5)
					if len(stars)>0])
			# get current cost of having arrived at node p
			_, cost = steps.get(p,(None,0))
			# append neighbours to frontier and steps history
			for n in neigh:
				if n.location: # wichtig
					ncost = cost+1-p.relates.get(n,0)
					# check if way to n is known
					best_way = steps.get(n)
					# either no better way is known than the current one
					if best_way == None or ncost < best_way[1]:
						steps[n] = (p, ncost)
						# if no way has been known at all, we append our n to front
						if not best_way:
							frontier.append(n)
					# or there is a better way
					# what if we have found a better way that the known one?
					# we do nothing, obviously
			i += 1
		# nothing left in frontier list
		if len(query)>0:
			path=[]
			pb=p
			while pb:
				path.insert(0,pb)
				pb = steps.get(pb)[0]
			if len(res)>0:
				if res[-1] == path[0]:
					path.pop(0)
			res.extend(path)
	return res





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

# return crawler instance
def get_crawler():
	crawly = crawler.instance()
	if not crawly:
		crawly = crawler.init(10, [])
	return crawly

# clusterin
def clustering(imgs, num):
	clusters = cluster.cluster(imgs, num)
	return [c.imgs for c in clusters]

# run page rank thingie
def scores(n, reset=True):
	return tumblr.dist_scores(n=n, reset=reset)


# combines two image instances of an identical picture to one
def merge_images(p,q):
	q,p = sorted([p,q], key=lambda i:i.size[0]*i.size[1])
	#TODO: todo!
	p.dim = max(p.dim, q.dim)
	p.rating = max(p.rating, q.rating)
	p.sources.extend(q.sources)
	p.sources = list(set(p.sources)) # but make sure blogs dont count twice
	# of both urls, keep that one that seems to have been accessbl more recently
	p.url = sorted([p,q], key=lambda i:i.date)[-1].url
	p.date = min(p.date, q.date) # date of retrieval: keep older
	p.reviewed = max(p.reviewed, q.reviewed)
	# replace references to q in blog image lists
	for t in q.sources:
		if q in t.images:
			t.images.remove(q) # if q is removed, insert p henceforth
			t.images.add(p)
	# remove q from central images list
	picture.Pict.imgs.pop(q.name,None)
	# TODO: what else?
	# remove absorbed image
	#if q in p.relates:
		#del p.relates[q]
	# replace all references to q made from blogs and other images with p
	# images: links to similar images
	for i in pictures():
		if i.relates.pop(q,None): # if link to q is to be removed, link to p instead
			if i != p: # unless we are at p, of course
				i.relates[p] = p.similarity(i)
	# blogs: links to hosted images
	# TODO: if everything is like its meant to be,
	# this should be unnecessary, since we can just update all blogs in q.sources
	#for t in blogs():
		#if q in t.images:
			#t.images.remove(q) # if q is removed, insert p henceforth
			#t.images.add(p)
	# delete local image copy
	picture.delete(q)
	# make absorbed img live on as exact copy of absorber?
	# q.__dict__ = p.__dict__
	# return tuple absorber, absorbee for erasure of absorbee in calling applications
	return (p, q)


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
	if not os.path.exists('images'):
		os.mkdir('images')
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
	# remove irrelevant blgos like www, staff...
	if os.path.exists('ignore.txt'):
		for blg in open('ignore.txt', 'r'):
			tumblr.remove(blg)
	# yeah! done!
	print 'ok'
	if len(picture.Pict.imgs)>0:
		print 'imported {} images, {} of which are locally present ({:.1f}%),'.format(
			len(picture.Pict.imgs), len(pictures()),
			100.*len(pictures())/len(picture.Pict.imgs))
	known = [t for t in blogs() if t.seen > 0]
	if len(blogs())>0:
		print 'and {} blogs, {} of which we have actually been at ({:.1f}%).'.format(
			len(blogs()), len(known),
			100.*len(known)/len(blogs()))
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

# html export of image sequence
def export_html(imgs, filename):
	inout.export_html(imgs, filename)
