#!/usr/bin/python
from random import randrange as rnd
import index
index.tumblr.load()
index.tumblr.remove(index.tumblr.rank(1))

a=index.tumblr.rank(rnd(20))
while len(a.links)*len(a.linked)<1:
	a=index.tumblr.rank(rnd(20))
	
index.inout.dot_render(index.tumblr.favs()[:90], 'favs.png')
lin = [index.tumblr.link_path(b,a) for b in index.tumblr.favs()[:50]]
lout = [index.tumblr.link_path(a,b) for b in index.tumblr.favs()[:100]]
index.inout.dot_render_paths(lout, lin, 'paths.png')

longest=[[]]
for b in index.tumblr.favs()[:700]:
	path = index.tumblr.link_path(a,b,way=1)
	if len(path)>len(longest[-1])*2/3:
		longest.append(path)
		print len(path)

index.inout.dot_render_paths(longest, [[]], 'longest.png')

