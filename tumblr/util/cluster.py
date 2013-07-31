#!/usr/bin/python

import util.measures as measures

class Cluster:
	reg=[]
	def __init__(self, images):
		self.members = images[:]
		self.distances = {'avg':{}, 'single': {}, 'norm': {}}
		self.children = []
		# reg
		Cluster.reg.append(self)
	

	def get_distances(self, other):
		distances=[]
		for p in self.members:
			for q in other.members:
				dist = measures.image_hist_dist(p,q)
				for corr in measures.image_histograms(p,q):
					dist *= 2-corr
				distances.append(dist)
		return distances

	
	def avg_distance(self, other):
		dist = self.distances.get('single').get(other)
		if dist:
			return dist
		# TODO: or maximum, or minimum/single linkage
		distances = self.get_distances(other)
		single = min(distances)
		self.distances.get('single')[other] = single
		other.distances.get('single')[self] = single
		return single


	def single_distance(self, other):
		dist = self.distances.get('avg').get(other)
		if dist:
			return dist
		# TODO: or maximum, or minimum/single linkage
		distances = self.get_distances(other)
		average = min(distances)
		self.distances.get('avg')[other] = average
		other.distances.get('avg')[self] = average
		return average


	def norm_distance(self, other):
		dist = self.distances.get('norm').get(other)
		if dist:
			return dist
		# TODO: or maximum, or minimum/single linkage
		distances = self.get_distances(other)
		single = min(distances)*(1+max(distances)-min(distances))
		self.distances.get('norm')[other] = single
		other.distances.get('norm')[self] = single
		return single
	

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
	

LINK_AVG='avg'
LINK_SINGLE='single'
LINK_NORM='norm'

def linkage(images, goal, mode=LINK_AVG):
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
				if mode == LINK_AVG:
					dist = a.avg_distance(b)
				elif mode == LINK_SINGLE:
					dist = a.single_distance(b)
				else:
					dist = a.norm_distance(b)
				if dist < best[2]:
					best = (a, b, dist)
		c = merge(best[0], best[1])
		clusters = Cluster.reg
	return clusters


