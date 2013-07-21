#!/usr/bin/python

import util.measures as measures

class Cluster:
	reg=[]
	def __init__(self, images):
		self.members = images[:]
		self.distances = {}
		self.children = []
		# reg
		Cluster.reg.append(self)
	
	
	def distance(self, other):
		distances = []
		dist = self.distances.get(other)
		if dist:
			return dist
		for p in self.members:
			for q in other.members:
				dist = measures.image_hist_dist(p,q)
				for corr in measures.image_histograms(p,q):
					dist *= 2-corr
				distances.append(dist)
		# TODO: or maximum, or minimum/single linkage
		average = sum(distances) / (len(self) * len(other))
		self.distances[other] = average
		other.distances[self] = average
		return average

	
	def __len__(self):
		return len(self.members)


def merge(a, b):
	members = a.members
	members.extend(b.members)
	c = Cluster(members)
	Cluster.reg.remove(a)
	Cluster.reg.remove(b)
	c.children.extend([a,b])
	return c
	

def avg_linkage(images, goal):
	Cluster.reg = []
	clusters = []
	for p in images:
		clusters.append(Cluster([p]))
	# continue until number is reached
	while len(clusters) > goal:
		best = (None, None, 10000)
		for i in range(len(clusters)):
			a=clusters[i]
			for b in clusters[i+1:]:
				dist = a.distance(b)
				if dist < best[2]:
					best = (a, b, dist)
		c = merge(best[0], best[1])
		clusters = Cluster.reg
	return clusters
