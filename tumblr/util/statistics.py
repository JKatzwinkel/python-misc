#!/usr/bin/python

from math import pow, sqrt

def pearson(X, Y):
	N=len(X)
	meanX=1.*sum(X)/N
	meanY=1.*sum(Y)/N
	N-=1
	# standard deviation
	sDevX=sqrt(sum([(x-meanX)**2 for x in X])/N)
	sDevY=sqrt(sum([(y-meanY)**2 for y in Y])/N)

	if sDevX != 0 and sDevY != 0:
		r=sum([(x-meanX)/sDevX*(y-meanY)/sDevY for (x,y) in zip(X,Y)])/N
		return r
	else:
		return None
	

def median_histogram(H):
	total=0
	half=sum(H)/2
	for bin, occ in enumerate(H):
		total+=occ
		if total>=half:
			return bin
