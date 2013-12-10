#!/usr/bin/python
# -*- coding: utf-8 -*- 
import Tkinter as tk
from tkFont import Font, families
from PIL import Image, ImageTk
from time import time
from math import sqrt as sqr
from random import choice, randrange as rnd
import os

import index
import weave.picture as picture
import weave.tumblr as tumblr
import util

# font registry for repeated use
fonts = {}

class Browser:
	BROWSE='browse'
	SINGLE='single'
	DETAIL='detail'
	BLOG='blog'
	POPULAR='pop'
	def __init__(self, root):
		self.cur_imgs = [] # backup references against garbage coll.
		self.img_reg = {} # registry to avoid disk access
		self.thmb_reg = {} # thumbnail registry to avoid resize
		self.preview_reg = {} # preview registry to avoid resize
		self.mode = Browser.BROWSE
		self.redraw = False # set true to redraw gui
		self.changes = False # changes to be saved?
		self.new_votes = set() # keep track of new ratings
		self.pool=[]
		# TODO: selection: GUI indicator must be present for selection state,
		# selection must be viewable in its entirety in dedicated view mode,
		# selection should probably be of type set.
		self.selection=[] # selection for exports or queries
		# compare new pictures with favorites
		favs = picture.starred()[:10]
		newsies = [p for p in picture.pictures() if p.reviewed < 1]
		if len(newsies)>0 and len(favs)>0:
			print 'calculating similarities between {} new images and highest rated'.format(
				len(newsies))
			self.new_votes = set(favs)
			for n in newsies:
				for p in favs:
					sim = p.similarity(n)
					if sim > .5:
						picture.connect(n, p, sim)
		# img clusters
		self.clusters=[]
		# init img tracking
		self.repool()
		#pics = sorted(pics, key=lambda p:p.rating)
		# repopulate history
		self.hist = []
		for p in picture.last_reviewed()[:50]:
			if util.days_since(p.reviewed)<1.5:
				self.hist.append(p)
				if p in self.pool:
					self.pool.remove(p)
		# choose image to displ
		if len(self.hist)<1 and len(self.pool)>0:
			self.choose(self.pool.pop()) # current image as Pict object
			self.hist = [self.img] # history of recent images
		elif len(self.hist)>0:
			self.img = self.hist[0]
		# self.trash
		# key: pict instance, value: (path, image)
		self.trash = {}
		# canvas
		self.cnv = tk.Canvas(root, bg="black")
		self.cnv.pack(side='top', fill='both', expand='yes')
		# put a button on the image panel to test it
		#self.button = tk.Button(self.cnv, text='button2')
		#self.button.pack(side='top')
		self.display()


	# init default image selection from favorites and newsies
	def repool(self):
		pics = picture.to_review()
		if len(pics)<3:
			pics.extend(picture.favorites()[:50])
		self.pool.extend(pics)
		return pics


	# make collection to choose from given current image
	def get_choices(self):
		# print time(), 'enter get_choices'
		# suggest pictures with similiarity link to current
		if not self.mode in [Browser.BLOG,Browser.POPULAR]:
			choices = dict(self.img.relates)
		else:
			choices = {}
		# prefer pictures in pool,
		# prefer newest pictures
		for p in self.pool:
			boost = min(1,util.days_since(p.reviewed)/99)
			boost *= 1./(1+util.days_since(p.date)/5)
			choices[p] = choices.get(p, 0)+boost
		# not enough candidates? fill up with favies!
		# TODO: need we?
		#if len(choices)<10:
			#favies=picture.favorites()
			#for i in range(10-len(choices)):
				#p = favies.pop(0)
				#choices[p] = p.relates.get(self.img,0)
		# calculate scores
		for p, sim in choices.items():
			score = (1+p.rating/6./10.) * sim
			for vote in self.new_votes:
				adv = p.relates.get(vote)
				if not adv:
					adv = vote.relates.get(p,0)
				score += vote.rating * (.1+adv/len(self.new_votes)/6./10.)
			choices[p] = score
		# return candidates ordered by highest score desc.
		choices = sorted(choices.items(), key=lambda t:t[1])
		# print time(), 'return get_choices'
		return [t[0] for t in choices[::-1]]


	# set pict as currently viewed 
	def choose(self, pict):
		self.img = pict
		pict.reviewed = time()
		self.changes = True


	# free some memory by deleting old imgs from registries
	def free_mem(self):
		for p in self.hist[10:]:
			if self.img_reg.get(p):
				del self.img_reg[p]
			if self.preview_reg.get(p):
				del self.preview_reg[p]
			if self.thmb_reg.get(p):
				del self.thmb_reg[p]
			else:
				return

