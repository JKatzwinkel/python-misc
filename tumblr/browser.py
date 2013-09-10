import Tkinter as tk
from PIL import Image, ImageTk
from time import time

import index
import weave.picture as picture
import weave.tumblr as tumblr
import util

class Browser:
	BROWSE='browse'
	SINGLE='single'
	DETAIL='detail'
	def __init__(self, root):
		self.cur_imgs = [] # backup references against garbage coll.
		self.img_reg = {} # registry to avoid disk access
		self.thmb_reg = {} # thumbnail registry to avoid resize
		self.preview_reg = {} # preview registry to avoid resize
		self.mode = Browser.BROWSE
		self.changes = False # changes to be saved?
		self.new_votes = set() # keep track of new ratings
		# init img tracking
		pics = picture.to_review()
		if len(pics)<1:
			pics = picture.favorites()[:20]
		self.pool = set(pics)
		#pics = sorted(pics, key=lambda p:p.rating)
		self.choose(pics[-1]) # current image as Pict object
		self.hist = [self.img] # history of recent images
		# canvas
		self.cnv = tk.Canvas(root, bg="black")
		self.cnv.pack(side='top', fill='both', expand='yes')
		# put a button on the image panel to test it
		#self.button = tk.Button(self.cnv, text='button2')
		#self.button.pack(side='top')
		self.display()


	def get_choices(self):
		# suggest pictures with similiarity link to current
		choices = dict(self.img.relates)
		# prefer pictures in pool,
		# prefer newest pictures
		for p in self.pool:
			boost = min(1.8,util.days_since(p.reviewed)/99)
			boost += 1.5/(1+util.days_since(p.date))
			choices[p] = choices.get(p, 0)+boost
		# calculate scores
		for p, sim in choices.items():
			score = (1+p.rating) * sim
			for vote in self.new_votes:
				adv = p.relates.get(vote)
				if not adv:
					adv = vote.relates.get(p,0)
				score += vote.rating*adv/len(self.new_votes)
			choices[p] = score
		# return candidates ordered by highest score desc.
		choices = sorted(choices.items(), key=lambda t:t[1])
		return [t[0] for t in choices[::-1]]


	# set pict as currently viewed 
	def choose(self, pict):
		self.img = pict
		pict.reviewed = time()
		self.changes = True

	# takes a Pict instance and returns a scaled (if size=(x,y) given)
	# ImageTk.PhotoImage object.
	def load_img(self, pict, size=None):
		w,h = pict.size
		img = self.img_reg.get(pict)
		if not img:
			img = pict.load()
			self.img_reg[pict] = img
		if size:
			mw,mh = size
			ratio = min([float(mw)/w, float(mh)/h])
			img = img.resize((int(w*ratio),int(h*ratio)), Image.ANTIALIAS)
		img = ImageTk.PhotoImage(img)
		return img

	# retrieve thumbnail for Pict object
	def load_thmb(self, pict):
		img = self.img_reg.get(pict)
		if not img:
			img = pict.load()
			self.img_reg[pict] = img
		thmb = self.thmb_reg.get(img)
		if not thmb:
			w,h = pict.size
			ratio = min([140./w, 140./h])
			thmb = img.resize((int(w*ratio),int(h*ratio)), Image.LINEAR)
			thmb = ImageTk.PhotoImage(thmb)
		return thmb




	def display(self):
		self.cur_imgs = [] # keep ref for objects (garbage coll)
		self.cnv.create_rectangle((0,0,1024,740), fill='black')
		# history
		y = 0
		imgs=[]
		cover=0
		for p in self.hist[:15]:
			img = self.load_thmb(p)
			imgs.append((img, (0,y), p.rating))
			y+=img.height() - cover
			self.cur_imgs.append(img)
			cover = min(80, cover+4)
		for img, pos, stars in imgs[::-1]:
			#self.cnv.create_rectangle((pos[0], pos[1],
				#pos[0]+img.width(), pos[1]+img.height()), fill='black')
			self.cnv.create_image(pos, 
				anchor=tk.NW, image=img)
			self.cnv.create_text(pos[0]+4, pos[1]+4, anchor=tk.NW, 
					font='Arial 12 bold', fill='white', text='*'*stars)

		# current img
		img = self.load_img(self.img, size=(720, 740))
		self.cur_imgs.append(img)
		self.cnv.create_image((500,370), anchor=tk.CENTER, image=img) 
		# topleft= NW

		# similars
		posx = min([max([500+self.img.size[0]/2, 724]),784])
		self.choices = []
		i = 0 # counter
		x,y = posx,0 # curr. thmbnail pos.
		# retrieve
		#sims = self.img.most_similar()
		sims = self.get_choices()
		while y<740 and len(sims)>0:
			s = sims.pop(0)
			if s.location and not s in self.hist:
				img = self.load_thmb(s)
				#self.cnv.create_rectangle((1024-img.width(),y,1024,y+img.height()),
					#fill='black')
				self.cnv.create_image((1024,y), 
					anchor=tk.NE, image=img)
				#self.cnv.create_text(1028-img.width(), y+4, anchor=tk.NW, 
					#font='Arial 14 bold', fill='white', text='*'*s.rating)
				# write little info caption
				notes=[]
				if s.rating>0:
					notes.append('*'*s.rating)
				sim = self.img.relates.get(s)
				if sim:
					notes.append('{:.1f}%'.format(sim*100))
				days=util.days_since(s.date)
				if days<7:
					notes.append('new!\n({} days)'.format(int(days)))
				days=int(util.days_since(s.reviewed))
				if days > 31:
					if days < 100:
						notes.append('awaits review\n({} days)'.format(days))
					else:
						notes.append('awaits review!')
				self.cnv.create_text(1020-img.width(), y+4, anchor=tk.NE, 
					font='Arial 10', justify='right', fill='white', 
					text='\n'.join(notes))
				y += img.height()
				self.cur_imgs.append(img)
				self.choices.append(s)

	def text(self, output, pos):
		lines = output.split('\n')
		x, y = pos
		for n, line in enumerate(lines):
			self.cnv.create_text(x, y+n*13+1, anchor=tk.NW, 
				font='Arial 12',
				fill='black',
				text=line)
			self.cnv.create_text(x+1, y+n*13, anchor=tk.NW, 
				font='Arial 12',
				fill='black',
				text=line)
			self.cnv.create_text(x, y+n*13, anchor=tk.NW, 
				font='Arial 12',
				fill='white',
				text=line)
		return y+len(lines)*13


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
			self.display()


	def back(self, key):
		if self.img in self.hist:
			i = self.hist.index(self.img)
			if i < min([len(self.hist)-1, 15]):
				self.choose(self.hist[i+1])
		else:
			self.choose(self.hist[0])
		self.display()

	def replay(self, key):
		if self.img in self.hist:
			i = self.hist.index(self.img)
			if i > 0:
				self.choose(self.hist[i-1])
				self.display()
			else:
				self.forward(0)
		else:
			self.forward(0)


	# single image view
	def display_single(self):
		w,h=self.img.size
		#if w>760 or h>740:
		img = self.load_img(self.img)
		self.cnv.create_image((500,370), anchor=tk.CENTER, image=img)
		imgtxt=self.img.details()
		y = self.text(imgtxt, (0,0))
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


	def zoom(self, key):
		# determine whether to change state		
		if self.mode == Browser.BROWSE:
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
		if self.mode == Browser.BROWSE:
			self.display()
		elif self.mode == Browser.SINGLE:
			self.zoom(key)

	def page_up(self, key):
		if key is 81:
			if self.img.rating < 6:
				self.img.rating += 1
				self.changes = True
				self.new_votes.add(self.img)
				self.update(key)

	def page_down(self, key):
		if key is 89:
			if self.img.rating > 0:
				self.img.rating = self.img.rating-1
				self.new_votes.add(self.img)
				self.changes = True
				self.update(key)

	def quit(self, key):
		if self.changes:
			print "saving changes..."
			index.save()
		root.quit()

	def delete(self, key):
		index.picture.delete(self.img)
		if self.img in self.hist:
			i = self.hist.index(self.img)
			self.hist = self.hist[i:]
		self.replay(0)
		self.mode = Browser.BROWSE
		self.update(key)
		self.changes = True

	# compute similarities for current image
	def compute_sim(self, key):
		print 'compute similarities for', self.img
		for p in picture.pictures():
			if p != self.img:
				sim = self.img.similarity(p)
				if p > .5:
					picture.connect(self.img,p,sim)
		print 'done.'


