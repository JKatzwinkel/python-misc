#!/usr/bin/python
# -*- coding: utf-8 -*- 

import re
from time import time
from random import choice

import weave.picture as picture
import util.inout as inout
import util

##############################################################
##############################################################
##############################################################
##############################################################
##############################################################
##############################################################
###########################################################33
# Blog
class Blog:
	blogs={}
	def __init__(self, name):
		self.name=name.split('.')[0]
		self.links=set() # outgoing
		self.linked=set() # incoming
		self.images=set()
		self.images_times={}
		self.seen = 0
		self._score = None
		#register
		if Blog.blogs.get(self.name) == None:
			Blog.blogs[self.name]=self
		else:
			print 'Blog id "{}" already assigned! Omitting instance!'.format(
				self.name)
	
	# interlinks this blog with another one
	def link(self, blogname):
		if type(blogname) == str:
			b2=get(blogname)
		else:
			b2 = blogname
		if not b2:
			b2 = create(blogname)
		if not b2 == self:
			self.links.add(b2)
			b2.linked.add(self)
		return b2
	
	# prints out links from and to other blogs
	def connections(self):
		for l in self.links:
			print ' {0} --> {1}'.format(self, l)
		for l in self.linked:
			print ' {0} <-- {1}'.format(self, l)

	
	# interlinks a blog and an image
	# returns true if link hadnt been there so far
	def assign_img(self, img, time=None):
		res = False
		if img:
			if isinstance(img, picture.Pict):
				pict = img
			else:
				pict = picture.get(img)
			if pict:
				if not time:
					time = pict.date
				# add image ref to blog obj
				if not pict in self.images:
					self.images.add(pict)
					self.images_times[pict] = time
					res = True
				# add blog ref to img obj
				if not self in pict.sources:
					pict.sources.append(self)
					res = True
				#print 'assigning {} to {}.'.format(pict.name, self.name)
			else:
				if not img in self.images:
					self.images.add(img)
					res = True
		else:
			print 'tumblr.assign_img: invalid img ref. wtf!!!'
		return res

	
	# how many of the images that this blog featured did remain on disk
	@property
	def score(self):
		if self._score is None:
			# time since last visit in month
			# urgency = util.days_since(self.seen)/31
			# avg rating of images at blogs linking here
			stars_in = sum([t.avg_img_rating() for t in self.linked])
			if len(self.linked) > 0:
				stars_in /= len(self.linked)
			if len(self.images) > 0:
				# TODO: page rank oder HITS
				# ratio incoming to outgoing links
				#link_ratio = 1+float(len(self.linked)+1)/(len(self.links)+1)
				# kept img ratio
				#kept_img = float(len(self.proper_imgs))/len(self.images)
				kept_img = 1.*self.reviewed_imgs() /len(self.images)
				# avg rating of hosted images
				stars = self.avg_img_rating()
				# avg rating of images at linked blogs
				stars_out = sum([t.avg_img_rating() for t in self.links])
				if len(self.links) > 0:
					stars_out /= len(self.links)
				# score is kept image ratio times avg stars plus
				# avg incoming stars and outgoing stars
				self._score = .001 + kept_img * (1+stars)**2 
				self._score *= (.9+stars_in)*(.95+stars_out)**2
			else:
				self._score = stars_in / (1+sum([len(t.links) for t in self.linked]))
		return self._score

	@property
	def proper_imgs(self):
		return [i for i in self.images 
			if isinstance(i, picture.Pict) and i.path]

	@property
	def dead_imgs(self):
		return [i for i in self.images 
			if not isinstance(i, picture.Pict) or i.path == None]

	# returns hosted images ordered by popularity
	@property
	def popular(self):
		pop=self.proper_imgs
		pop.sort(key=lambda p:len(p.sources), reverse=True)
		return pop

	# # of images that are still on disk and have already been
	# reviewed, divided by time since review
	def reviewed_imgs(self):
		if len(self.proper_imgs)>0:
			return sum([1/(1+util.days_since(p.reviewed)/31) for 
				p in self.proper_imgs 
				if p.reviewed > 0]) / len(self.proper_imgs)
		return 0.
	
	# ratio of images kept on disk and reviewed
	def imgs_ratio(self):
		if len(self.images)>0:
			return 1.*len([p for p in self.proper_imgs
			if p.reviewed > 0])/len(self.images)
		return 0.




	# how many stars did the avg image on this blog get by user
	#@property
	def avg_img_rating(self):
		if len(self.proper_imgs) > 0:
			return float(self.stars())/len(self.proper_imgs)
		return 0

	# number of stars this blog has in total
	def stars(self):
		stars = sum([p.rating for p in self.proper_imgs])
		return stars


	# text representation
	def __repr__(self):
		strs = self.stars()
		stars = ['', ' {}*'.format(strs)][strs>0]
		return u'<{}: {}img, {}/{}io {:.2f}sc{}>'.format(
			self.name, len(self.images), len(self.linked),len(self.links),
			self._score, stars)


	# url where this blog can be found
	def url(self):
		return 'http://{}.tumblr.com'.format(self.name)


	# print detailed information
	def details(self):
		disk_ratio = 100*len(self.proper_imgs)
		if len(self.images)>0:
			disk_ratio /= len(self.images)
		ratings = 1.*sum([p.rating for p in self.proper_imgs])
		if len(self.proper_imgs)>0:
			ratings /= len(self.proper_imgs)
		infos = [
			self.name,
			'Score: {:.2f}'.format(self.score),
			'Last visit: {}'.format(util.time_span_str(self.seen)),
			'Retrieved images: {}'.format(len(self.images)),
			'Images kept on disk: {} ({}%)'.format(len(self.proper_imgs), 
				disk_ratio),
			'Average rating of remaining images: {:.2f}/6'.format(ratings),
			'Reviewed imgs score: {:.2f}'.format(self.reviewed_imgs())
			]
		if len(self.linked)>0:
			infos.append('Linked by {} blogs with an average score of {:.2f}'.format(
				len(self.linked), 
				sum([t.score for t in self.linked])/len(self.linked)))
			ll=[t.name for t in list(self.linked)[:3]]
			if len(self.linked)>3:
				ll.append('...')
			infos.append(' [{}]'.format(', '.join(ll)))
		if len(self.links)>0:
			infos.append('Links {} blogs with an average score of {:.2f}'.format(
				len(self.links), 
				sum([t.score for t in self.links])/len(self.links)))
			ll=[t.name for t in list(self.links)[:3]]
			if len(self.links)>3:
				ll.append('...')
			infos.append(' [{}]'.format(', '.join(ll)))
		return '\n'.join(infos)


	# last image download/kept? when?78
	def time_of_last_contribution(self):
		if len(self.proper_imgs)>0:
			return max([p.date for p in self.proper_imgs])
		return 0.

