#!/usr/bin/python

from PIL import Image as pil
import os
from random import choice
from math import sqrt as sqr
import re

import util.statistics as stats
import util.measures as measure
import util.inout

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
	def __init__(self, path, name, image):
		self.path=path
		self.name=name
		self.sources=[]
		self.relates={} # TODO
		#self.info="<unknown>"
		#self.mode = ''
		#self.size = (0,0)
		#self.dim = 0
		#self.ext = ''
		if isinstance(image, pil.Image):
			self.mode = image.mode
			self.size = image.size
			self.histogram = Histogram(image)
		else:
			self.mode = image.get('mode','None')
			self.size = image.get('size',(0,0))
			histogram = image.get('histogram', [])
			self.histogram = Histogram(histogram, bands=image.get('bands'))
			self.dim = image.get('format', 500)
			self.ext = image.get('extension', 'jpg')
			self.relates = image.get('similar', {})
			self.sources = image.get('hosted', [])

		self.info='{0} {1}'.format(self.size, self.mode)
		Pict.imgs[name]=self
		#print '\r{0}'.format(len(Pict.imgs)),

	# load and show picture
	def show(self):
		print self.sources
		self.pict=pil.open(self.location)
		self.pict.show()
		del self.pict
	
	@property
	def filename(self):
		return '{}_{}.{}'.format(self.name, self.dim, self.ext)

	@property
	def location(self):
		return os.sep.join([self.path, self.filename])
	
	@property
	def origin(self):
		if len(self.sources)>0:
			return self.sources[0]
		return None
	
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
	p = Pict.imgs.get(name)
	if p:
		return p
	m = idex.search(name)
	if m:
		p = Pict.imgs.get(m.group(1))
	return p


# return all instances aliove
def pictures():
	return Pict.imgs.values()


# establishes a link between two pictures
def connect(p,q,sim):
	p.relates[q]=sim
	q.relates[p]=sim



##############################################################
##############         Image IO         ######################
##############################################################


# loads the image at the given URL and returns a Pict image container
def openurl(url, save=True):
	image = util.inout.open_img_url(url)
	if image:
		m = idex.search(url)
		if m != None:
			name = m.group(1)
		else:
			name = url.split('/')[-1]
			print 'WARNING: ', name
		# do we have it alerady?
		pict = lookup(name)
		if pict:
			print '{} already here: {}'.format(url, pict)
			#if pict.dim < dim:
				#print 'But format is better: {} vs. {}'.format(pict.dim, dim)
		else:
			pict = Pict('images', name, image) #TODO
			pict.ext = url.split('.')[-1]
			m = re.search('_([1-9][0-9]{2,3})\.', url)
			if m:
				pict.dim=int(m.group(1))
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
			pict = Pict(path, name, image)
			del image
			return pict
	except Exception, e:
		print e.message
		print 'Could not load {}.'.format(fn)
	return None


# create pict cntainer from single record
def opendump(slots):
	loc = slots.get('location')
	if loc:
		loc = loc.split(os.sep)
		path = os.sep.join(loc[:-1])
		name = slots.get('id')
		return Pict(path, name, slots)
	return None