handlers={113:Browser.back,
					114:Browser.replay,
					36:Browser.zoom,
					81:Browser.page_up,
					89:Browser.page_down,
					9:Browser.quit,
					22:Browser.delete,
					119:Browser.delete,
					39:Browser.compute_sim}

def key(event):
  print "pressed", event.keycode
  if event.keycode in range(10,20):
  	browser.forward(event.keycode-10)

  # handlers implemented by browser
  f = handlers.get(event.keycode)
  if f:
  	f(browser, event.keycode)

   #if len(browser.img.relates.keys()) > 0:
   	#browser.img = browser.img.relates.keys()[0]
   #print browser.img.location



# Ok Go
index.load()

root = tk.Tk()
root.title('background image')

# pick an image file you have .bmp  .jpg  .gif.  .png
# load the file and covert it to a Tkinter image object
imageFile = "images/lda3m4he0E1qdlb01o1.jpg"
image1 = ImageTk.PhotoImage(Image.open(imageFile))

# make the root window the size of the image
root.geometry("%dx%d+%d+%d" % (1024, 740, 0, 0))
root.bind("<Key>", key)	

# root has no image argument, so use a label as a panel
#panel1 = tk.Label(root, image=image1)
#panel1.pack(side='top', fill='both', expand='yes')



# save the panel's image from 'garbage collection'
#panel1.image = image1

browser = Browser(root)

# start the event loop
root.mainloop()
