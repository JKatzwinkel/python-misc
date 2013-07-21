#!/usr/bin/python
from urllib2 import urlopen, Request
from urllib import urlretrieve
from bs4 import BeautifulSoup
from urlparse import urlparse, urlsplit, urljoin
import re
from time import time

import weave.picture as picture
import weave.tumblr as tumblr

# crawler. 
class Crawler:
	def __init__(self):
		self.visited={}
		self.frontier=set()
		self.links={}
		self.images={}
		self.current = None

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

	def init(self, url):
		self.frontier.update([url])

	def crawl(self):
		# check url scheme
		url = self.current
		refparts = urlsplit(url)
		if not refparts.scheme:
			url=''.join(['http://', url])
		# request
		req = Request(url)#, headers={
			#'User Agent':'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:16.0) Gecko/20100101 Firefox/16.0',
			#'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
			#'Accept-Language': 'en-US,en;q=0.5',
			#'Accept-Encoding': 'gzip, deflate',
			#'Connection': 'keep-alive',
			#'DNT': '1',
			#'If-Modified-Since': 'Sat, 20 July 2013 01:43:23 GMT',
			#'Cache-Control': 'max-age=0'
			#})
		print url
		page = urlopen(req)
		mimetype = page.info().gettype()
		if mimetype != 'text/html':
			return
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
					if tumblrex.match(href):
						links.update([href])
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
						imgs.update([src])
		# save
		for link in list(links):
			self.addpage(link)
		self.links[self.current] = links
		self.images[self.current] = imgs


def best_version(imgurl):
	m = re.search('_([1-9][0-9]{2,3})\.', imgurl)
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

tumblrex=re.compile('(http://)?\w*\.tumblr.com')
imgex=re.compile('http://[0-9]{2}\.media\.tumblr\.com(/[0-9a-f]*)?/tumblr_\w*\.(jpg|png)')
idex=re.compile('_(\w{19})_')
#http://31.media.tumblr.com/f87d34d3d0d945857bd48deb5e934372/
#tumblr_mpkl2n8aqK1r0fb8eo1_500.jpg


images = []

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
