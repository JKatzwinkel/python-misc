#!/usr/bin/python

import index
import weave.crawler as crawler
import weave.picture as picture
import util.inout

crawler.crawl('.tumblr.com', n=50)

picts = picture.pictures()

for pict in picts:
	print pict.histogram
	print pict

index.simpairs()
index.stumblr(picts[0], 'walk.html')

util.inout.saveXML(picts, 'images.xml')