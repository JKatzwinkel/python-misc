#!/usr/bin/python
from urllib2 import urlopen, Request
from urllib import urlretrieve
from bs4 import BeautifulSoup
from urlparse import urlparse, urlsplit, urljoin
import re
from time import time

import weave.picture as picture
import weave.tumblr as tumblr
import util


##############################################################
####################    CRAWLER    ###########################
##############################################################

# blog score times days since last visit. (max 14 days)
queue_score = lambda t: t.score * min(14**2,(util.days_since(t.seen)**2))

class Crawler:
	# optionally, give a list of blogs we should start with
	def __init__(self, numblogs, query=[]):
		self.visited={}
		# ignore blogs that we have seen recently
		# last (6 hours)
		#now = time()
		#for t in tumblr.blogs():
			#if t.seen > now - 3600*6:
				#self.visited[t] = t.seen
		# frontier is actual Blog instances!
		self.frontier=set(query)
		self.latest = None
		self.numblogs = numblogs
		self.parser = Parser(self)
		# what we gather
		self.images = {}
		self.msg = ''

	# add blog to frontier
	def add(self, t):
		if not self.visited.get(t):
			self.frontier.add(t)

	# clear crawler state in preparation for continuing search
	def rewind(self, n):
		self.numblogs = n
		self.images = {}

	# have I been at this particular url?
	def been_at(self, url):
		t = tumblr.get(url)
		return t in self.visited


	# choose next blog to visit
	def next_blog(self):
		if len(self.frontier)>0:
			# pick highest score blog from frontier list
			cand = sorted(self.frontier, key=queue_score)
			blog = cand.pop()
			while self.visited.get(blog):
				if len(cand) > 0:
					blog = cand.pop()
				else:
					blog = None
			self.frontier = set(cand)
			return blog
		else:
			print 'List is empty. Nowhere to go.'
		return None


	# perform one step of the crawling process
	def crawling(self):
		# Abbruchbedingung:
		#if sum([len(ii) for ii in self.images.values()]) >= self.numblogs:
		if len(self.images) >= self.numblogs:
			return False
		# weiter
		t = self.next_blog()
		if t:
			self.msg = self.status(t)
			now = time()
			t.seen = now
			self.visited[t] = now
			#print('visit {} at {:.1f}.'.format(t.name, now))
			# get extracted stuff from parser
			data = self.extract(t.url())
			if data:
				# process links:
				# create instances for them in order to create edges in graph
				# and also add them to the crawler's fronter list
				for href in data.get('links', []):
					l = t.link(href)
					if not self.visited.get(l):
						self.frontier.add(l)
				# now: images! Store them aligned to their blogs for later
				imgs = self.images.get(t, [])
				imgs.extend(data.get('images', []))
				self.images[t] = imgs
				# done with this blog/url
				# TODO: unless we want to check additional pages, but later
			# done. mark blog as visited
			self.latest = t
			return True
		return False


	# ask parser to extract stuff from current URL
	def extract(self, url):
		# check url scheme
		refparts = urlsplit(url)
		if not refparts.scheme:
			url=''.join(['http://', url])
		# send request
		req = Request(url)
		#print url
		try:
			page = urlopen(req)
			mimetype = page.info().gettype()
			if mimetype == 'text/html':
				return self.parser.parse(page)
		except Exception, e:
			print 'Error: {} couldnt be accessed.'.format(url)
			print e.message
			return {}


	def status(self, t):
		temp = '{:4} < {:4} \t{:5} Img. \t {}: {:2.2f} {:.2f}'
		n = sum([len(l) for l in self.images.values()])
		return temp.format(len(self.visited), len(self.frontier),
			n, t.name, t.score,
			queue_score(t))

	def message(self):
		return self.msg

##############################################################
##############################################################
##############################################################
##############################################################
##############################################################

# parser.
class Parser:
	def __init__(self, crawler):
		self.crawler = crawler


	# parse one page
	def parse(self, page):
		# Hmmmm...
		soup = BeautifulSoup(page)
		# collect links and images
		links=set()
		imgs=set()
		# links
		for link in soup.find_all('a'):
			href = link.get('href')
			if href:
				m = tumblrex.match(href)
				if m:
					links.add(m.group(2))
		# images
		for link in soup.find_all('img'):
			src = link.get('src')
			if src:
				if imgex.match(src):
					# FIXME: is it worth downloading or do we already have it?
					imgs.add(src)
					#print('found img url {}.'.format(src))
		# save
		#for link in list(links):
		#	self.addpage(link)
		return {'links': links, 'images': imgs}



##############################################################
##############################################################
##############################################################
##############################################################
##############################################################

# is a URL to an image worth downloading?
def img_relevant(url):
	m = idex.search(url)
	if m:
		p = picture.get(m.group(1))
		# is image known and has not been deleted?
		#if p:
			#print 'location {}\t dim {} > {} = {}'.format(
				#p.location != None, dim_class(url), p.dim, dim_class(url)>p.dim)
		return (p == None) or (p.path != None and dim_class(url) > p.dim)
	print 'no id found'
	return False


# try to extract the image size class indicated by a URL
def dim_class(url):
	dim = 0
	m = re.search(imgdimex, url)
	if m:
		dim = int(m.group(1))
	return dim