################################################################
################################################################
##########                                           ###########
##########           gui render stuff                ###########
##########                                           ###########
################################################################
################################################################


	# takes a Pict instance and returns a scaled (if size=(x,y) given)
	# ImageTk.PhotoImage object.
	def load_img(self, pict, size=None):
		w,h = pict.size
		if size:
			img = self.preview_reg.get(pict)
			if not img:
				im = self.img_reg.get(pict)
				if not im:
					im = pict.load()
					self.img_reg[pict] = im
				mw,mh = size
				ratio = min([float(mw)/w, float(mh)/h])
				im = im.resize((int(w*ratio),int(h*ratio)), Image.ANTIALIAS)
				img = ImageTk.PhotoImage(im)
				del im
				self.preview_reg[pict] = img
		else:
			im = self.img_reg.get(pict)
			if not im:
				im = pict.load()
				self.img_reg[pict] = im
			img = ImageTk.PhotoImage(im)
			del im
		return img


	# retrieve thumbnail for Pict object
	def load_thmb(self, pict):
		thmb = self.thmb_reg.get(pict)
		if not thmb:
			im = self.img_reg.get(pict)
			if not im:
				im = pict.load()
			w,h = pict.size
			ratio = min([140./w, 140./h])
			img = im.resize((int(w*ratio),int(h*ratio)), Image.LINEAR)
			del im
			thmb = ImageTk.PhotoImage(img)
			del img
			self.thmb_reg[pict] = thmb
		return thmb


	# assemble displayal of main viewing mode
	def display(self):
		# print time(), 'enter display'
		ids = self.cnv.find_all()
		for i in ids:
			self.cnv.delete(i)
		# print time(), 'deleted prev canvas items'
		self.cur_imgs = [] # keep ref for objects (garbage coll)
		self.cnv.create_rectangle((0,0,1024,740), fill='black')
		# history
		y = 0
		imgs=[]
		cover=0
		for p in self.hist[1:15]:
			img = self.load_thmb(p)
			self.cnv.create_image((0,y), 
				anchor=tk.NW, image=img)
			#self.cnv.create_text(0+4, y+4, anchor=tk.NW, 
				#font='Arial 12 bold', fill='white', text='*'*p.rating)
			self.mini_desc((img.width()+4, y+4),p)
			if p == self.img:
				self.cnv.create_rectangle((3,y+3,img.width()-3,y+img.height()-3),
					outline='yellow', width='3')
			if self.trash.get(p):
				self.cnv.create_text(img.width()-4, y+4, anchor=tk.NE, 
						font='Arial 14 bold', fill='red', text='X')
			if p in self.selection:
				self.cnv.create_text(img.width()-4, y+4, anchor=tk.NE, 
						font='Arial 10 bold', fill='green', text='[In Selection]')
			y += img.height()
			#imgs.append((img, (0,y), p.rating))
			self.cur_imgs.append(img)
			#cover = min(80, cover+4)
		#for img, pos, stars in imgs[::-1]:
			#self.cnv.create_rectangle((pos[0], pos[1],
				#pos[0]+img.width(), pos[1]+img.height()), fill='black')
		# current img
		# print time(), 'load curr img preview'
		img = self.load_img(self.img, size=(720, 740))
		self.cur_imgs.append(img)
		# print time(), 'place curr img preview'
		self.cnv.create_image((500,370), anchor=tk.CENTER, image=img) 
		# print time(), 'place curr img decoration'
		self.mini_desc((504-img.width()/2,374-img.height()/2),self.img)
		if self.trash.get(self.img):
			self.cnv.create_text(500, 374-img.height()/2, anchor=tk.CENTER, 
					font='Arial 14 bold', fill='red', 
					text='In Trash. Hit <Del> to Restore.')
		if self.img in self.selection:
			self.cnv.create_text(500, 392-img.height()/2, anchor=tk.CENTER, 
					font='Arial 12 bold', fill='green', 
					text='[In Selection. Hit <space> to deselect]')
		# topleft= NW
		# similars
		posx = min([max([500+self.img.size[0]/2, 724]),784])
		self.choices = []
		i = 0 # counter
		x,y = posx,0 # curr. thmbnail pos.
		# retrieve
		#sims = self.img.most_similar()
		sims = self.get_choices()
		# print time(), 'assemble img suggestions'
		while y<740 and len(sims)>0:
			s = sims.pop(0)
			if s.path and not s in self.hist:
				img = self.load_thmb(s)
				#self.cnv.create_rectangle((1024-img.width(),y,1024,y+img.height()),
					#fill='black')
				self.cnv.create_image((1024,y), 
					anchor=tk.NE, image=img)
				#self.cnv.create_text(1028-img.width(), y+4, anchor=tk.NW, 
					#font='Arial 14 bold', fill='white', text='*'*s.rating)
				# write little info caption
				self.mini_desc((1020-img.width(),y+4),s,justify='right')
				#self.cnv.create_text(1020-img.width(), y+4, anchor=tk.NE, 
					#font='Arial 9', justify='right', fill='white', 
					#text='\n'.join(notes))
				y += img.height()
				self.cur_imgs.append(img)
				self.choices.append(s)
		# print time(), 'return from display'



	# single image view
	def display_single(self):
		w,h=self.img.size
		#if w>760 or h>740:
		img = self.load_img(self.img)
		self.cnv.create_image((500,370), anchor=tk.CENTER, image=img)
		self.text('[{}] [{}]'.format(
			'S'*int(self.img in self.selection),
			'X'*int(self.trash.get(self.img) != None)), (4,4))
		imgtxt=self.img.details()
		x,y = self.text(imgtxt, (4,24))
		medians = map(lambda b:b*8, self.img.histogram.mediane)
		if len(medians)<3:
			medians *= 3
		med_col = '#{}'.format(''.join([('%02x' % b) for b in medians]))
		self.cnv.create_rectangle((10,y+20,100,y+84),
			outline='#fff',
			fill=med_col)
		self.text('Color code {}'.format(med_col), (0,y+90))
		if self.img.origin:
			blogtxt = self.img.origin.details()
			self.text(blogtxt, (0,y+130))
		self.text('Source: {}'.format(self.img.url), (0,724))
		self.cur_imgs = [img]


	# text output
	def text(self, output, pos, anchor=tk.NW, justify='left',
		font='Arial', size=12, decoration='', shadow=True, split=False):
		# http://infohost.nmt.edu/tcc/help/pubs/tkinter/web/create_text.html
		# http://infohost.nmt.edu/tcc/help/pubs/tkinter/web/fonts.html
		#size = util.grep('[1-9]?[0-9]{1,2}', font, n=0)
		# choose font
		fid='{} {} {}'.format(font, size, decoration)
		f = fonts.get(fid)
		if not f:
			w = ['normal', 'bold'][decoration.count('bold')>0]
			s = ['roman', 'italic'][decoration.count('italic')>0]
			u = int(decoration.count('underline')>0)
			f = Font(family=font, size=-size, weight=w,
				slant=s, underline=u)
			fonts[fid]=f
		# start aligning output
		x, y = pos
		for xx,yy in [(0,1),(1,0),(0,-1),(-1,0),(1,1),(2,0)]:
			self.cnv.create_text(x+xx, y+yy, anchor=anchor, 
				font=f, 
				justify=justify,
				fill='black',
				text=output)
		self.cnv.create_text(x, y, anchor=anchor, 
			font=f, 
			justify=justify,
			fill='white',
			text=output)
		return x+f.measure(output), y+len(output.split('\n'))*size


	# places a short informative text about e.g. a thumbnail
	# returns bounding box of written text or whatever
	def mini_desc(self, pos, p, justify='left'):
		a=tk.NW
		if justify=='right':
			a=tk.NE
		desc = p.short_desc()
		sim = self.img.relates.get(p)
		if sim:
			desc = '\n'.join(['{:.1f}%'.format(sim*100),desc])
		return self.text(desc, pos, anchor=a, 
			justify=justify, font='Arial', size=10)


	# places a warning sign
	def message(self, text, confirm=False):
		w = 400.
		h = w/((sqr(5)+1)/2) # goldener schnitt, yay!
		x = 1024/2-w/2
		y = 780/((sqr(5)+1)/2)-h/((sqr(5)+1)/2)
		self.cnv.create_rectangle((x,y,x+w,y+h),
			fill='black', outline='red', width='5')
		self.text(text, (x+10,y+10), font='Liberation Serif', 
			anchor=tk.NW)
		if confirm:
			self.mode = 'message'
			self.text('Hit any key to continue', 
				(x+w-10,y+h-20), font='Liberation Serif', 
				anchor=tk.NE)
		self.cnv.update_idletasks()




