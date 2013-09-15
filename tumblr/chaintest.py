import index
from random import randrange as rnd

index.load()

for n in range(6):
	stars = sorted(index.pictures(), key=lambda p:p.rating, reverse=True)[:5+n*2]
	query = []

	print 'Checkpoints:'
	for i in range(3+n):
		p = stars[rnd(len(stars))]
		query.append(p)
		stars.remove(p)
		print '{}. {}'.format(i+1, p.name)

	path = index.chain(query=query)

	print '\nPath:'
	print ' > '.join([p.name for p in path])

	reference = [p for p in query if p in path]
	index.export_html(reference+[None]+path, 'path{}.html'.format(n))