#!/usr/bin/python

from random import choice
import sys

import index
import weave.picture as picture
import weave.tumblr as tumblr
import util.cluster as clustering

index.load(recover=True)
index.inout.save_log('load')
print 'compute scores'
scores = tumblr.dist_scores(n=1,reset=False)
hi=sorted(scores.items(), key=lambda t:t[1])

print 'top 10:'
for i,t in enumerate(hi[-10:][::-1]):
	print i+1, t[0].name, t[0].score

seed = None
if len(sys.argv) > 1:
	#TODO: all params!
	url = sys.argv[-1]
	if url in ['-r', '-rnd']:
		seed = tumblr.any().url()
	elif tumblr.proper_url(url) or url.count('.')<1:
		seed = url
#if not seed:
	#seed = sorted(index.blogs(), key=lambda t:len(t.proper_imgs))[-1]
	#seed = sorted(index.blogs(), key=lambda t:t.score)[-1]
	#if len(index.blogs())>0:
		#seed = choice(index.blogs()).url()

proceed=True
imgs = []

n=9
while proceed:
	imgs_new = index.crawl(seed, num=n)
	imgs.extend(imgs_new)
	#for i,p in enumerate(imgs_new):
		#for q in imgs_new[i+1:]:
			#if p.origin == q.origin:
				#sim = p.similarity(q)
				#if sim>.45:
					#picture.connect(p,q,sim)
	print 'images so far:', len(imgs)
	seed = None
	proceed = raw_input('continue downloading? ').lower() in ['y', 'yes']
	n=max(n-1,3)

index.save()
index.inout.save_log('save')