################################################################
################################################################
##########                                           ###########
##########             functionality                 ###########
##########                                           ###########
################################################################
################################################################


	def forward(self, ix):
		if ix < len(self.choices):
			# truncate history if we went back before
			if self.img in self.hist:
				i = self.hist.index(self.img)
				self.hist = self.hist[i:]
			#else:
				# save in history
				# self.hist.insert(0,self.img)
			# forward and paint
			self.choose(self.choices[ix])
			self.hist.insert(0,self.img)
			print 'imgs in history:', len(self.hist)
		else:
			self.pool.extend(picture.favorites()[:50])
		self.redraw=True


	def back(self, key):
		if self.img in self.hist:
			i = self.hist.index(self.img)
			if i < min([len(self.hist)-1, 7]):
				self.choose(self.hist[i+1])
		else:
			self.choose(self.hist[0])
		self.display()

	# redo one step in history.
	# if not in history, move forward
	def replay(self, key):
		if self.img in self.hist:
			i = self.hist.index(self.img)
			if i > 0:
				self.choose(self.hist[i-1])
				self.redraw=True
			else:
				self.forward(0)
		else:
			self.forward(0)



	def zoom(self, key):
		# determine whether to change state
		if self.mode in [Browser.BROWSE, Browser.BLOG, Browser.POPULAR]:
			self.cnv.create_rectangle((0,0,1024,740), fill='black')
			self.display_single()
			self.mode = Browser.SINGLE
		elif self.mode == Browser.SINGLE:
			self.cnv.create_rectangle((0,0,780,740), fill='black')
			self.cnv.create_rectangle((0,724,780,740), fill='black')
			if key in [9,36]:
				self.display()
				self.mode = Browser.BROWSE
			else:
				self.display_single()


	# re-generate GUI contents based on mode and action
	def update(self, key):
		# print time(), 'enter update'
		self.redraw=False
		#if self.mode != 'message':
		if self.mode in [Browser.BROWSE, Browser.BLOG, Browser.POPULAR,
			'cluster']:
			self.display()
		elif self.mode == Browser.SINGLE:
			self.zoom(key)
		self.free_mem()
		# print time(), 'return update'


	def page_up(self, key):
		if key in [81,112]:
			if self.img.rating < 6:
				self.img.rating += 1
				self.changes = True
				self.new_votes.add(self.img)
				if len(self.img.relates)<1:
					for p in picture.starred():
						if not p == self.img:
							sim = self.img.similarity(p)
							if sim > .5:
								picture.connect(self.img,p,sim)
				self.redraw=True


	def page_down(self, key):
		if key in [89,117]:
			if self.img.rating > 0:
				self.img.rating = self.img.rating-1
				self.new_votes.add(self.img)
				self.changes = True
				self.redraw=True

	# suggest only images from same blog as current
	def blog_mode(self, key):
		if self.mode == Browser.BLOG:
			self.mode = Browser.BROWSE
			self.repool()
			self.redraw=True
		else:
			if self.img.origin:
				self.pool = self.img.origin.proper_imgs
				self.mode = Browser.BLOG
				self.redraw=True

	# suggest only images with more than zero stars
	def pop_mode(self, key):
		if self.mode == Browser.POPULAR:
			self.mode = Browser.BROWSE
			self.repool()
			self.redraw=True
		else:
			self.pool = [p for p in picture.favorites() 
				if not p in self.hist and p.rating>0]
			self.pool = sorted(self.pool, key=lambda p:p.rating, reverse=True)[:50]
			self.mode = Browser.POPULAR
			self.redraw=True

	# empty trash. delete image files, change image object to light instance
	def empty_trash(self, key):
		if len(self.trash)>0:
			self.message('Empty Trash ({} images)...'.format(len(self.trash)))
			print 'emptying Browser.trash: delete {} images'.format(len(self.trash))
			if self.trash.get(self.img):
				self.forward(0)
			for p, path in self.trash.items():
				# delete image from disk.
				index.picture.delete(p)
				if p in self.hist:
					self.hist.remove(p)
			self.trash = {}
			print 'Browser.trash empty'
			self.redraw=True
		else:
			print 'Nothing in Trash'


	# empty trash, save data to xml and f.o.
	def quit(self, key):
		self.empty_trash(key)
		if self.changes:
			print "saving changes..."
			self.message('Saving image/blog data to XML...')
			index.save()
		root.quit()


	# delete image/self.trash it
	def delete(self, key):
		self.trashed = self.trash.get(self.img)
		if self.trashed:
			path = self.trashed
			self.img.path = path
			#self.img.upgrade(img, self.img.url, save=True)
			del self.trash[self.img]
			self.redraw=True
		else:
			# save copy to self.trash
			self.trash[self.img] = self.img.path #, self.img.load())
			# redo history
			if self.img in self.hist:
				i = self.hist.index(self.img)
				self.hist = self.hist[i:]
				print 'imgs in history:', len(self.hist)
			self.replay(0)
			#self.mode = Browser.BROWSE
			self.redraw=True
			self.changes = True

	
	# select/deselect images for whatever, probably export
	def select(self, key):
		if self.img in self.selection:
			self.selection.remove(self.img)
		else:
			self.selection.append(self.img)
		self.redraw=True
	

	# compute similarities for current image
	def compute_sim(self, key):
		print 'compute similarities for', self.img
		self.message('Compute similarities:\n\n{}\nx{} imgs'.format(
			self.img,
			len(picture.pictures())))
		sims = {}
		for p in picture.pictures():
			if p != self.img:
				sim = self.img.similarity(p)
				sims[p] = sim
		minsim = min(sims.values())
		maxsim = max(sims.values())
		thresh = maxsim - (maxsim-minsim)/3.
		res = []
		for p,s in sims.items():
			if s > thresh:
				picture.connect(self.img, p, s)
				res.append(p)
					#x=0
					#for q in res[:10]:
						#img = self.load_thmb(q)
						#self.cnv.create_image((x,780), 
							#anchor=tk.SW, image=img)
						#self.cur_imgs.append(img)
						#x += img.width()
		print 'done. found {} images.'.format(len(res))
		self.redraw=True
		return res


	# compute scores of blogs using page rank
	def compute_scores(self, key):
		steps = 3
		print 'running page rank {} times. yay!'.format(steps)
		dur = time()
		# original score ranks
		hi_=sorted(index.blogs(), key=lambda t:t._score, reverse=True)
		# compute...
		for i in range(steps):
			self.message('\n'.join([
				'Computing blog scores using page rank:',
				'{} iteration step{}'.format(steps, 's'*int(steps>1)),
				'','This might take a while...','',
				'Step {}/{}'.format(i+1,steps)]))
			scores = index.scores(1, reset=False)
		scs = sorted(scores.items(), key=lambda t:t[1])
		self.redraw=True
		self.changes=True
		# display result on GUI
		hi=sorted(index.blogs(), key=lambda t:t._score, reverse=True)
		prom = lambda t: hi_.index(t) - hi.index(t)
		news = lambda t: ['','({}{})'.format('-+'[prom(t)>0], abs(prom(t)))][
			prom(t) != 0]
		n = 14
		prompt=[] #['Top {} blogs:'.format(n), '']
		for i,t in enumerate(hi[:n]):
			prompt.append('\t\t{}.  {} - {:.2f}  {}'.format(i+1, t.name, t._score,
				news(t)))
		prompt.extend(['', '(Processed {} blogs in {:.1f} seconds)'.format(
			len(index.blogs()), time()-dur)])
		self.message('\n'.join(prompt), confirm=True)


	# export selection to xml
	def export(self, key):
		if not os.path.exists('exports'):
			os.mkdir('exports')
		if len(self.selection) > 0:
			blgs = set()
			for p in self.selection:
				if len(p.sources) > 0:
					blgs.update(p.sources)
			self.message('exporting selection of {} images and {} blogs to xml.'.format(
				len(self.selection), len(blgs)))
			imgs = self.selection[:]
			# remove references not being exported
			for p in imgs:
				p.relates = {q:s for q,s in p.relates.items() if q in imgs}
				#FIXME: offline workaround: copy images instead of downloading them
				if not os.path.exists('exports/{}'.format(p.filename)):
					os.link('images/{}'.format(p.filename), 'exports/{}'.format(p.filename))
			util.inout.saveImages(imgs, 'exports/images.xml')
			util.inout.saveBlogs(list(blgs), 'exports/blogs.xml')
			self.redraw=True


	# import xml dumps located in /exports/
	def import_dump(self, key):
		if not os.path.exists('exports'):
			os.mkdir('exports')
		imgs=[]
		srcimgs=[]
		blgs=[]
		#TODO: find all xml files in folder
		if os.path.exists('exports/images.xml'):
			#TODO: download image from original location
			imgrec = util.inout.loadImages('exports/images.xml')
			srcimgs = [picture.opendump(rec) for rec in imgrec]
			# FIXME: workaround wegen offline: bilder werden komplett mitkopiert
			for p in srcimgs:
				if not os.path.exists('images/{}'.format(p.filename)):
					os.rename('exports/{}'.format(p.filename), 'images/{}'.format(p.filename))
					imgs.append(p)			
			# remove images xml records so that missing images cannot be imported again
			os.remove('exports/images.xml')
		if os.path.exists('exports/blogs.xml'):
			blgrec = util.inout.loadBlogs('exports/blogs.xml')
			blgs = [tumblr.opendump(rec) for rec in blgrec]
			# reify image references made by blogs
			for t in blgs:
				index.clean_img_refs(t)
			# remove xml file because import is successful
			os.remove('exports/blogs.xml')
		# now that we have our blogs imported, we can reify blog/img references 
		# in img instances
		# TODO: reification of source blogs, interblog references, interimg links!!
		for p in srcimgs:
			index.clean_sources(p)
			p.clean_links()
		self.message('imported {} images and {} blogs.'.format(
			len(srcimgs), len(blgs)))
 		# compute similarities with present images
 		self.message('compute similarities with present images..')
		bestsim=0 # sim stat
 		for p in imgs:
			sims = {}
			for q in picture.pictures():
				if q != p:
					sims[q] = p.similarity(q)
			minsim,maxsim = (min(sims.values()), max(sims.values()))
			p.relates.update({q:s for q,s in sims.items() 
				if s > maxsim-(maxsim-minsim)/3})
			# keep track of best match
			bestsim = max(bestsim, maxsim)
		# remove xml files (now left without their actual images...)
		# and repool
		if len(imgs)>0:
			self.pool = imgs
		self.redraw = True
 		self.message('\n'.join(['Imported {} image records with {} new images'.format(
			len(srcimgs), len(imgs)),
			'featured by {} blogs.'.format(len(blgs)),
			'Highest similarity between old and new image was {:.2f}'.format(bestsim)]),
			confirm=True)

		


	# generate path that connects all selected or upvoted? images and export it
	# to html
	def export_path_html(self, key):
		if len(self.selection)>0:
			explst = self.selection
			print 'export selection;', len(self.selection)
		else:
			explst = self.new_votes
			print 'export votes;', len(self.new_votes)
		query = [p for p in list(explst) if not p in self.trash]
		self.message('\n'.join([
			'Export assemblage of selected images. ({} imgs)'.format(
				len(query[:20])),
			'','This may take a while.']))
		# FIXME: this is limited to 20 images???
		path = index.chain(query=query[:20])
		index.export_html(path, 'selection.html')
		self.redraw=True


	# compute clusters
	def cluster_mode(self, key):
		if self.mode in [Browser.BROWSE, Browser.BLOG, Browser.POPULAR]:
			#if len(self.clusters)<1:
			self.message('Clustering...')
			self.clusters = index.clustering(picture.pictures(), 
				len(picture.pictures())-100)
			self.mode='cluster'
			for c in self.clusters:
				if self.img in c:
					self.pool = c
			self.redraw=True
		else:
			self.mode = Browser.BROWSE
			self.repool()
			self.redraw=True


	# go to the interweb!
	def crawl(self, key):
		seed = None
		score = ''
		if self.img.origin:
			seed = self.img.origin.url()
			score = '({:.2f})'.format(self.img.origin._score)
		msg = []
		imgs = []
		pool = []
		dur = time()
		# crawl 3 blogs
		for i in range(3):
			msg += [index.get_crawler().message()]
			self.message('\n'.join(['Wait for crawler...','',
				'Seed URL: {} {}'.format(seed, score),''] + msg + 
				['','{}/3'.format(i),
				'{} images (+{})'.format(len(pool), len(imgs)),
				'time: {:.1f}'.format(time()-dur)]))
			imgs = index.crawl(seed, num=1)
			pool.extend(imgs)
		self.pool.extend(pool)
		# done. prompt status. redraw?
		# redraw GUI -> show new imgs
		self.display()
		# prompt status
		dur = time()-dur
		msg += [index.get_crawler().message()]
		crl = index.get_crawler()
		self.message('\n'.join(['Done.',
			'Crawler returned {} new images in {:.1f} seconds'.format(
				len(pool), dur),
			'({:.2f} img/sec avg.).'.format(len(pool)/dur),
			'']+
			msg+['', 'Crawler status:', 
			' {} visited,'.format(len(crl.visited)),
			' {} in queue.'.format(len(crl.frontier))]), 
			confirm=True)
		self.redraw = True

	# just pick random image
	def rnd_img(self, key):
		p = choice([p for p in index.pictures() 
			if not p in self.hist and not p == self.img])
		self.choose(p)
		self.hist.insert(0,self.img)
		self.redraw = True


	# show palette
	def palette(self, key):
		img = self.img.show_pal()
		img.show()
		self.message("displaying image most significant colors..", confirm=True)
		del img
	



