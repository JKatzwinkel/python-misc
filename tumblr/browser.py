import Tkinter as tk
from PIL import Image, ImageTk

import index
import weave.picture as picture
import weave.tumblr as tumblr


class Browser:
	def __init__(self, root):
		self.cur_imgs = [] # backup references against garbage coll.
		# init img tracking
		pics =  picture.pictures()
		pics = sorted(pics, key=lambda p:len(p.relates))
		self.img = pics[-2] # current image as Pict object
		self.hist = [] # history of recent images
		self.img_reg = {} # registry to avoid disk access
		# canvas
		self.cnv = tk.Canvas(root, bg="black")
		self.cnv.pack(side='top', fill='both', expand='yes')
		# put a button on the image panel to test it
		self.button = tk.Button(self.cnv, text='button2')
		self.button.pack(side='top')
		self.display()


	# takes a Pict instance and returns a scaled (if size=(x,y) given)
	# ImageTk.PhotoImage object.
	def load_img(self, pict, size=None):
		w,h = pict.size
		mw,mh = size
		ratio = min([float(mw)/w, float(mh)/h])
		img = self.img_reg.get(pict)
		if not img:
			img = pict.load()
			self.img_reg[pict] = img
		img = img.resize((int(w*ratio),int(h*ratio)), Image.ANTIALIAS)
		img = ImageTk.PhotoImage(img)
		return img

	def display(self):
		w,h = self.img.size
		img = self.img.load()
		ratio = min([800./w, 740./h])
		img = img.resize((int(w*ratio),int(h*ratio)), Image.ANTIALIAS)
		img = ImageTk.PhotoImage(img)
		#img = self.load_img(self.img, size=(800, 740))
		self.cnv.create_image((500,370), anchor=tk.CENTER, image=img) 
		self.cur_imgs = [img] # keep ref for objects (garbage coll)
		# topleft= NW
		posx = min([max([500+self.img.size[0]/2+20, 724]),900])
		# similars
		self.choices = []
		i = 0 # counter
		sims = self.img.most_similar()
		while i < 3 and len(sims)>0:
			s = sims.pop(0)
			if s.location:
				print s, s.location
				w,h = s.size
				ratio = min([200./w,223./h]) # scale ratio
				# blit image
				img = s.load()
				img = img.resize((int(w*ratio),int(h*ratio)), Image.ANTIALIAS)
				img = ImageTk.PhotoImage(img)
				self.cnv.create_image((posx,140+i*233), 
					anchor=tk.CENTER, image=img)
				self.cur_imgs.append(img)
				self.choices.append(s)
				i+=1
		# history
		size = 140.
		for i,p in enumerate(self.hist[:8]):
			w,h = p.size
			ratio = min([size/w,size/h]) # scale ratio
			# blit image
			img = p.load()
			img = img.resize((int(w*ratio),int(h*ratio)), Image.ANTIALIAS)
			img = ImageTk.PhotoImage(img)
			self.cnv.create_image((90,90+i*size), 
				anchor=tk.CENTER, image=img)
			self.cur_imgs.append(img)
			size-=10



	def forward(self, i):
		# save in history
		self.hist.insert(0, self.img)
		# forward and paint
		self.img = self.choices[i]
		self.display()


def key(event):
  print "pressed", event.keycode
  if event.keycode in [10,11,12]:
  	browser.forward(event.keycode-10)

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