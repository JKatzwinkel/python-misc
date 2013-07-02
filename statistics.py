#!/usr/bin/python

from math import pow, sqrt

def pearson(X, Y):
	N=len(X)
	meanX=1.*sum(X)/N
	meanY=1.*sum(Y)/N
	
	sDevProd=0
	cov=0
	for i in range(0,N):
		varX=X[i]-meanX
		varY=Y[i]-meanY
		cov+=varX*varY
		sDevProd+=varX**2*varY**2
	sDev=sqrt(sDevProd)
	return cov/sDev