##############################################################
##############################################################
##############################################################
##############################################################
##############################################################

# create from dictionary. instantiate images by default
def opendump(slots, images=True):
	name = slots.get('name')
	if name:
		name = name.lower()
	#reify data set
	t = Blog.blogs.get(name)
	if not t:
		t = create(name)
	if t:
		t.seen = float(slots.get('seen', 0))
		t._score = float(slots.get('score',0))
		# connect related image identifiers, whereever possible
		# using reification as well
		for p in slots.get('images', []):
			if not p:
				print "invalid img ref! very weird.. {}".format(t.name)
			else:
				t.assign_img(p)
		# reify hyperlink identifiers
		for l in slots.get('out', []):
			if l:
				t.link(l)
		for l in slots.get('in', []):
			if l:
				ln = get(l)
				if ln:
					ln.link(t)
	return t


# load blogs. ignore images by default
def load(filename='blogs.xml', images=False):
	records = inout.loadBlogs(filename)
	print 'instantiate blog objects from imported records...'
	print ['Ignore', 'Instantiate'][images], 'image references'
	blgs = [opendump(rec,images=images) for rec in records]
	print 'Blog instances:', len(Blog.blogs)
	#return blgs

##############################################################
##############################################################
##############################################################

# return known blogs
def blogs():
	if len(Blog.blogs)<1:
		load()
	return Blog.blogs.values()

# find blog by name/url
def get(url):
	if url:
		url = re.sub('http://', '', url)
		name = url.split('.')[0].lower()
		return Blog.blogs.get(name)
	return None

# creates a container instance for the blog at the given URL
def create(url, time=0):
	if url:
		name = re.sub('http://', '', url)
		t = Blog(name.lower())
		t.seen = time
		return t
	return None


# get random blog
def any():
	return choice(blogs())


################################################################
################################################################

# high score blogs first
def favs():
	return sorted(blogs(), key=lambda t:t._score)[::-1]

# return blog with score rank i
def rank(i):
	if i-1 in range(len(blogs())):
		return favs()[i-1]
	return None

