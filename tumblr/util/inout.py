#!/usr/bin/python
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from urllib2 import urlopen, Request
from PIL import Image as pil
from io import BytesIO


# saves a list of images to an XML file
def saveImages(images, filename):
	f=open(filename, 'w')
	f.write('<?xml version="1.0" standalone="yes"?>\n')
	f.write('<images num="{}">\n'.format(len(images)))
	for p in images:
		#attr=p.name.split('_')
		#extf = attr[-1].split('.')
		f.write(' <image id="{}" extension="{}" mode="{}" format="{}">\n'.format(
						p.name, p.ext, p.mode, p.dim))
		attr=p.size
		f.write('  <size width="{}" height="{}"/>\n'.format(attr[0], attr[1]))
		f.write('  <location>{}</location>\n'.format(p.location))
		histo = p.histogram
		f.write('  <histogram bands="{}">{}</histogram>\n'.format(
						histo.bands, histo.hex()))
		f.write('  <hosted times="{}">\n'.format(len(p.sources)))
		for s in p.sources:
			f.write('   <at when="{}">{}</at>\n'.format(0,s.name))
		f.write('  </hosted>\n')
		f.write('  <similar num="{}">\n'.format(len(p.relates)))
		for s in p.relates.items():
			f.write('   <img m="{:1.3}">{}</img>\n'.format(s[1],s[0].name))
		f.write('  </similar>\n')
		f.write(' </image>\n')
	f.write('</images>\n')
	f.close()

##############################################################
##############################################################
##############################################################

# loads image container records from XML file
def loadImages(filename):
	print 'Reading images metadata from ', filename
	imgs=[]
	data={}
	known={}
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
			if elem.tag == 'hosted':
				data['hosts']=[]
			if elem.tag == 'at':
				try:
					data.get('hosts').append(elem.text)
				except:
					data['hosts'] = [elem.text]
			if elem.tag == 'similar':
				data['similar']={}
			if elem.tag == 'img':
				try:
					data['similar'][elem.text] = float(elem.attrib.get('m',0))
				except:
					data['similar']={elem.text:elem.attrib.get('m',0)}
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
					print 'No histogram dump:', data.get('id')
				data['histogram'] = histogram
			# image tag closed:
			if elem.tag == 'image':
				# instantiate a picture
				imgs.append(data)
				if known.get(data['id']):
					print 'double: {} !'.format(data['id'])
				known[data['id']]=True
				data={}
	return imgs



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



# craft html page for groups of images
def savegroups(groups, filename):
	f=open(os.sep.join(['html', filename]), 'w')
	f.write('<html>\n<body>')
	for group in groups[:50]:
		f.write(' <div>\n')
		f.write('  <h3>{} Members</h3/>\n'.format(len(group)))
		p=group.pop(0)
		height=min(600, p.size[1])
		f.write('  <table height="{}">\n'.format(height))
		f.write('   <tr><td rowspan="2">\n')
		f.write('    <img src="../{}"/><br/>\n'.format(p.location))
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


##############################################################
##############################################################
##############################################################
##############################################################
##############################################################
##############################################################
##############################################################


# saves a list of images to an XML file
def saveBlogs(blogs, filename):
	f=open(filename, 'w')
	f.write('<?xml version="1.0" standalone="yes"?>\n')
	f.write('<blogs num="{}">\n'.format(len(blogs)))
	for p in blogs:
		#attr=p.name.split('_')
		#extf = attr[-1].split('.')
		f.write(' <blog name="{}" seen="{}">\n'.format(
						p.name, p.seen))
		f.write('  <images>\n')
		# existing files
		for i in p.proper_imgs:
			f.write('   <img when="{}">{}</img>\n'.format(0,i.name))
		# removed images
		for i in p.dead_imgs:
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

# loads image container records from XML file
def loadBlogs(filename):
	print 'Reading blog metadata from ', filename
	records=[]
	data={}
	for event, elem in ET.iterparse(filename, events=('start','end')):
		# ON OPENING TAGS:
		if event == 'start':
			if elem.tag == 'blog':
				data=elem.attrib
			# read image list
			if elem.tag == 'images':
				data['images']=[]
			if elem.tag == 'img':
				try:
					data.get('images').append(elem.text)
				except:
					data['images']=[elem.text]
			# ream link lists
			if elem.tag == 'links':
				data['in'] = []
				data['out'] = []
			if elem.tag in ['out', 'in']:
				try:
					data.get(elem.tag).append(elem.text)
				except:
					data[elem.tag] = [elem.text]
		# CLOSING TAGS:
		else:
			if elem.tag == 'blog':
				records.append(data)
				data = {}
	return records