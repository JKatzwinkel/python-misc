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
		dist = other.distances.get('single').get(self)
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
	clusters = [Cluster([p]) for p in images]
	# continue until number is reached
	while len(clusters) > goal:
		best = (None, None, 10000)
		for i,a in enumerate(clusters):
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


sims = lambda p,o: [0]+[p.relates.get(q) for q in o if q in p.relates]
msim = lambda l,o: max([max(sims(p,o)) for p in l])

class Clust:
	reg=[]
	def __init__(self, p):
		self.imgs = [p]
		self.sim = {}
		Clust.reg.append(self)
	
	def similarity(self, other):
		if other == self:
			return 1
		s = self.sim.get(other)
		if s:
			return s
		s = msim(self.imgs, other.imgs)
		self.sim[other] = s
		#other.sim[self] = s
		return s
	
	@staticmethod
	def verkuppel():
		best=(None,None,-1)
		cands = Clust.reg[:]
		while len(cands)>0 and best[2]<1:
			a = cands.pop()
			for b in cands:
				s = b.similarity(a)
				if s > best[2]*.95:
					if s > best[2] or len(b.imgs)<len(best[0].imgs):
						best = (b,a,s)
		b,a,s=best
		Clust.reg.remove(a)
		b.marry(a)


	def marry(self, other):
		noobs=other.imgs
		self.imgs.extend(noobs)
		i = Clust.reg.index(self)
		left = Clust.reg[:i]
		right = Clust.reg[i+1:]
		#self.sim = {k:max([self.sim.get(k,0),msim(noobs,k.imgs)]) for k in right}
		self.sim = {k:max([self.sim.get(k,0),other.sim.get(k,0)]) for k in right}
		for k in left:
			k.sim[self] = max([k.sim.get(self,0),k.sim.get(other,0)])


def cluster(imgs, num):
	if len(Clust.reg)<1:
		cc = [Clust(p) for p in imgs]
	if len(Clust.reg)>num:
		for i in range(2):
			Clust.verkuppel()
	return Clust.reg

