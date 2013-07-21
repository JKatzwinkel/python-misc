#!/usr/bin/python

from PIL import Image as pil
import os
from random import choice
from math import sqrt as sqr
import util.statistics as stats
import util.measures as measure

def scaledown(a):
	return [a[i]+a[i+1] for i in range(0,len(a),2)]

class Histogram:
	def __init__(self, image):
		data=[]
		bands=1
		if isinstance(image, pil.Image):
			data = image.histogram()
			bands = min(3, len(image.mode)) # cut A band of RGBA images
		elif type(image) is list:
			data = image[:]
			bands=1
			if len(data)>64:
				bands=3
		# struct band hists
		self.bands = []
		size=max(len(data)/bands, 32)
		for b in range(0,len(data), size):
			self.bands.append(data[b:b+size])
		# prepare median values
		self.mediane = [stats.median_histogram(band) 
											for band in self.bands]
		self._hex=''

	def hex(self):
		if len(self._hex)<1:
			aa=[]
			for band in self.bands:
				aa.extend(band)
			self._hex=''.join([('%02x' % b) for b in aa])
		return self._hex



# featured Image
class Pict:
	imgs={}
	def __init__(self, path, name, slots={}):
		self.path=path
		self.name=name
		self.sources=[]
		self.info="<unknown>"
		self.mode=slots.get('mode','None')
		self.size=slots.get('size',(0,0))
		self.histogram=slots.get('histogram', [])
		self.histoscale=slots.get('histoscale', 1)
		if len(self.histogram) < 1:
			filename=os.sep.join([self.path, self.name])
			try:
				self.pict=pil.open(filename)
				self.size=self.pict.size
				self.mode=self.pict.mode
				self.histogram=self.pict.histogram()
				del self.pict
				#os.remove(filename)
				# scale down histogram
				#ratio=len(self.histogram)/96
				#hist=[sum(self.histogram[i*ratio:(i+1)*ratio]) for i in range(0,32)]
				#self.histogram=[v/ratio for v in hist]
				#while len(self.histogram)>32:
				hist=self.histogram[:]
				for i in [1,2,3]:
					if len(hist)>96 or self.mode != 'RGB':
						hist=scalehalf(hist) # scale histogram down to 32re tones
				norm=max(hist)/255.
				if norm>1:
					self.histogram=[int(v/norm) for v in hist]
					self.histoscale=int(norm)
				else:
					self.histogram=hist[:]
				if self.mode=='RGBA':
					self.histogram=self.histogram[:96]
					self.mode='RGB'
			except:
				print filename, 'broken' 
		self.info='{0} {1}'.format(self.size, self.mode)
		self.relates={}
		Tum.imgs[name]=self
		#print '\r{0}'.format(len(Tum.imgs)),

	def show(self):
		print self.sources
		self.pict=pil.open(os.sep.join([self.path, self.name]))
		self.pict.show()
		del self.pict
	
	
	@property
	def location(self):
		return os.sep.join([self.path, self.name])
	
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
		return sum(msr)/len(msr)
	
	# finds related images
	def similar(self, n=10):
		sim=[]
		hosts=self.sources[:]
		sim.extend([choice(Tum.imgs.values()) for i in range(n*2)])
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
	
	def __repr__(self):
		if len(self.sources) > 0:
			return '<{0}, orig: {1} ({2} src)>'.format(
				self.info, self.sources[0], len(self.sources))
		return '<{0} - No record> '.format(self.info)
	
	#simple histogram representation
	@property
	def hist(self):
		res=[]
		for thresh in [200,150,100,50,25,0]:
			row=[[' ','.',':'][int(v>thresh)+int(v>thresh+15)] for v in
				self.histogram]
			res.append(''.join(row))
		return "\n".join(res)
		#return ''.join([" _.-~'^`"[v/36] for v in self.histogram])
