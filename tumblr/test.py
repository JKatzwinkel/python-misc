#!/usr/bin/python

import index
import weave.picture as picture
import weave.tumblr as tumblr
import util.cluster as clustering

index.load()

index.simpairs()
index.save()

pics =  picture.pictures()
pics = sorted(pics, key=lambda p:len(p.relates))
index.stumblr(pics[-1], 'walk.html')


clusters = clustering.linkage(pics, len(pics)/10, mode=clustering.LINK_NORM)
groups = [c.members for c in clusters]
index.savegroups(groups, 'cluster.html')
