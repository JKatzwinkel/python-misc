#!/usr/bin/python

import index
import weave.crawler as crawler
import weave.picture as picture
import util.inout

crawler.crawl('acrosstheweb.tumblr.com', n=20)

picts = picture.pictures()

for pict in picts:
	print pict.histogram
	print pict

index.simpairs()
index.stumblr(picts[0], 'walk.html')

util.inout.saveXML(picts, 'images.xml')