#!/usr/bin/python

from PIL import Image as pil
import os
from random import choice
from math import sqrt as sqr
import re
from time import time

import util.statistics as stats
import util.measures as measure
import util.inout
import util


# scale down to half size
def scaledown(a):
	return [a[i]+a[i+1] for i in range(0,len(a),2)]





##################################################################

# bw or color histogram of an image
class Histogram:
	# create a histogram object representing an image's histogram
	# or histogram data passed as an array
	def __init__(self, image, bands=0):
		data=[]
		if isinstance(image, pil.Image):
			try:
				data = image.histogram()
				bands = min(3, len(image.mode)) # cut A band of RGBA images
				# scale, normalize
				# only if data is extracted from actual image
				while len(data) > bands*32:
					data = scaledown(data)
				# normalize: 255 means entire image is of colors of a bin
				h,w = image.size
				maxx = h*w
				data = [bin * 255. / maxx for bin in data]
			except:
				data = [10]*96
		# if hostogram is given as a list, guess number of color bands
		elif type(image) is list:
			data = image[:]
			if bands < 1:
				bands=1
				if len(data)>64:
					bands=3
		# struct band hists
		self.data = []
		self.bands = bands
		# split array into color histograms
		size=max(len(data)/bands, 32)
		for b in range(0,len(data), size):
			self.data.append(data[b:b+size])
		# prepare median values
		self.mediane = [stats.median_histogram(band) 
											for band in self.data]
		self._hex=''


	# return hex representation
	def hex(self):
		if len(self._hex)<1:
			aa = self.array()
			self._hex=''.join([('%02x' % b) for b in aa])
		return self._hex


	# returns all bands in one single array
	def array(self, bands=None):
		aa=[]
		for band in self.data:
			aa.extend(band)
		if bands:
			while len(aa) < bands*32:
				aa.extend(aa)
		return aa


	# calculate distance between two image histograms
	def distance(self, other):
		bands=max(self.bands, other.bands)
		a = self.array(bands=bands)
		b = other.array(bands=bands)
		comp = zip(a, b)
		dist = sum(map(lambda (i,j):(i-j)**2, comp))/len(comp)
		return dist**.5


	#simple histogram representation
	def __repr__(self):
		res=[]
		for thresh in [200,150,100,50,25,0]:
			row=[[' ','.',':'][int(v>thresh)+int(v>thresh+15)] for v in
				self.array()]
			res.append(''.join(row))
		return "\n".join(res)





##############################################################
##############################################################
##############################################################
##############################################################
##############################################################
##############################################################
##############################################################
##############################################################
##############################################################
##############################################################
##############################################################
##############################################################

