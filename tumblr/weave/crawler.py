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
				reverse=True)
		# frontier is actual Blog instances!
		self.frontier=set(query)
		self.parser = Parser(self)
		# what we gather
		self.images = {}


	# choose next blog to visit
	def next_blog(self):
		# pick random blog from frontier list
		blog = self.frontier.pop()
		# move blog to visited list and save time
		self.visited[blog] = time()
		return blog


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
			e.message()
			return None


##############################################################
##############################################################
##############################################################
##############################################################
##############################################################

# parser. 
class Parser:
	def __init__(self, crawler):
		self.crawler = crawler


	def addpage(self, url):
		lastvisit = self.visited.get(url)
		if lastvisit == None:
			if not url in self.frontier:
				self.frontier.update([url])
		linked = self.links.get(self.current)
		if linked:
			linked.update([url])
		else:
			self.links[self.current] = set([url])



	def next(self):
		if len(self.frontier) > 0:
			url = self.frontier.pop()
		else:
			return None
		#lastvisit = self.visited.get(url)
		#if lastvisit == None:
		self.visited[url] = time()
		self.current = url
		return url


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
						href = urljoin(url, ''.join(refparts[2:4]))
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
						href = urljoin(url, ''.join(refparts[2:4]))
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
	m = re.search('_([1-9][0-9]{2,3})\.', imgurl)
	if m:
		dim=int(m.group(1))
		# count down sizes
		for d in filter(lambda x:x>=dim, [1280,800,500,400,250]):
			url = re.sub('_([1-9][0-9]{2,3})\.', '_{}.'.format(d), imgurl)
			try:
				req = Request(url)
				urlopen(req)
				return url
			except:
				pass
	return imgurl
	



#bilder:
# http://stackoverflow.com/questions/3042757/downloading-a-picture-via-urllib-and-python
#

tumblrex=re.compile('(http://)?(\b\w*\.tumblr.com).*')
imgex=re.compile('http://[0-9]{2}\.media\.tumblr\.com(/[0-9a-f]*)?/tumblr_\w*\.(jpg|png)')
idex=re.compile('_(\w{19,})_')
#http://31.media.tumblr.com/f87d34d3d0d945857bd48deb5e934372/
#tumblr_mpkl2n8aqK1r0fb8eo1_500.jpg


images = []
blogs = tumblr.blogs()
pictures = picture

def crawl(url, n=10):
	crawler = Crawler()
	crawler.init(url)
	c=0
	while crawler.next() and c < n:
		crawler.crawl()
		c += 1

	for blog, imgs in crawler.images.items():
		t = tumblr.create(blog)
		for img in imgs:
			#name = idex.search(img).group(1)
			best = best_version(img)
			print best
			#urlretrieve(best, 'images/{}.{}'.format(name,ext))
			pict = picture.openurl(best)
			t.feature(pict)
			images.append(pict)

# go to the internets and browse through there!
def 