# delete blog under given id (or given instance)
def remove(tid, links=True):
	if isinstance(tid, Blog):
		name = tid.name
	else:
		name = tid
		tid = Blog.blogs.get(name)
	if tid and name:
		del Blog.blogs[name]
		ll = 0
		for t in Blog.blogs.values():
			if links:
				if tid in t.links:
					t.links.discard(tid)
					ll += 1
				if tid in t.linked:
					t.linked.discard(tid)
					ll += 1
		print 'Removed blog at "{}". {} instances remaining.'.format(
			name, len(Blog.blogs))
		if links:
			print 'Removed {} references from adjacent instances.'.format(ll)


# export nodes set to graphviz .dot file
def save_dot(blogs, filename):
	if not filename.endswith('.dot'):
		filename='{}.dot'.format(filename)
	f = open(filename, 'w')
	f.write('digraph {\n')
	edges = []
	# outgoing:
	for t in blogs:
		for l in [l for l in t.links if l in blogs]:
			if not (t,l) in edges:
				edges.append((t,l))
	# incoming:
	for t in blogs:
		for l in [l for l in t.linked if l in blogs]:
			if not (l,t) in edges:
				edges.append((l,t))
	for a,b in edges:
		f.write('\t{} -> {}\n'.format(a.name, b.name))
	f.write('}\n')
	f.close()


# export graph
def dot_render(blogs, filename):
	inout.dot_render(blogs, filename)

###############################################################
##############################################################
##############################################################
##############################################################

#TODO rewrite!
def queue(num=100):
	seed = sorted(Blog.blogs.values(), key=lambda t:t.score, reverse=True)
	res = []
	for t in seed:
		res.append(t)
		#res.extend(t.links)
		#res.extend(t.linked)
		#if len(t.links)>0:
			#res.append(choice(list(t.links)))
		res.extend(list(t.links))
		if len(t.linked)>0:
			res.append(choice(list(t.linked)))
	return res[:num]



# do some page rank-like stuff
def dist_scores(n=10, reset=False):
	print 'run page rank for {} steps.'.format(n)
	# total amount of stars a blog's images archieved
	stars = lambda t: sum([p.rating for p in t.proper_imgs])
	# blog score directory:
	# start scores for all blogs 0 on default, or whatever
	# score is saved to xml dump in case no reset is desired.
	# no reset option might be more interesting due to its 'memory'
	if reset:
		reg = {t:0. for t in blogs()}
	else:
		reg = {t:t._score for t in blogs() if t._score}
	# spawned score. total stars plus # of imgs times review ratio.
	img_score = lambda t: float(stars(t)*2+len(t.proper_imgs)) * t.reviewed_imgs()
	# blog score per round: half of last score plus score spawned by images
	# slightly damped by huge numbers of downloaded images
	score = lambda t: reg.get(t,0)/1. + img_score(t) / (1+len(t.images)/100.)
	# distribution func: score shares from incoming links added up
	dist = lambda t: sum([reg.get(l,0)/(len(l.links)+1) for l in t.linked])
	# start
	# copy blogs to list
	blgs = blogs()
	# iterate n steps
	for i in range(n):
		reg = {t:score(t)+dist(t)*(.5+t.imgs_ratio()) for t in blgs}
	# save new scores to blogs objects, normalize to max. 1000 if nec.
	maxs = max(reg.values())
	norm = max(maxs, 1000.)/1000.
	for t in blgs:
		t._score = reg.get(t)/norm
	print 'ok'
	return reg


# find shortest link path between blog a and blog b
# follow directions: way=1: outgoing, way=2: incoming, way=3: both
def link_path(a, b, way=1, steps=0):
	if steps<1:
		steps = len(Blog.blogs)-1
	visited = {a:(None,0)}
	frontier = [a]
	i = 0
	while i < min(len(frontier), steps):
		t = frontier[i]
		neighbours = []
		if way & 1:
			neighbours.extend(sorted(list(t.links),key=lambda x:len(x.links)))
		if way & 2:
			neighbours.extend(sorted(list(t.linked),key=lambda x:len(x.linked)))
		_, cost = visited.get(t, (None,0))
		# look at neighbours = in/out links
		for n in neighbours:
			# arrived? traverse path end return!
			if n == b:
				path = [n]
				while t:
					path.append(t)
					t = visited.get(t, (None, None))[0]
				#print 'ran depth search for blogs for {} iterations;'.format(i+1),
				#print 'pool length:', len(frontier)
				return path[::-1]
			# if not arrived at b, check in/out links
			_, best = visited.get(n, (t, None))
			if best==None or cost+1 < best:
				visited[n] = (t, cost+1)
				#print n.name, t.name, cost+1
				if best==None:
					frontier.append(n)
		i += 1
	print 'no path found between {} and {}.'.format(a.name, b.name)
	# print 'iteration steps:', i,
	#print 'pool length:', len(frontier)
	return []
