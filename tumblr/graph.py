import index
index.tumblr.load()
index.tumblr.remove(index.tumblr.rank(1))
a=index.tumblr.rank(3)
index.inout.dot_render(index.tumblr.favs()[:90], 'favs.png')
lin = [index.tumblr.link_path(b,a) for b in index.tumblr.favs()[3:50]]
lout = [index.tumblr.link_path(a,b) for b in index.tumblr.favs()[3:300]]
index.inout.dot_render_paths(lout, lin, 'paths.png')
