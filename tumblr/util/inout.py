#!/usr/bin/python
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from urllib2 import urlopen, Request
from PIL import Image as pil
from io import BytesIO
import os
from time import time

log_msgs=[]
# save logs to file
def save_log(filename):
	global log_msgs
	if not filename.endswith('.log'):
		filename = '{}.log'.format(filename)
	f=open(os.sep.join(['logs', filename]), 'w+')
	f.write('\n\nIO LOG MSGS {}\n'.format(time()))
	for m in log_msgs:
		f.write('{}\n'.format(m))
	f.close()
	log_msgs=[]


# saves a list of images to an XML file
def saveImages(images, filename):
	print 'saving imgs.',
	f=open(filename, 'w')
	f.write('<?xml version="1.0" standalone="yes"?>\n')
	f.write('<images num="{}">\n'.format(len(images)))
	for p in images:
		#attr=p.name.split('_')
		#extf = attr[-1].split('.')
		f.write(' <image id="{}" extension="{}" mode="{}" format="{}" stars="{}">\n'.format(
						p.name, p.ext, p.mode, p.dim, p.rating))
		attr=p.size
		f.write('  <size width="{}" height="{}"/>\n'.format(attr[0], attr[1]))
		if p.url:
			f.write('  <url>{}</url>\n'.format(p.url))
		# img histogram
		histo = p.histogram
		f.write('  <histogram bands="{}">{}</histogram>\n'.format(
					histo.bands, histo.hex()))
		if p.path:
			f.write('  <location time="{}" reviewed="{}">{}</location>\n'.format(
				p.date, p.reviewed, p.location))
			# list of similar images
			f.write('  <similar num="{}">\n'.format(len(p.relates)))
			# TODO: is this ok? we just cut off similarities as of egde nr. 75...
			for s in sorted(p.relates.items(), key=lambda s:s[1], reverse=True)[:75]:
				f.write('   <img m="{:1.3}">{}</img>\n'.format(s[1],s[0].name))
			f.write('  </similar>\n')
		# list where this img has been found
		f.write('  <hosted times="{}">\n'.format(len(p.sources)))
		for s in p.sources:
			f.write('   <at when="{}">{}</at>\n'.format(
				s.images_times.get(p,0),s.name))
		f.write('  </hosted>\n')			
		f.write(' </image>\n')
	f.write('</images>\n')
	f.close()
	print 'ok.'

##############################################################
##############################################################
##############################################################

# loads image container records from XML file
def loadImages(filename):
	if not os.path.exists(filename):
		print filename, "not found."
		return []
	print 'Reading images metadata from', filename
	imgs=[]
	data={}
	known={}
	warnings=[]
	for event, elem in ET.iterparse(filename, events=('start','end')):
		# ON OPENING TAGS:
		if event == 'start':
			if elem.tag == 'image':
				data=elem.attrib
			if elem.tag == 'size':
				data['size'] = (int(elem.attrib.get('width',0)), 
												int(elem.attrib.get('height',0)))
			if elem.tag == 'location':
				data['location'] = elem.text
				data['time'] = float(elem.attrib.get('time', 0))
				data['reviewed'] = float(elem.attrib.get('reviewed', 0))
			if elem.tag == 'hosted':
				data['hosts']=[]
			if elem.tag == 'similar':
				data['similar']={}
		# REACT ON END TAG
		else:
			if elem.tag == 'histogram':
				data['bands'] = int(elem.attrib.get('bands', 0))
				dump = elem.text
				histogram=[]
				if dump:
					for i in range(0,len(dump),2):
						histogram.append(int(dump[i:i+2], 16))
				else:
					warnings.append('No histogram dump for {}.'.format(
						data.get('id')))
				data['histogram'] = histogram
			# image tag closed:
			if elem.tag == 'image':
				# instantiate a picture
				imgs.append(data)
				if known.get(data['id']):
					print 'double: {} !'.format(data['id'])
				known[data['id']]=True
				data={}
			# url tag closed
			if elem.tag == 'url':
				if elem.text:
					data['url'] = elem.text
				else:
					warnings.append('error: couldnt read URL in {} record! (closing tag)'.format(data.get('id')))
			# similar img closing tag
			if elem.tag == 'img':
				if elem.text:
					try:
						data['similar'][elem.text] = float(elem.attrib.get('m',0))
					except:
						data['similar']={elem.text:elem.attrib.get('m',0)}
				else:
					warnings.append('W: unreadable img element @ {} similarity record'.format(
						data.get('id')))
			# source blogs
			if elem.tag == 'at':
				#TODO: date of retrieval
				if elem.text:
					try:
						data.get('hosts').append(elem.text)
					except:
						data['hosts'] = [elem.text]
				else:
					warnings.append('W: unreadable blog ref at sources sec of {} record'.format(
						data.get('id')))
	if len(warnings)>0:
		print '{} warnings.'.format(len(warnings))
	log_msgs.extend(warnings)
	print 'Read {} images into memory.'.format(len(imgs))
	return imgs



