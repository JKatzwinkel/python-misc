#!/usr/bin/python

from math import sqrt as sqr
from random import randrange as rnd
import util.statistics as stats

# statistics and similarity measure repositories
# for Images
hist_distances = {}
hist_correlations = {}

def lookup(registry, p, q):
	p,q = sorted([p,q])
	record = registry.get(p, {})
	v = record.get(q)
	if v:
		return v
	registry[p] = record

def register(registry, p, q, value):
	p,q = sorted([p,q])
	record = registry.get(p, {})
	record[q] = value
	registry[p] = record
	

# computes the similarity of two picture's histograms
# based on Pearson coefficient
def image_histograms(p, q):
	# asume number color tones has been reduced to 32 by Picture class
	# if those two pictures are not in the same colorspace, thats no prob
	# while the first one might visit its B, G, and R histograms, the other
	# one just stays in its black'n'white space.
	# handle maximum colorspace, however
	#colspace=sorted([p.mode, q.mode], key=lambda m:len(m))[-1]
	v = lookup(hist_correlations, p, q)
	if v:
		return v
	bands = max(p.histogram.bands, q.histogram.bands)
	correlations=[]
	for offset in range(bands):
		h1 = p.histogram.array(bands=bands)
		h2 = q.histogram.array(bands=bands)
		off1=offset*32%len(h1)
		off2=offset*32%len(h2)
		corr=stats.pearson(h1[off1:off1+32], h2[off2:off2+32])
		correlations.append(corr)
	# now how do we put them together?
	#res=sum(correlations)/len(correlations)
	register(hist_correlations, p, q, correlations)
	return correlations
	

# gibt einen abstand der farbaussteuerungen
# zurueck
def image_histmediandist(p,q):
	mediane=[p.histogram.mediane, q.histogram.mediane]
	dists=map(lambda (x,y):sqr((x-y)**2), zip(mediane[0], mediane[1]))
	dist=sum(dists)/32.
	return dist

# wie bunt?
def image_histrelcol(p):
	hist=p.histogram.array(bands=3)
	#print len(hist), p.name
	res=[]
	if len(hist)>32:
		grey=[sum(
			[hist[i],hist[(i+32)%len(hist)],
			hist[(i+64)%len(hist)]])/3 for i in range(32)]
		for bank in range(3):
			res.extend(
				[v-grey[i] for (i,v) in enumerate(hist[bank*32:(bank+1)*32])])
	else:
		for bank in range(3):
			res.extend([hist[i]/(i-17.5) for i in range(32)])
	return res


# korrelier das
def image_histrelcor(p,q):
	corrs=[]
	rel=[image_histrelcol(p), image_histrelcol(q)]
	for bank in range(0,96,32):
		cor=stats.pearson(rel[0][bank:bank+32], rel[1][bank:bank+32])
		corrs.append(cor)
	return corrs


# difference between the histograms of two pictures
def image_hist_dist(p, q):
	v = lookup(hist_distances, p, q)
	if v:
		return v
	dist = p.histogram.distance(q.histogram)
	register(hist_distances, p, q, dist)
	return dist
	
