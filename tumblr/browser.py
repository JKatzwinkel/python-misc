# -*- coding: utf-8 -*- 
import Tkinter as tk
from tkFont import Font, families
from PIL import Image, ImageTk
from time import time

import index
import weave.picture as picture
import weave.tumblr as tumblr
import util

# key: pict instance, value: (path, image)
trash = {}
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
		# init img tracking
		self.repool()
		#pics = sorted(pics, key=lambda p:p.rating)
		# repopulate history
		self.hist = []
		for p in picture.last_reviewed()[:30]:
			if util.days_since(p.reviewed)<.125:
				self.hist.append(p)
				if p in self.pool:
					self.pool.remove(p)
		# choose image to displ
		if len(self.hist)<1:
			self.choose(self.pool.pop()) # current image as Pict object
			self.hist = [self.img] # history of recent images
		else:
			self.img = self.hist[0]
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
		print time(), 'enter get_choices'
		# suggest pictures with similiarity link to current
		if self.mode != Browser.BLOG:
			choices = dict(self.img.relates)
		else:
			choices = {}
		# prefer pictures in pool,
		# prefer newest pictures
		for p in self.pool:
			boost = min(1.8,util.days_since(p.reviewed)/99)
			boost += 1.5/(1+util.days_since(p.date))
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
			score = (1+p.rating/5) * sim
			for vote in self.new_votes:
				adv = p.relates.get(vote)
				if not adv:
					adv = vote.relates.get(p,0)
				score += vote.rating*adv/len(self.new_votes)
			choices[p] = score
		# return candidates ordered by highest score desc.
		choices = sorted(choices.items(), key=lambda t:t[1])
		print time(), 'return get_choices'
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
		print time(), 'enter display'
		ids = self.cnv.find_all()
		for i in ids:
			self.cnv.delete(i)
		print time(), 'deleted prev canvas items'
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
			if trash.get(p):
				self.cnv.create_text(img.width()-4, y+4, anchor=tk.NE, 
						font='Arial 14 bold', fill='red', text='X')
			y += img.height()
			#imgs.append((img, (0,y), p.rating))
			self.cur_imgs.append(img)
			#cover = min(80, cover+4)
		#for img, pos, stars in imgs[::-1]:
			#self.cnv.create_rectangle((pos[0], pos[1],
				#pos[0]+img.width(), pos[1]+img.height()), fill='black')
		# current img
		print time(), 'load curr img preview'
		img = self.load_img(self.img, size=(720, 740))
		self.cur_imgs.append(img)
		print time(), 'place curr img preview'
		self.cnv.create_image((500,370), anchor=tk.CENTER, image=img) 
		print time(), 'place curr img decoration'
		self.mini_desc((504-img.width()/2,374-img.height()/2),self.img)
		if trash.get(self.img):
			self.cnv.create_text(500, 374-img.height()/2, anchor=tk.CENTER, 
					font='Arial 14 bold', fill='red', 
					text='In Trash. Hit <Del> to Restore.')
		# topleft= NW
		# similars
		posx = min([max([500+self.img.size[0]/2, 724]),784])
		self.choices = []
		i = 0 # counter
		x,y = posx,0 # curr. thmbnail pos.
		# retrieve
		#sims = self.img.most_similar()
		sims = self.get_choices()
		print time(), 'assemble img suggestions'
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
		print time(), 'return from display'



	# single image view
	def display_single(self):
		w,h=self.img.size
		#if w>760 or h>740:
		img = self.load_img(self.img)
		self.cnv.create_image((500,370), anchor=tk.CENTER, image=img)
		imgtxt=self.img.details()
		x,y = self.text(imgtxt, (4,4))
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
	def message(self, text):
		w = 400
		h = w/2**.5
		x = 1024/2-w/2
		y = 780/2-h/2
		self.cnv.create_rectangle((x,y,x+w,y+h),
			fill='black', outline='red', width='5')
		self.text(text, (x+10,y+10), font='Liberation Serif', 
			anchor=tk.NW)
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



	def update(self, key):
		print time(), 'enter update'
		self.redraw=False
		if self.mode in [Browser.BROWSE, Browser.BLOG, Browser.POPULAR]:
			self.display()
		elif self.mode == Browser.SINGLE:
			self.zoom(key)
		self.free_mem()
		print time(), 'return update'


	def page_up(self, key):
		if key is 81:
			if self.img.rating < 6:
				self.img.rating += 1
				self.changes = True
				self.new_votes.add(self.img)
				self.redraw=True


	def page_down(self, key):
		if key is 89:
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

	# suggest only images with more than one source
	def pop_mode(self, key):
		if self.mode == Browser.POPULAR:
			self.mode = Browser.BROWSE
			self.repool()
			self.redraw=True
		else:
			self.pool = [p for p in picture.pictures() if len(p.sources)>1]
			self.mode = Browser.POPULAR
			self.redraw=True


	def quit(self, key):
		if len(trash)>0:
			print 'emptying trash: delete {} images'.format(len(trash))
			for p, path in trash.items():
				# delete image from disk.
				index.picture.delete(p)
			print 'trash empty'
		if self.changes:
			print "saving changes..."
			index.save()
		root.quit()


	# delete image/trash it
	def delete(self, key):
		trashed = trash.get(self.img)
		if trashed:
			path = trashed
			self.img.path = path
			#self.img.upgrade(img, self.img.url, save=True)
			del trash[self.img]
			self.redraw=True
		else:
			# save copy to trash
			trash[self.img] = self.img.path#, self.img.load())
			# redo history
			if self.img in self.hist:
				i = self.hist.index(self.img)
				self.hist = self.hist[i:]
				print 'imgs in history:', len(self.hist)
			self.replay(0)
			#self.mode = Browser.BROWSE
			self.redraw=True
			self.changes = True


	# compute similarities for current image
	def compute_sim(self, key):
		print 'compute similarities for', self.img
		self.message('Compute similarities:\n{}\nx{} imgs'.format(
			self.img,
			len(picture.pictures())))
		res = []
		for p in picture.pictures():
			if p != self.img:
				sim = self.img.similarity(p)
				if sim > .5:
					picture.connect(self.img,p,sim)
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


	# compute scores of blogs using page rank
	def compute_scores(self, key):
		print 'running page rank. yay!'
		self.message('\n'.join([
			'Computing blog scores using page rank:',
			'Iteration steps: 10',
			'','This might take a while...']))
		scores = index.scores(10)
		scs = sorted(scores.items(), key=lambda t:t[1])
		self.redraw=True
		print 'ok, got new blog scores. highest is {} with {}.'.format(
			scs[-1][0], scs[-1][1])
		self.changes=True



handlers={113:Browser.back,
					114:Browser.replay,
					36:Browser.zoom,
					81:Browser.page_up,
					89:Browser.page_down,
					9:Browser.quit,
					22:Browser.delete,
					119:Browser.delete,
					39:Browser.compute_sim,
					40:Browser.compute_scores,
					56:Browser.blog_mode,
					33:Browser.pop_mode}

def key(event):
  print time(), "pressed", event.keycode
  if event.keycode in range(10,20):
  	browser.forward(event.keycode-10)

  # handlers implemented by browser
  f = handlers.get(event.keycode)
  if f:
  	f(browser, event.keycode)
  if browser.redraw:
  	browser.update(event.keycode)
  print time(), 'leave keyhandler'

   #if len(browser.img.relates.keys()) > 0:
   	#browser.img = browser.img.relates.keys()[0]
   #print browser.img.location



# Ok Go
index.load()

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