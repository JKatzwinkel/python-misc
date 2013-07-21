#!/usr/bin/python

import index
import weave.crawler as crawler
import weave.picture as picture
import util.inout

crawler.crawl('weloveariagiovanni.tumblr.com', n=1)

picts = picture.pictures()

for pict in picts:
	print pict.histogram
	print pict

util.inout.saveXML(picts, 'test.xml')