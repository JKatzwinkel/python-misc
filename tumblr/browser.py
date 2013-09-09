import Tkinter as tk
from PIL import Image, ImageTk

import index
import weave.picture as picture
import weave.tumblr as tumblr


class Browser:
	BROWSE='browse'
	SINGLE='single'
	DETAIL='detail'
	def __init__(self, root):
		self.cur_imgs = [] # backup references against garbage coll.
		# init img tracking
		pics =  picture.pictures()
		pics = sorted(pics, key=lambda p:len(p.relates))
		self.img = pics[-1] # current image as Pict object
		self.hist = [] # history of recent images
		self.img_reg = {} # registry to avoid disk access
		self.thmb_reg = {} # thumbnail registry to avoid resize
		self.preview_reg = {} # preview registry to avoid resize
		self.mode = Browser.BROWSE
		# canvas
		self.cnv = tk.Canvas(root, bg="black")
		self.cnv.pack(side='top', fill='both', expand='yes')
		# put a button on the image panel to test it
		#self.button = tk.Button(self.cnv, text='button2')
		#self.button.pack(side='top')
		self.display()


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
		# history
		y = 0
		imgs=[]
		cover=0
		for p in self.hist[:15]:
			img = self.load_thmb(p)
			imgs.append((img, (0,y)))
			y+=img.height() - cover
			self.cur_imgs.append(img)
			cover = min(80, cover+8)
		for img, pos in imgs[::-1]:
			self.cnv.create_image(pos, 
				anchor=tk.NW, image=img)

		# current img
		img = self.load_img(self.img, size=(760, 740))
		self.cur_imgs.append(img)
		self.cnv.create_image((500,370), anchor=tk.CENTER, image=img) 
		# topleft= NW

		# similars
		posx = min([max([500+self.img.size[0]/2, 724]),784])
		self.choices = []
		i = 0 # counter
		x,y = posx,0 # curr. thmbnail pos.
		# retrieve
		sims = self.img.most_similar()
		while y<740 and len(sims)>0:
			s = sims.pop(0)
			if s.location and not s in self.hist:
				img = self.load_thmb(s)
				self.cnv.create_image((1024,y), 
					anchor=tk.NE, image=img)
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
			else:
				# save in history
				self.hist.insert(0,self.img)
			# forward and paint
			self.img = self.choices[ix]
			self.display()


	def back(self):
		if self.img in self.hist:
			i = self.hist.index(self.img)
			if i < min([len(self.hist)-1, 15]):
				self.img = self.hist[i+1]
		else:
			self.img = self.hist[0]
		self.display()

	def replay(self):
		if self.img in self.hist:
			i = self.hist.index(self.img)
			if i > 0:
				self.img = self.hist[i-1]
				self.display()



	def zoom(self):
		if self.mode == Browser.BROWSE:
			w,h=self.img.size
			#if w>760 or h>740:
			img = self.load_img(self.img)
			self.cnv.create_image((500,370), anchor=tk.CENTER, image=img)
			imgtxt=self.img.details()
			y = self.text(imgtxt, (0,0))
			medians = map(lambda b:b*8, self.img.histogram.mediane)
			med_col = '#{}'.format(''.join([('%02x' % b) for b in medians]))
			self.cnv.create_rectangle((10,y+30,100,y+94),
				outline='#fff',
				fill=med_col)
			self.text('Color code {}'.format(med_col), (0,y+100))
			self.text('Source: {}'.format(self.img.url), (0,724))
			self.cur_imgs = [img]
			self.mode = Browser.SINGLE
		elif self.mode == Browser.SINGLE:
			self.cnv.create_rectangle((0,0,780,300), fill='black')
			self.cnv.create_rectangle((0,724,780,740), fill='black')
			self.display()
			self.mode = Browser.BROWSE


def key(event):
  print "pressed", event.keycode
  if event.keycode in range(10,20):
  	browser.forward(event.keycode-10)
  if event.keycode == 113:
  	browser.back()
  if event.keycode == 36:
  	browser.zoom()
  if event.keycode == 114:
  	browser.replay()

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