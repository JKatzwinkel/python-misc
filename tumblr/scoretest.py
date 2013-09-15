# -*- coding: utf-8 -*- 
import index as ix

ix.load()

imgs=sorted(ix.picture.pictures(), key=lambda p:p.rating)
blogs=sorted(ix.tumblr.blogs(), key=lambda t:t.avg_img_rating())

print 'distributing blog scores...'
scores=ix.tumblr.dist_scores()
print 'sorting blogs by score'
hi=sorted(scores.items(), key=lambda t:t[1])

stars = {}
for p in imgs[-40:]:
	t = p.origin
	if t:
		stars[t] = stars.get(t,0)+p.rating

print ' '.join(['name','stars','imgs','local/blog',
	'links','in/out']),
print 'avg* - SCORE'
print '_'*75
for t,s in sorted(stars.items(),key=lambda x:x[1]):
	print u'{} - {}* {}/{}imgs ⇶{}/{}⇶'.format(
		t.name,s,len(t.proper_imgs),len(t.images),
		len(t.linked),len(t.links)),
	print '{:.2f}* - score {:.2f}'.format(t.avg_img_rating(),
		scores.get(t))

print 'ok'