# high resolution!
def best_version(imgurl):
	dim = dim_class(imgurl)
	# count down sizes
	for d in filter(lambda x:x >= dim, [1280,800,500,400,250,100]):
		url = re.sub('_([1-9][0-9]{2,3})\.', '_{}.'.format(d), imgurl)
		try:
			req = Request(url)
			urlopen(req)
			return (url, d)
		except:
			pass
	return (imgurl, dim)




#bilder:
# http://stackoverflow.com/questions/3042757/downloading-a-picture-via-urllib-and-python
#

tumblrex=re.compile('(http://)?(\w*\.tumblr.com).*')
imgex=re.compile('http://[0-9]{2}\.media\.tumblr\.com(/[0-9a-f]*)?/tumblr_\w*\.(jpg|png)')
idex=re.compile('_(\w{19,20})_')
imgdimex=re.compile('_([1-9][0-9]{2,3})\.')
#tumblr_mpkl2n8aqK1r0fb8eo1_500.jpg
#urlretrieve(best, 'images/{}.{}'.format(name,ext))

# central module crawler instance
inst = None
# returns instance. no init
def instance():
	return inst

# initialize
def init(n, query):
	global inst
	inst = Crawler(n, query=query)
	return inst


# go to the internets and browse through there!
def crawl(url, n=30):
	# if no query is given, we try to get some blogs
	# with good image output from out database
	# TODO: heuristik ausdenken!
	#query = sorted(tumblr.blogs(),
		#key=lambda t:len(t.proper_imgs)/(len(t.images)+1),
		#key = lambda t: t.score*len(t.links),
		#reverse=True)
	#query = tumblr.queue()
	#query = [p.origin for p in picture.favorites() if p.origin]

	if instance():
		crawler = instance()
		favs = picture.favorites()
		while len(crawler.frontier)<2:
			p = favs.pop(0)
			for t in p.sources:
				crawler.add(t)
	else:
		# populate crawler frontier
		query = []
		for p in picture.favorites():
			query.extend(p.sources)
		query = sorted(set(query), key=queue_score)[::-1]
		# create crawler
		crawler = init(n, query)

	# possibly single seeding url to blog
	if url and not crawler.been_at(url):
		seed = tumblr.get(url)
		if not seed:
			seed = tumblr.create(url)
		# add single seed point, in case we cant build query
		print 'starting at blog:', seed.name
		#crawler.add(seed)
		#query = list(crawler.frontier)[:n] + [seed]
		crawler = init(n, [seed])

	# clean retrieval buffer
	crawler.rewind(n)

	# wait for the crawler to be done
	while crawler.crawling():
		print crawler.message()

	print 'Done.'

	images = []
	dis2 = []
	# now handle the collected image URLs
	for t, imgs in crawler.images.items():
		print t, '{:.2f}'.format(t.score)
		counter = 0
		for img in imgs:
			# check if image is already known
			# and if we can extract its Id
			m = idex.search(img)
			if m:
				name = m.group(1)
				# lookup
				pict = picture.get(name)
				#print('img id {} links to {} so far.'.format(name, pict))
				# if image is not on the disk yet, or if its resolution
				# is lower than the available ones, download the image
				best, dim = img, dim_class(img)
				if not pict:
					# image not known so far
					best, dim = best_version(img)
					pict = picture.openurl(best)
					#print('img not known so far, download it from {}.'.format(
						#best))
				else:
					if pict.dim < 1280:
						best, dim = best_version(img)
					#print('img {} known already in resolution {}.'.format(
						#name, pict.dim))
					# if we have local copy, but it is smaller than possible
					# look for high resolutions
					if pict.path != None and pict.dim < dim:
						# better version of known image available
						print 'upgradable image: {} from {} to {}'.format(
							name, pict.dim, dim)
						upgrade_img = pict.download(url=best)
						del upgrade_img
					else:
						# image known. assign to current blog and f.o.
						if t.assign_img(pict):
							if len(pict.sources)>1:
								dis2.append(pict)
								print '  Known img {},'.format(
									pict.name, t.name),
								if pict.origin:
									print 'from {}'.format(pict.origin.name),
								print 'up to {} refs'.format(len(pict.sources))
						pict.url = best
						pict = None
				# if downloading was succesful, append it to list of
				# retrieved images and assign it to the blog it appeared on
				if pict:
					pict.date = time()
					images.append(pict)
					t.assign_img(pict)
					pict.url = best
					#print '   {} - {} {}'.format(pict.name, pict.dim, pict.size)
					print '', pict
					counter += 1
					if counter >= max(5,t.score):
						break
			else:
				print 'Keine Id gefunden: {}. omitting.'.format(img)
		print ''
	# Puh endlich fertig!
	print 'Retrieved {} images from {} blogs.'.format(
		len(images), len(crawler.images))
	print '{} of those images come with proper url.'.format(
		len([p for p in images if p.url]))
	if len(dis2)>0:
		print 'Discovered {} references to images known from elsewhere:'.format(
			len(dis2))
		for p in dis2:
			print p.name, [t.name for t in p.sources]

	# thats it
	return images
