#!/usr/bin/python
from urllib2 import urlopen, Request
from urllib import urlretrieve
from bs4 import BeautifulSoup
from urlparse import urlparse, urlsplit, urljoin
import re
from time import time

import weave.picture as picture
import weave.tumblr as tumblr


class Crawler:
	# optionally, give a list of blogs we should start with
	def __init__(self, query=[]):
		self.visited={}
		# ignore blogs that we have seen recently
		now = time()
		for t in tumblr.blogs():
			if t.seen > now - 300:
				self.visited[t] = t.seen
		# if no query is given, we try to get some blogs
		# with good image output from out database
		# TODO: heuristik ausdenken!
		if len(query) < 1:
			query = sorted(tumblr.blogs(), 
				key=lambda t:len(t.proper_imgs)/(len(t.images)+1),
				reverse=True)[:10]
		# frontier is actual Blog instances!
		self.frontier=set(query)
		self.parser = Parser(self)
		self.latest = None
		# what we gather
		self.images = {}


	# choose next blog to visit
	def next_blog(self):
		try:
			# pick random blog from frontier list
			blog = self.frontier.pop()
			# move blog to visited list and save time
			self.visited[blog] = time()
			return blog
		except:
			print 'List is empty. Nowhere to go.'
		return None


	# perform one step of the crawling process
	def crawling(self):
		t = self.next_blog()
		if t:
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
				t.seen = time()
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
			return None


	def status(self):
		temp = '{:4} < {:4} \t{:5} Img. \t {}'
		n = sum([len(l) for l in self.images.values()])
		return temp.format(len(self.visited), len(self.frontier),
			n, self.latest.name)

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
			# are we able to open this?
			if href:
				refparts = urlsplit(href)
				if not refparts.scheme:
					if not refparts.netloc:
						href = urljoin(page.url, ''.join(refparts[2:4]))
						#links.append(href)
				elif refparts.scheme == 'http':
					m = tumblrex.match(href)
					if m:
						links.add(m.group(2))
		# images
		for link in soup.find_all('img'):
			src = link.get('src')
			# are we able to open this?
			if src:
				refparts = urlsplit(src)
				if not refparts.scheme:
					if not refparts.netloc:
						href = urljoin(page.url, ''.join(refparts[2:4]))
						#imgs.append(href)
				elif refparts.scheme == 'http':
					if imgex.match(src):
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


# high resolution!
def best_version(imgurl):
	dim = 0
	m = re.search('_([1-9][0-9]{2,3})\.', imgurl)
	if m:
		dim=int(m.group(1))
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
#tumblr_mpkl2n8aqK1r0fb8eo1_500.jpg
#urlretrieve(best, 'images/{}.{}'.format(name,ext))

images = []

# go to the internets and browse through there!
def crawl(url, n=10):
	print 'Starting crawler.'
	seed = tumblr.get(url)
	if not seed:
		seed = tumblr.create(url)
	crawler = Crawler([seed])
	c=0
	# wait for the crawler to be done
	while crawler.crawling() and c < n:
		print crawler.status()
		c += 1
	print 'Done.'

	# now handle the collected image URLs
	for t, imgs in crawler.images.items():
		print t.name
		for img in imgs:
			# look for high resolutions
			best, dim = best_version(img)
			# check if image is already known
			# and if we can extract its Id
			m = idex.search(best)
			if m:
				name = m.group(1)
				pict = picture.get(name)
				# if image is not on the disk yet, or if its resolution
				# is lower than the available ones, download the image
				if not pict:
					pict = picture.openurl(best)
				elif pict.dim < dim:
					print '     upgradable image: {} from {} to {}'.format(
						name, pict.dim, dim)
					pict = picture.openurl(best)
				# if downloading was succesful, append it to list of 
				# retrieved images and assign it to the blog it appeared on
				if pict:
					images.append(pict)
					t.assign_img(pict)
					print '   {} - {} {}'.format(pict.name, pict.dim, pict.size)
			else:
				print 'Keine Id gefunden'
	print 'Retrieved {} images from {} blogs.'.format(
		len(images), len(crawler.images))
	# thats it
	return images
