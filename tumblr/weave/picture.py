#!/usr/bin/python
# -*- coding: utf-8 -*- 

from PIL import Image as pil
import os
import os.path
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
		self.info="<unknown>"
		self.mode = ''
		self.size = (0,0)
		self.dim = 0
		self.histogram = None
		self.ext = ''
		self.date = 0 # date of retrieval (timestamp)
		self.url = None #TODO: implementieren
		self.rating = 0
		self.reviewed = 0 # timestamp of last appearance in browser
		# if pil image is given, analyze that
		if isinstance(image, pil.Image):
			self.mode = image.mode
			self.size = image.size
			self.dim = self.size[0]
			self.histogram = Histogram(image)
			self.date = 0 # zusehen, dasz man das aus der datei holt
			self.reviewed = 0
		else:
			# given data must be metadata dictionary
			self.mode = image.get('mode')
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
		# register
		self.info='{0} {1}'.format(self.size, self.mode)#TODO we need?
		Pict.imgs[name]=self
		#print '\r{0}'.format(len(Pict.imgs)),

	# load and show picture
	def show(self):
		print self.sources
		self.pict=self.load()
		if self.pict:
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
	
	# do fancy stuff with img pixel values
	#TODO make fancier
	def palette(self, n=10):
		img = self.load()
		if img:
			px = img.load()
			cols = {}
			w,h = img.size
			# populate color directory:
			# {(R,G,B): count, (r,g,b):..., ...}
			for x in range(0,w,10):
				for y in range(0,h,10):
					i = tuple([c/32*32 for c in px[x,y]])
					cols[i] = cols.get(i,0) + 1
			print 'colors: {}'.format(len(cols))
			# clustering
			while len(cols)>n:
				# merge entries of color directory into clusters of close colors:
				# [((R,G,B),count), (R2,G2,B2),count), (col,n)...]
				# NOTE: may also be grayscale!!
				clst = cols.items()
				# step
				best=(None,None,255**2)
				for i, col1 in enumerate(clst):
					for col2 in clst[i+1:]: #col2 = ((r,g,b), count)
						# calc cluster distance as pairwise square dist in
						# [(r1,r2), (g1,g2), (b1,b2)]
						dist = sum([(t[0]-t[1])**2 for t in zip(col1[0], col2[0])])
						if dist<best[2]:
							# maintain merge candidate best=(((r1,g1,b1),cnt),((r2,g2,b2),n),distance)
							best = (col1, col2, dist)
				# merge closest
				col1, col2, dist = best
				#TODO: merge color components proportional to color frequencies
				i = (col1[1], col2[1]) # extract frequency count from color entries
				cmb = sum(i) # calc combined frequency
				# compute color resulting in merge of closest colors:
				# value per color channel times color frequency in ratio to other color freq
				# ((r1*cnt1+r2*cnt2)/(cnt1+cnt2), (g1*...
				col = tuple([(t[0]*i[0]+t[1]*i[1])/cmb for 
					t in zip(col1[0], col2[0])])
				# delete distinct colors, store merge product
				del cols[col1[0]]
				del cols[col2[0]]
				cols[col] = cmb
		ss = img.size[0]*img.size[1]/100
		del img
		#TODO: save primary colors as object fields!!
		return [(t[0], t[1]*100/ss) for t in cols.items()]

	
	# show siginificant colors
	def show_pal(self, n=5):
		pal = self.palette(n=n)
		hr = sum([t[1] for t in pal])
		print hr
		img = pil.new('RGB', (200,600), 'black')
		pix = img.load()
		pal = sorted(pal, key=lambda t:t[1])
		i = 0
		yy = 0
		for y in range(600):
			for x in range(200):
				pix[x,y]=pal[i][0]
			if y>yy+pal[i][1]*6 and i<n-1:
				yy+=pal[i][1]*6
				i+=1
				print yy,i,pal[i]
		# img.show()
		return img


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
		if loc != None:
			#if re.match('_[1-9][0-9]{2,3}\.(jpg|png)$', loc):
			#FIXME: wtf is this shit???
			if loc.endswith('_{}.{}'.format(self.dim, self.ext)):
				self.path = os.sep.join(loc.split(os.sep)[:-1])
		else:
			self.path = None

	
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
		#dimensions=zip(self.size, pict.size)
		#widths=sorted(dimensions[0])
		#heights=sorted(dimensions[1])
		#msr.append(sqr(1.*widths[0]/widths[1]*heights[0]/heights[1]))
		dimcor = stats.pearson(self.size, pict.size)
		if dimcor:
			msr.append(dimcor)
		#hst=sum(map(lambda (x,y):(x-y)**2, zip(self.histogram, pict.histogram)))
		hstcor=measure.image_histograms(self, pict)
		if hstcor:
			msr.extend(hstcor)
		mood=measure.image_histmediandist(self, pict)
		if mood:
			msr.append(1.-mood)
		#colorful=measure.image_histrelcor(self, pict)
		#if colorful:
			#msr.extend(colorful)
		#dist = measure.image_hist_dist(self, pict)
		#if dist:
			#msr.append(1.-dist/255.)
		res = 1.
		#while len(msr)>0:
			#res *= msr.pop()
		return sum(msr)/len(msr)
		#return res
	
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
		orig = 'unknown'
		if self.origin:
			orig = self.origin.name
			if len(orig)>15:
				orig='{}...'.format(orig[:12])
		return u'<{3} {0}, orig: {1} {2}src r{4}>'.format(
			self.info, orig, len(self.sources),
			self.name, '*'*self.rating)


	# multiple lines of usefuil information
	def details(self):
		ago = util.time_span_str(self.date)
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

	# short description of image for mult line output
	def short_desc(self):
		notes=[]
		if self.rating>0:
			notes.append('*'*self.rating)
		days=util.days_since(self.date)
		if days<7:
			if days<2:
				notes.append('new! ({} hours)'.format(int(days*24)))
			else:
				notes.append('new! ({} days)'.format(int(days)))
		days=int(util.days_since(self.reviewed))
		if days > 31:
			if days < 100:
				notes.append('awaits review ({} days)'.format(days))
			else:
				notes.append('awaits review!')
		if self.origin:
			notes.append(self.origin.name)
			if len(self.sources)>1:
				notes.append('found {}x'.format(len(self.sources)))
		return '\n'.join(notes)


	# del image after call, ok? memory perspective!
	def upgrade(self, image, url, save=True):
		self.ext = url.split('.')[-1]
		m = re.search('_([1-9][0-9]{2,3})\.', url)
		if m:
			self.dim = int(m.group(1))
		else:
			self.dim = image.size[0] # TODO: korrekt?
		if save:
			image.save(self.location)
		self.url = url
		self.size = image.size
		#self.histogram = Histogram(image)


	# download image at url and update metadata accordingly
	# if save=True, local copy is saved to disk/overwritten if present
	# returns upgraded pil image instance, so make sure to del image
	# at some point when calling this!
	def download(self, url=None, save=True):
		if not url:
			url = self.url
		image = util.inout.open_img_url(url)
		self.upgrade(image, url, save=save)
		return image

	# remove string identifiers from link list, either by
	# replacing them with their corresponding instance, or 
	# by deleting them
	def clean_links(self):
		# generate objects for str keys
		objects = [(k, reify(k)) for k in self.relates.keys() ] 
		# repopulate link list
		links = {}
		for k, obj in objects:
			if obj:
				links[obj] = self.relates.get(k)
		#print ' reification impact: {} -> {}'.format(
			#len(self.relates), len(links))
		self.relates = links



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


