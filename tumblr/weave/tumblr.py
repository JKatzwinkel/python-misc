#!/usr/bin/python

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
		self.seen = 0
		self._score = None
		#register
		Blog.blogs[self.name]=self
	
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
	def assign_img(self, img):
		if isinstance(img, picture.Pict):
			pict = img
		else:
			pict = picture.get(img)
		if pict:
			if not pict in self.images:
				self.images.add(pict)
				pict.sources.append(self)
			#print 'assigning {} to {}.'.format(pict.name, self.name)
		else:
			if not img in self.images:
				self.images.add(img)
	
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
				kept_img = self.reviewed_imgs() /len(self.images)
				# avg rating of hosted images
				stars = self.avg_img_rating()
				# avg rating of images at linked blogs
				stars_out = sum([t.avg_img_rating() for t in self.links])
				if len(self.links) > 0:
					stars_out /= len(self.links)
				# score is kept image ratio times avg stars plus
				# avg incoming stars and outgoing stars
				self._score = kept_img * stars + stars_in + stars_out
			else:
				self._score = stars_in / 10
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
		return 0



	# how many stars did the avg image on this blog get by user
	#@property
	def avg_img_rating(self):
		if len(self.proper_imgs) > 0:
			stars = sum([p.rating for p in self.proper_imgs])
			return float(stars)/len(self.proper_imgs)
		return 0

	# text representation
	def __repr__(self):
		return '<{0}: {1}img, {2}cnx>'.format(
			self.name, len(self.images), len(self.links) + len(self.linked))

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
			'Score: {}'.format(int(self.score*100)),
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
				100*sum([t.score for t in self.linked])/len(self.linked)))
		if len(self.links)>0:
			infos.append('Links {} blogs with an average score of {:.2f}'.format(
				len(self.links), 
				100*sum([t.score for t in self.links])/len(self.links)))
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
##############################################################

# return known blogs
def blogs():
	return Blog.blogs.values()

# find blog by name/url
def get(url):
	url = re.sub('http://', '', url)
	name = url.split('.')[0]
	return Blog.blogs.get(name)

# creates a container instance for the blog at the given URL
def create(url, time=0):
	name = re.sub('http://', '', url)
	t = Blog(name)
	t.seen = time
	return t


# create from dictionary
def opendump(slots):
	name = slots.get('name')
	last_seen = float(slots.get('seen', 0))
	#reify data set
	t = Blog.blogs.get(name)
	if not t:
		t = create(name, time=last_seen)
	t.seen = last_seen
	# connect related image identifiers, whereever possible
	# using reification as well
	for p in slots.get('images', []):
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

#TODO rewrite!
def queue(num=100):
	seed = sorted(Blog.blogs.values(), key=lambda t:t.score, reverse=True)
	seed = filter(lambda t:t.score > .05, seed)
	seed = filter(lambda t:t.seen<time()-6*3600, seed)
	res = []
	for t in seed:
		res.append(t)
		#res.extend(t.links)
		#res.extend(t.linked)
		if len(t.links)>0:
			res.append(choice(list(t.links)))
		if len(t.linked)>0:
			res.append(choice(list(t.linked)))
	res = filter(lambda t:t.seen<time()-6*3600, res)
	return res[:num]
