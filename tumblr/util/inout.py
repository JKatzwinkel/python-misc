#!/usr/bin/python
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from urllib2 import urlopen, Request
from PIL import Image as pil
from io import BytesIO



def saveXML(images, filename):
	f=open(filename, 'w')
	f.write('<?xml version="1.0" standalone="yes"?>\n<images>\n')
	for p in images:
		#attr=p.name.split('_')
		#extf = attr[-1].split('.')
		f.write(' <image id="{}" extension="{}" format="{}">\n'.format(
						p.name, p.ext, p.dim))
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

def loadXML(filename):
	imgs=[]
	data={}
	known={}
	for event, elem in ET.iterparse(filename, events=('start','end')):
		if event == 'start':
			if elem.tag == 'image':
				data=elem.attrib
			if elem.tag == 'size':
				data['size'] = (int(elem.attrib.get('width',0)), 
												int(elem.attrib.get('height',0)))
			if elem.tag == 'location':
				data['location'] = elem.text

			if elem.tag == 'hosted':
				#data['num_hosts'] = elem.attrib.get('times',0)
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
		else:
			if elem.tag == 'histogram':
				data['histogram_bands'] = elem.attrib.get('bands', 0)
				dump = elem.text
				histogram=[]
				if dump:
					for i in range(0,len(dump),2):
						histogram.append(int(dump[i:i+2], 16))
				else:
					print 'No histogram dump:', data.get('id')
				data['histogram'] = histogram
			if elem.tag == 'image':
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

