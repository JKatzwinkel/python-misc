#!/usr/bin/python

import index
import weave.picture as picture
import weave.tumblr as tumblr
import util.cluster as clustering

index.load()
index.inout.save_log('load')
print 'compute scores'
scores = tumblr.dist_scores()
hi=sorted(scores.items(), key=lambda t:t[1])

print 'top 5:'
for i,t in enumerate(hi[-5:][::-1]):
	print i+1, t[0].name, t[0].score

#seed = sorted(index.blogs(), key=lambda t:len(t.proper_imgs))[-1]
seed = sorted(index.blogs(), key=lambda t:t.score)[-1]

proceed=True
imgs = []

while proceed:
	imgs.extend(index.crawl(seed.url(), num=5))
	print 'images so far:', len(imgs)
	proceed = raw_input('continue downloading? ').lower() in ['y', 'yes']

index.save()
index.inout.save_log('save')
