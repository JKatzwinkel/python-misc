#!/usr/bin/python

import index
import weave.picture as picture
import util.cluster as clustering

index.crawl('tumblr.com', num=10)
picts = index.pictures()

#for pict in picts:
#	print pict.histogram
#	print pict

index.simpairs()
index.stumblr(picts[0], 'walk.html')
index.saveXML(picts, 'images.xml')

clusters = clustering.avg_linkage(picts, 4)
groups = [c.members for c in clusters]
index.savegroups(groups, 'cluster.html')