handlers={113:Browser.back, # lkey
					114:Browser.replay, # rkey
					36:Browser.zoom, # enter
					81:Browser.page_up, # page up
					112:Browser.page_up, # pg up
					89:Browser.page_down, # pg down
					117:Browser.page_down,
					65:Browser.select, # space
					9:Browser.quit, # esc
					22:Browser.delete, # del, backsp
					119:Browser.delete,
					39:Browser.compute_sim, # s
					38:Browser.export_path_html, # a
					40:Browser.compute_scores, # d
					54:Browser.cluster_mode, # c
					53:Browser.export, # x
					56:Browser.blog_mode, # b
					25:Browser.crawl, # w
					26:Browser.empty_trash, # e
					27:Browser.rnd_img, # r
					31:Browser.import_dump, # i
					32:Browser.pop_mode, # o
					33:Browser.palette # p
					}

def key(event):
	print time(), "pressed", event.keycode
	# message prompt to be confirmed?
	if browser.mode == 'message':
		browser.mode = Browser.BROWSE
		browser.update(0)
	else:
		# no message, do as expected:
		# number key choice?
		if event.keycode in range(10,20):
			browser.forward(event.keycode-10)
		# keys we know functions for?
	  # handlers implemented by browser
		f = handlers.get(event.keycode)
		if f:
			f(browser, event.keycode)
		if browser.redraw:
			browser.update(event.keycode)
	# print time(), 'leave keyhandler'

   #if len(browser.img.relates.keys()) > 0:
		#browser.img = browser.img.relates.keys()[0]
   #print browser.img.location



# Ok Go
index.load(recover=True)

# create tkinter window
root = tk.Tk()
root.title('tumblr img browser')
# make the root window the size of the image
root.geometry("%dx%d+%d+%d" % (1024, 740, 0, 0))
root.bind("<Key>", key)
# instantiate browser class
browser = Browser(root)

# screen size:
w = root.winfo_screenwidth()
h = root.winfo_screenheight() 
print 'screen size {}x{}'.format(w,h)
# start the event loop
root.mainloop()

#for f in families():
	#print f
