import Tkinter as tk
from PIL import Image, ImageTk

root = tk.Tk()
root.title('background image')

# pick an image file you have .bmp  .jpg  .gif.  .png
# load the file and covert it to a Tkinter image object
imageFile = "images/lda3m4he0E1qdlb01o1.jpg"
image1 = ImageTk.PhotoImage(Image.open(imageFile))

# get the image size
w = image1.width()
h = image1.height()

# position coordinates of root 'upper left corner'
x = 0
y = 0

# make the root window the size of the image
root.geometry("%dx%d+%d+%d" % (w, h, x, y))

# root has no image argument, so use a label as a panel
panel1 = tk.Label(root, image=image1)
panel1.pack(side='top', fill='both', expand='yes')

# put a button on the image panel to test it
button2 = tk.Button(panel1, text='button2')
button2.pack(side='top')

# save the panel's image from 'garbage collection'
panel1.image = image1

# start the event loop
root.mainloop()