##############################################################
##############################################################
##############################################################
##############################################################
##############################################################
##############################################################
##############################################################


# saves a list of images to an XML file
def saveBlogs(blogs, filename):
	print 'saving blogs.',
	f=open(filename, 'w')
	f.write('<?xml version="1.0" standalone="yes"?>\n')
	f.write('<blogs num="{}">\n'.format(len(blogs)))
	for p in blogs:
		#attr=p.name.split('_')
		#extf = attr[-1].split('.')
		f.write(' <blog name="{}" seen="{}" score="{}">\n'.format(
						p.name, p.seen, p.score))
		f.write('  <images total="{}" local="{}">\n'.format(
			len(p.images), len(p.proper_imgs)))
		# existing files
		for i in p.images:
			if i:
				if i.name:
					f.write('   <img when="{}">{}</img>\n'.format(
						p.images_times.get(i,0),i.name))
				else:
					f.write('   <img when="{}">{}</img>\n'.format(0,i))
		f.write('  </images>\n')
		# links incoming and outgoing
		f.write('  <links>\n')
		for s in p.links:
			f.write('   <out>{}</out>\n'.format(s.name))
		for s in p.linked:
			f.write('   <in>{}</in>\n'.format(s.name))
		f.write('  </links>\n')
		f.write(' </blog>\n')
	f.write('</blogs>\n')
	f.close()
	print 'ok.'

# loads image container records from XML file
def loadBlogs(filename):
	if not os.path.exists(filename):
		print filename, "not found."
		return []
	print 'Reading blog metadata from', filename
	records=[]
	data={}
	warnings=[]
	for event, elem in ET.iterparse(filename, events=('start','end')):
		# ON OPENING TAGS:
		if event == 'start':
			if elem.tag == 'blog':
				data=elem.attrib
			# read image list
			if elem.tag == 'images':
				data['images'] = []
			# ream link lists
			if elem.tag == 'links':
				data['in'] = []
				data['out'] = []
		# CLOSING TAGS:
		else:
			# closing blog
			if elem.tag == 'blog':
				records.append(data)
				data = {}
			# closing img
			if elem.tag == 'img':
				#TODO: date of retrieval
				if elem.text:
					try:
						data.get('images').append(elem.text)
					except:
						data['images']=[elem.text]
				else:
					warnings.append('W: empty img element in {} record'.format(
						data.get('name')))
			# links
			if elem.tag in ['out', 'in']:
				try:
					data.get(elem.tag).append(elem.text)
				except:
					data[elem.tag] = [elem.text]
	if len(warnings)>0:
		print '{} warnings.'.format(len(warnings))
	log_msgs.extend(warnings)
	print 'Read {} blog objects.'.format(len(records))
	return records



##############################################################
##############################################################
##############################################################
##############################################################
##############################################################
##############################################################
##############################################################

