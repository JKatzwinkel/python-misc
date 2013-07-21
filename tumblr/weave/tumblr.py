#!/usr/bin/python

import re
from time import time()

import weave.picture as picture

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
		self.links=set()
		self.linked=set()
		self.images=set()
		self.seen = 0
		#register
		Blog.blogs[self.name]=self
	
	# interlinks this blog with another one
	def link(self, blogname):
		b2=Blog.blogs.get(blogname, create(blogname))
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
			pict = picture.lookup(img)
		if pict:
			self.images.add(pict)
			pict.sources.append(self)
		else:
			self.images.add(img)
	
	@property
	def proper_imgs(self):
		return [i for i in self.images if isinstance(i, picture.Pict)]

	@property
	def dead_imgs(self):
		return [i for i in self.images if not isinstance(i, picture.Pict)]	
	
	
	# returns hosted images ordered by popularity
	@property
	def popular(self):
		pop=self.proper_imgs
		pop.sort(key=lambda p:len(p.sources), reverse=True)
		return pop

	# text representation
	def __repr__(self):
		return '<{0}: {1}img, {2}cnx>'.format(
			self.name, len(self.images), len(self.links) + len(self.linked))

	# url where this blog can be found
	def url(self):
		return 'http://{}.tumblr.com'.format(self.name)

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
	t = Blog.blogs.get(name, create(name))
	for p in slots.get('images', []):
		t.assign_img(p)
	for l in slots.get('out', []):
		t.link(l)
	return t