# featured Image
class Pict:
	# registry
	imgs={}
	# initialize for given 
	def __init__(self, name, image, path='images'):
		# TODO: eigentlich ist der pfad hier ueberfluessig. der indexer
		# sollte ein default projektverzeichnise fuehren, wo er
		# alle bilder reinschmeiszt und rausholt. fuer abweichende
		# verzeichnisse koennte der parameter optional gemacht werden
		# TODO> dann haette man auch eine einfache moeglichkeit, 
		# geloeschte von vorhandenen bildern zu unterscheiden ohne
		# unterschiedliche klassen verwenden oder die metadaten
		# wegschmeiszen zu muessen.
		self.path=path
		self.name=name
		self.sources=[]
		self.relates={} # TODO
		#self.info="<unknown>"
		#self.mode = ''
		#self.size = (0,0)
		#self.dim = 0
		#self.ext = ''
		#self.date = 0 # date of retrieval (timestamp)
		self.url = None #TODO: implementieren
		self.rating = 0
		self.reviewed = 0 # timestamp of last appearance in browser
		if isinstance(image, pil.Image):
			self.mode = image.mode
			self.size = image.size
			self.histogram = Histogram(image)
			self.date = 0 # zusehen, dasz man das aus der datei holt
			self.reviewed = 0
		else:
			self.mode = image.get('mode','None')
			self.size = image.get('size',(0,0))
			self.url = image.get('url')
			histogram = image.get('histogram', [])
			self.histogram = Histogram(histogram, bands=image.get('bands'))
			self.dim = int(image.get('format', 500))
			self.ext = image.get('extension', 'jpg')
			self.date = float(image.get('time', 0))
			self.relates = image.get('similar', {})
			self.sources = image.get('hosts', [])
			self.rating = int(image.get('stars', 0))
			self.reviewed = float(image.get('reviewed', 0))

		self.info='{0} {1}'.format(self.size, self.mode)
		Pict.imgs[name]=self
		#print '\r{0}'.format(len(Pict.imgs)),

	# load and show picture
	def show(self):
		print self.sources
		if self.path:
			self.pict=pil.open(self.location)
			self.pict.show()
			del self.pict
			return True
		else:
			print 'no copy.'
			return False

	# load copy from hard disk and return as pil Image
	def load(self):
		if self.path:
			return pil.open(self.location)
		print 'no copy.'


	
	@property
	def filename(self):
		return '{}.{}'.format(self.name, self.ext)

	@property
	def location(self):
		if self.path:
			return os.sep.join([self.path, self.filename]).strip()
		else:
			return None
	@property
	def set_location(self, loc):
		if self.loc != None:
			#if re.match('_[1-9][0-9]{2,3}\.(jpg|png)$', loc):
			if log.endswith('_{}.{}'.format(self.dim, self.ext)):
				self.path = os.sep.join(loc.split(os.sep)[:-1])
		else:
			self.path = loc

	
	@property
	def origin(self):
		if len(self.sources)>0:
			return self.sources[0]
		return None


	# remove string identifiers from link list, either by
	# replacing them with their corresponding instance, or 
	# by deleting them
	def clean_links(self):
		# generate objects for str keys
		objects = [(k, get(k)) for k in self.relates.keys() ] 
		# repopulate link list
		links = {}
		for k, obj in objects:
			if obj:
				links[obj] = self.relates.get(k)
		#print ' reification impact: {} -> {}'.format(
			#len(self.relates), len(links))
		self.relates = links

	
	# calculates similarity measure between two images
	# -1: negative correlation, 1: perfect correlation/identity
	def similarity(self, pict):
		# distance of sizes
		#dim=sum(map(lambda (x,y):(x-y)**2, zip(self.size, pict.size)))
		#dim/=self.size[0]**2+self.size[1]**2
		msr=[]
		dimensions=zip(self.size, pict.size)
		widths=sorted(dimensions[0])
		heights=sorted(dimensions[1])
		msr.append(sqr(1.*widths[0]/widths[1]*heights[0]/heights[1]))
		#hst=sum(map(lambda (x,y):(x-y)**2, zip(self.histogram, pict.histogram)))
		hstcor=measure.image_histograms(self, pict)
		msr.extend(hstcor)
		mood=measure.image_histmediandist(self, pict)
		msr.append(1-mood)
		colorful=measure.image_histrelcor(self, pict)
		msr.extend(colorful)
		dist = measure.image_hist_dist(self, pict)
		msr.append(1-dist/255)
		return sum(msr)/len(msr)
	
	# finds related images
	def similar(self, n=10):
		sim=[]
		hosts=self.sources[:]
		sim.extend([choice(Pict.imgs.values()) for i in range(n*2)])
		while hosts != [] and len(sim)<n*10:
			host=hosts.pop(0)
			hosts.extend(host.relates)
			sim.extend(host.popular)
		sim=list(set(sim))
		if self in sim:
			sim.remove(self)
		ann=[(p,self.similarity(p)) for p in sim]
		for p,sm in ann:
			if sm>.85:
				connect(self,p,sm)
		ann.sort(key=lambda x:x[1], reverse=True)
		return ann[:n]

	# returns the n images most similar to this one.
	# n is not limited by default
	def most_similar(self, n=None):
		res = sorted(self.relates.items(), key=lambda t:t[1])
		res = [t[0] for t in res[::-1]]
		if n:
			res = res[:n]
		return res

	# look how two pictures are related
	def compare(self, pict):
		sim=self.similarity(pict)
		if sim>.85:
			connect(self,pict,sim)
		print 'Similarity: {:2.3f}'.format(sim)
		print 'Color mood dist: {:2.3f}'.format(
			measure.image_histmediandist(self, pict))
		for p in [self, pict]:
			print '\tInfo:     \t{}'.format(p.info)
			print '\tNamespace:\t{}'.format(p.path)
			print '\tFilename: \t{}'.format(p.name)
			print '\tHistogram:\t{}'.format(p.hist)
			print '\tSources:\n\t\t',
			for source in p.sources:
				print source.name,
			print 
	
	# tostring
	def __repr__(self):
		if len(self.sources) > 0:
			return '<{0}, orig: {1} ({2} src)>'.format(
				self.info, self.sources[0], len(self.sources))
		return '<{0} - No record> '.format(self.info)

	# multiple lines of usefuil information
	def details(self):
		ago = util.inout.time_span_str(self.date)
		return '\n'.join([
			'Rating: {}'.format('*'*self.rating),
			'Size: {}x{} Pixels'.format(self.size[0], self.size[1]),
			'Filename: {}'.format(self.name),
			'Mode: {} {}'.format(self.mode, self.ext),
			'Seen {} times, first on {}'.format(len(self.sources), self.origin),
			'Timestamp {}, downloaded {}'.format(self.date, ago),
			'',
			'Histogram channel medians: {}'.format(
				map(lambda v:v*8, self.histogram.mediane))
			])

	# del image after call
	def upgrade(self, image, url, save=True):
		self.ext = url.split('.')[-1]
		m = re.search('_([1-9][0-9]{2,3})\.', url)
		if m:
			self.dim = int(m.group(1))
		else:
			self.dim = image.size[0] # TODO: korrekt?
		if save == True:
			image.save(self.location)
		self.url = url
		self.size = image.size
		
		


