#!/usr/bin/python

import index
import weave.picture as picture
import util.cluster as clustering

index.crawl('tumblr.com', num=5)
picts = index.pictures()
blogs = index.blogs()

#for pict in picts:
#	print pict.histogram
#	print pict

index.simpairs()
index.stumblr(picts[0], 'walk.html')

index.saveImages(picts, 'images.xml')
index.saveBlogs(blogs, 'blogs.xml')

clusters = clustering.avg_linkage(picts, 10)
groups = [c.members for c in clusters]
index.savegroups(groups, 'cluster.html')
