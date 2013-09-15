#!/usr/bin/python

from random import choice

import index
import weave.picture as picture
import weave.tumblr as tumblr
import util.cluster as clustering

index.load()
index.inout.save_log('load')
print 'compute scores'
scores = tumblr.dist_scores()
hi=sorted(scores.items(), key=lambda t:t[1])

print 'top 10:'
for i,t in enumerate(hi[-10:][::-1]):
	print i+1, t[0].name, t[0].score

#seed = sorted(index.blogs(), key=lambda t:len(t.proper_imgs))[-1]
#seed = sorted(index.blogs(), key=lambda t:t.score)[-1]
seed = choice(index.blogs())

proceed=True
imgs = []

n=9
while proceed:
	imgs.extend(index.crawl(seed.url(), num=n))
	print 'images so far:', len(imgs)
	proceed = raw_input('continue downloading? ').lower() in ['y', 'yes']
	n=max(n-1,3)

index.save()
index.inout.save_log('save')
