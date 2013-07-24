#!/usr/bin/python

import index
import weave.picture as picture
import weave.tumblr as tumblr
import util.cluster as clustering

index.load()

#seed = sorted(index.blogs(), key=lambda t:len(t.proper_imgs))[-1]
seed = sorted(index.blogs(), key=lambda t:t.score)[-1]

index.crawl(seed.url(), num=20)
picts = index.pictures()
blogs = index.blogs()

index.simpairs()
index.stumblr(picts[0], 'walk.html')

index.save()

clusters = clustering.avg_linkage(picts, 3)
groups = [c.members for c in clusters]
index.savegroups(groups, 'cluster.html')
