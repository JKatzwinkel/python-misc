#!/usr/bin/python

import re

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
		self.relates=set()
		self.features=set()
		#register
		Blog.blogs[self.name]=self
	
	# interlinks this blog with another one
	def link(self, blogname):
		b2=Blog.blogs.get(blogname)
		if b2:
			self.relates.add(b2)
			b2.relates.add(self)
	
	# prints out implied connections to blogs
	def linked(self):
		for l in self.relates:
			print ' {0} <--> {1}'.format(self, l)
	
	# interlinks a blog and an image
	def feature(self, img):
		if isinstance(img, picture.Pict):
			pict = img
		else:
			pict = picture.lookup(img)
		if pict:
			self.features.add(pict)
			pict.sources.append(self)
		else:
			self.features.add(img)
	
	@property
	def feat(self):
		return [i for i in self.features if isinstance(i, Tum)]
	
	# returns hosted images ordered by popularity
	@property
	def popular(self):
		pop=self.feat
		pop.sort(key=lambda p:len(p.sources), reverse=True)
		return pop

	def __repr__(self):
		return '<{0}: {1}img, {2}cnx>'.format(
			self.name, len(self.features), len(self.relates))


##############################################################
##############################################################
##############################################################
##############################################################
##############################################################
##############################################################


def blogs():
	return Blog.blogs.values()

def lookup(name):
	return Blog.blogs.get(name)

def create(name):
	name = re.sub('http://', '', name)
	return Blog(name)

# create from dictionary
def opendump(slots):