idex=re.compile('_(\w{19,20})_')

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
	#print type(name)
	#if name in Pict.imgs.values():
		#return name
	return None

# get instance from registry or try to create one from local file,
# or create a dummy
def reify(name):
	p = get(name)
	if not p:
		for ext in ['jpg', 'png']:
			p = openfile('images', '.'.join([name, ext]), name=name)
			if p:
				return p
	else:
		return p
	p = Pict(name, {}, path='images')
	return p

# get random picture
def any():
	return choice(pictures())

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

# imgs last seen
def last_reviewed():
	now = time()
	return sorted(pictures(), key=lambda p:now-p.reviewed)


# highest rated
def favorites():
	# rating times month passed since review
	fav = lambda p:p.rating * (.5+util.days_since(p.reviewed)/31)
	return sorted(pictures(), key=fav, reverse=True)

# at least one star, come on!
def starred():
	return sorted([p for p in pictures() if p.rating>0], key=lambda p:p.rating)[::-1]



# establishes a link between two pictures
def connect(p,q,sim):
	p.relates[q]=sim
	q.relates[p]=sim


# combines two instances of an identical picture to one
def merge(p,q):
	parts = sorted([p,q], key=lambda i:i.size[0]*i.size[1])
	#TODO: todo!
	pict = parts[-1]
	delete(parts[0])


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
			p.path = None

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
		pict.url = url #TODO: why not pict.upgrade(...)?
		pict.ext = url.split('.')[-1]
		m = re.search('_([1-9][0-9]{2,3})\.', url)
		if m:
			pict.dim = int(m.group(1))
		else:
			pict.dim = pict.size[0]
		if save:
			image.save(pict.location)
		del image
		return pict
	else:
		return None



# load image from file
def openfile(path, filename, name=None):
	fn=os.path.join(path, filename)
	try:
		image = pil.open(fn)
		if image:
			if not name:
				name = '.'.join(filename.split('.')[:-1])
			# check if instance is present at key
			pict = get(name)
			# if not:
			if not pict:
				# create instance!
				pict = Pict(name, image, path=path)
			else:
				# recover information from file and pil image
				pict.mode = image.mode
				pict.size = image.size
				if pict.dim < pict.size[0]:
					pict.dim = pict.size[0]
				if not pict.path:
					pict.path = path
				pict.histogram = Histogram(image)
			# recover file ext
			ext = filename.split('.')[-1].lower()
			if ext in ['jpg', 'png']:
				pict.ext = ext
			# recover modification date
			if pict.date < 1:
				date = os.stat(fn)
				if date:
					pict.date = date.st_mtime
			# del pil img
			del image
			# return obj
			return pict
	except Exception, e:
		print e.message
		print 'Could not load {}.'.format(fn)
	return None


# open file
def open(fn):
	if os.sep in fn:
		comp = fn.split(os.sep)
		path = os.sep.join(comp[:-1])
		fn = comp[-1]
	else:
		path = 'images'
	pict = openfile(path, fn)
	return pict


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
