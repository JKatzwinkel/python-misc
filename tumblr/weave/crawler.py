#!/usr/bin/python
from urllib2 import urlopen, Request
from urllib import urlretrieve
from bs4 import BeautifulSoup
from urlparse import urlparse, urlsplit, urljoin
import re
from time import time

import weave.picture as picture
import weave.tumblr as tumblr


##############################################################
####################    CRAWLER    ###########################
##############################################################


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


	# choose next blog to visit
	def next_blog(self):
		if len(self.frontier)>0:
			# pick highest score blog from frontier list
			cand = sorted(self.frontier, key=lambda t: t.score, 
				reverse=True)
			blog = None
			now = time()
			# consider only blogs that haven't been visited in the last 6h
			while not blog:
				if len(cand) > 0:
					blog = cand.pop(0)
					if blog.seen > now-6*3600:
						self.visited[blog] = blog.seen
						self.frontier.remove(blog)
						blog = None
				else:
					return None
			# move blog to visited list and save time
			if blog in self.frontier:
				self.frontier.remove(blog)
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
			now = time()
			# get extracted stuff from parser
			data = self.extract(t.url())
			if data:
				# process links:
				# create instances for them in order to create edges in graph
				# and also add them to the crawler's fronter list
				for href in data.get('links', []):
					l = t.link(href)
					if not self.visited.get(l):
						if l.seen < now-3600*6:
							self.frontier.add(l)
						else:
							self.visited[l] = l.seen
				# now: images! Store them aligned to their blogs for later
				imgs = self.images.get(t, [])
				imgs.extend(data.get('images', []))
				self.images[t] = imgs
				# done with this blog/url
				# TODO: unless we want to check additional pages, but later
			# done. mark blog as visited
			t.seen = now
			self.visited[t] = now
			self.latest = t
			self.msg = self.status()
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


	def status(self):
		temp = '{:4} < {:4} \t{:5} Img. \t {}: {:2.2}'
		n = sum([len(l) for l in self.images.values()])
		return temp.format(len(self.visited), len(self.frontier),
			n, self.latest.name, self.latest.score)

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
					# is it worth downloading or do we already have it?
					imgs.add(src)
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
		return (p == None) or (p.location != None and dim_class(url) > p.dim)
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
idex=re.compile('_(\w{19})_')
imgdimex=re.compile('_([1-9][0-9]{2,3})\.')
#tumblr_mpkl2n8aqK1r0fb8eo1_500.jpg
#urlretrieve(best, 'images/{}.{}'.format(name,ext))

images = []

# go to the internets and browse through there!
def crawl(url, n=30):
	# if no query is given, we try to get some blogs
	# with good image output from out database
	# TODO: heuristik ausdenken!
	query = sorted(tumblr.blogs(), 
		#key=lambda t:len(t.proper_imgs)/(len(t.images)+1),
		key = lambda t: t.score*len(t.links),
		reverse=True)
	query = filter(lambda t:t.seen<time()-6*3600, query)

	# set up suff
	#print 'Starting crawler at', url
	seed = tumblr.get(url)
	if not seed:
		seed = tumblr.create(url)
	if not seed in query:
		query = [seed] + query
	# create crawler
	crawler = Crawler(n, query=query[:5])
	
	# wait for the crawler to be done
	while crawler.crawling():
		print crawler.message()
		
	print 'Done.'

	# now handle the collected image URLs
	for t, imgs in crawler.images.items():
		print t.name
		for img in imgs:
			# check if image is already known
			# and if we can extract its Id
			m = idex.search(img)
			if m:
				name = m.group(1)
				# lookup
				pict = picture.get(name)
				# if image is not on the disk yet, or if its resolution
				# is lower than the available ones, download the image
				best, dim = img, dim_class(img)
				if not pict:
					# image not known so far
					best, dim = best_version(img)
					pict = picture.openurl(best)
				else:
					if pict.dim < 1280:
						best, dim = best_version(img)
					# look for high resolutions
					if pict.location and pict.dim < dim:
						# better version of known image available
						print '     upgradable image: {} from {} to {}'.format(
							name, pict.dim, dim)
						pict = picture.openurl(best)
					else:
						# image known. assign to current blog and f.o.
						t.assign_img(pict)
						pict = None
				# if downloading was succesful, append it to list of 
				# retrieved images and assign it to the blog it appeared on
				if pict:
					pict.date = time()
					images.append(pict)
					t.assign_img(pict)
					pict.url = img
					#print '   {} - {} {}'.format(pict.name, pict.dim, pict.size)
					print pict
			else:
				print 'Keine Id gefunden'
	# Puh endlich fertig!
	print 'Retrieved {} images from {} blogs.'.format(
		len(images), len(crawler.images))
	# thats it
	return images