# goes to the internets and gets an image. returns PIL Image
def open_img_url(url):
	image = None
	try:
		sck = urlopen(url)
		image = pil.open(BytesIO(sck.read()))
	except Exception, e:
		print e.message
		print 'Could not retrieve {}. '.format(url)
	return image


# craft html page for sequence of images
def export_html(imgs, filename):
	f=open(os.sep.join(['html', filename]), 'w')
	f.write('<html>\n<body>')
	maxh=500
	if None in imgs:
		maxh = 200
	for p in imgs:
		if p:
			height = min(maxh, p.size[1])
			f.write('    <img src="../{}" height="{}"/>\n'.format(
				p.location, height))
		else:
			f.write('<br/><hr/><br/>\n')
			maxh = 500
	f.write('</body>\n</html>\n')
	f.close()



# craft html page for groups of images
def savegroups(groups, filename):
	f=open(os.sep.join(['html', filename]), 'w')
	f.write('<html>\n<body>')
	for group in groups[:50]:
		f.write(' <div>\n')
		f.write('  <h3>{} Members</h3/>\n'.format(len(group)))
		p = group.pop(0)
		height = min(500, p.size[1])
		f.write('  <table height="{}">\n'.format(height))
		f.write('   <tr><td rowspan="2">\n')
		f.write('    <img src="../{}" height="{}"/>\n'.format(
			p.location, height))
		f.write('   </td>\n')
		thmbsize=min(height/2, 300)
		rowheight=thmbsize+10
		for i,s in enumerate(group):
			f.write('     <td height="{}" valign="top">\n'.format(rowheight))
			f.write('      <img src="../{}" height="{}"><br/>\n'.format(s.location, thmbsize))
			if (s.origin):
				f.write('      {}\n'.format(s.origin.name))
			f.write('     </td>\n')
			if i+1==len(group)/2:
				f.write('    </tr><tr>\n')
				rowheight=p.size[1]-rowheight
		f.write('   </tr>\n  </table>\n')
		f.write(' </div>\n')
	f.write('</body>\n</html>\n')
	f.close()

# graphviz
def dot_render(blogs, filename):
	try:
		import pygraphviz as dot
	except ImportError:
		print 'PyGraphviz not installed.'
		return
	graph = dot.AGraph(directed=True, overlap=False, splines=True, sep=.1)
	#for i,t in enumerate(blogs):
		#size = min(.01+t._score/20,.9)
		#graph.add_node('n{}'.format(i), label=t.name, color='black', 
			#width=size, 
			#height=size, 
			#fontsize=11)
	# outgoing:
	#for t in blogs:
		#for l in [l for l in t.links if l in blogs]:
			#graph.add_edge(t.name,l.name, color='blue', 
				#len=.5+min(len(t.links)/50,2.))
	# incoming:
	for t in blogs:
		ti = 'n{}'.format(blogs.index(t))
		for l in [l for l in t.linked if l in blogs]:
			li = 'n{}'.format(blogs.index(l))
			graph.add_edge(l.name,t.name, color='grey',
				weight=.01+l._score**2,
				len=.01+len(l.links)/100.,
				label='{:.2f}'.format(l._score/(1+len(l.links))))
	graph.layout()
	graph.draw(filename)


# graphviz for link paths
def dot_render_paths(down, up, filename):
	try:
		import pygraphviz as dot
	except ImportError:
		print 'PyGraphviz not installed.'
		return
	graph = dot.AGraph(directed=True, overlap=False, splines=True, sep=.1)
	for dir, col in [(down,'blue'), (up,'green')]:
		for path in [p[:] for p in dir if len(p)>0]:
			l = path.pop()
			while len(path)>0:
				t = path.pop()
				graph.add_edge(l.name, t.name, color=col,
					weight=.01+l._score**2/(1+len(l.links)/200.),
					len=.01+len(l.links)/100.)
				l = t
	graph.layout()
	graph.draw(filename)