##############################################################
##############################################################
##############################################################
##############################################################
##############################################################
##############################################################
##############################################################
##############################################################
##############################################################
##############################################################
##############################################################
##############################################################


idex=re.compile('_(\w{19})_')

# find image by name
def get(name):
	if type(name) == str:
		p = Pict.imgs.get(name)
		if p:
			return p
		m = idex.search(name)
		if m:
			p = Pict.imgs.get(m.group(1))
		return p
	print type(name)
	if name in Pict.imgs.values():
		return name
	return None


# return all image instances that are saved to a local file
def pictures():
	return filter(lambda p:p.location != None, Pict.imgs.values())

# pictures downloaded within last 12 h
def newest():
	now = time()
	return [p for p in pictures() if p.date>now-3600*24*7]

# pictures awaiting appearance in browser
# = those not seen for a month
def to_review():
	now = time()
	return [p for p in pictures() if p.reviewed<now-3600*24*31]

# highest rated
def favorites():
	# rating times month passed since review
	fav = lambda p:p.rating * (.5+util.days_since(p.reviewed)/31)
	return sorted(pictures(), key=fav, reverse=True)


# establishes a link between two pictures
def connect(p,q,sim):
	p.relates[q]=sim
	q.relates[p]=sim



# update collection. filter removed files, clean references
def sync():
	for p in Pict.imgs.values():
		# replace string identifiers with the instances they reference
		p.clean_links()
		if p.location:
			if not os.path.exists(p.location):
				p.location = None

# delete picture from disk
def delete(p):
	if p.location:
		if os.path.exists(p.location):
			print 'delete image', p
			os.remove(p.location)
			p.location = None
##############################################################
##############         Image IO         ######################
##############################################################


# loads the image at the given URL and returns a Pict image container
def openurl(url, save=True):
	image = util.inout.open_img_url(url)
	if image:
		m = idex.search(url)
		if m:
			name = m.group(1)
		else:
			name = url.split('/')[-1]
			print 'WARNING: ', name
		# do we have it alerady?
		pict = get(name)
		if pict:
			print '{} already here: {}'.format(url, pict)
			pict.upgrade(image, url, save=save)
			del image
			return pict
			#if pict.dim < dim:
				#print 'But format is better: {} vs. {}'.format(pict.dim, dim)
			#else:
				#return pict
		pict = Pict(name, image) #TODO
		pict.url = url
		pict.ext = url.split('.')[-1]
		m = re.search('_([1-9][0-9]{2,3})\.', url)
		if m:
			pict.dim = int(m.group(1))
		else:
			pict.dim = pict.size[0]
		if save == True:
			image.save(pict.location)
		del image
		return pict
	else:
		return None



# load image from file
def openfile(path, filename):
	fn=os.sep.join([path, filename])
	try:
		image = pil.open(fn)
		if image:
			name = idex.search(filename).group(1)
			pict = Pict(name, image, path=path)
			del image
			return pict
	except Exception, e:
		print e.message
		print 'Could not load {}.'.format(fn)
	return None


# create pict cntainer from single record
def opendump(slots):
	loc = slots.get('location')
	name = slots.get('id')
	if loc:
		loc = loc.split(os.sep)
		path = os.sep.join(loc[:-1])
	else:
		path = None
	return Pict(name, slots, path=path)

###############################################################
