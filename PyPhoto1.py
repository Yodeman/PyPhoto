import sys, math, os
from tkinter import *
from tkinter.filedialog import SaveAs, Directory
from tkinter.messagebox import showinfo
from PIL import Image
from PIL.ImageTk import PhotoImage
from view_thumb import makeThumbs

saveDialog = SaveAs(title='Save As')
openDialog = Directory(title='Select Image Directory To Open')
trace = print
appname = 'PyPhoto'

class scrolledCanvas(Canvas):
    """
    a canvas in a container that automatically makes vertical
    and horizontal scroll bars for itself
    """
    def __init__(self, container):
        super().__init__(container)
        self.config(borderwidth=0)
        vbar = Scrollbar(container)
        hbar = Scrollbar(container, orient='horizontal')
        vbar.pack(side=RIGHT, fill=Y)
        hbar.pack(side=BOTTOM, fill=X)
        self.pack(side=TOP, fill=BOTH, expand=YES)
        vbar.config(command=self.yview)
        hbar.config(command=self.xview)
        self.config(yscrollcommand=vbar.set)
        self.config(xscrollcommand=hbar.set)

class viewOne(Toplevel):
    """
    Open a single image in a pop-up window when created;
    scroll if image is too big for display;
    resizes window's height or width on mouse click;
    stretches or shrinks; zooms in/out
    """
    def __init__(self, imgdir, imgfile, forcesize=()):
        super().__init__()
        helptext = '(click L/R or press I/O to resize, Ctrl+S to save, Ctrl+O to open)'
        Button(self, text='Help', command=(lambda:showinfo(appname, helptext))).pack()
        self.title(imgfile+' - '+appname)
        imgpath = os.path.join(imgdir, imgfile)
        imgpil = Image.open(imgpath)
        self.canvas = scrolledCanvas(self)
        self.canvas.focus_set()
        self.drawImage(imgpil, forcesize)
        self.canvas.bind('<Button-1>', self.onSizeToDisplayHeight)
        self.canvas.bind('<Button-3>', self.onSizeToDisplayWidth)
        self.canvas.bind('<KeyPress-i>', self.onZoomIn)
        self.canvas.bind('<KeyPress-o>',  self.onZoomOut)
        self.canvas.bind('<Control-s>', self.onSaveImage)
        self.canvas.bind('<Control-o>', onDirectoryOpen)
        #self.focus()

    def drawImage(self, imgpil, forcesize=()):
        imgtk = PhotoImage(image=imgpil)
        scrwide, scrhigh = forcesize or self.maxsize()
        imgwide = imgtk.width()
        imghigh = imgtk.height()

        fullsize = (0, 0, imgwide, imghigh)
        viewwide = min(imgwide, scrwide)
        viewhigh = min(imghigh, scrhigh)

        canvas = self.canvas
        canvas.delete('all')
        canvas.config(height=viewhigh, width=viewwide)
        canvas.config(scrollregion=fullsize)
        canvas.create_image(0, 0, image=imgtk, anchor=NW)

        if imgwide <= scrwide and imghigh <= scrhigh:
            self.state('normal')
        elif sys.platform[:3] == 'win':
            self.state('zoomed')
        self.saveimage = imgpil
        self.savephoto = imgtk
        #trace((scrwide, scrhigh), imgpil.size)
        self.update()

    def sizeToDisplaySide(self, scaler):
        # resize to fill one side of the display
        imgpil = self.saveimage
        scrwide, scrhigh = self.maxsize()
        imgwide, imghigh = imgpil.size
        newwide, newhigh = scaler(scrwide, scrhigh, imgwide, imghigh)
        if (newwide * newhigh < imgwide * imghigh):
            filter = Image.ANTIALIAS
        else:
            filter = Image.BICUBIC
        imgnew = imgpil.resize((newwide, newhigh), filter)
        self.drawImage(imgnew)

    def onSizeToDisplayHeight(self, event):
        def scaleHigh(scrwide, scrhigh, imgwide, imghigh):
            newhigh = scrhigh
            newwide = int(scrhigh * (imgwide/imghigh))
            return (newwide, newhigh)
        self.sizeToDisplaySide(scaleHigh)

    def onSizeToDisplayWidth(self, event):
        def scaleWide(scrwide, scrhigh, imgwide, imghigh):
            newwide = scrwide
            newhigh = int(scrwide * (imghigh/imgwide))
            return (newwide, newhigh)
        self.sizeToDisplaySide(scaleWide)

    def zoom(self, factor):
        # zoom in or out in increments
        imgpil = self.saveimage
        wide, high = imgpil.size
        if factor < 1.0:
            filter = Image.ANTIALIAS
        else:
            filter = Image.BICUBIC
        new = imgpil.resize((int(wide * factor), int(high * factor)), filter)
        self.drawImage(new)

    def onZoomIn(self, event, incr=0.10):
        #trace('Zooming In')
        self.zoom(1.0 + incr)

    def onZoomOut(self, event, decr=0.10):
        #trace('Zooming Out')
        self.zoom(1.0-decr)

    def onSaveImage(self, event):
        filename = saveDialog.show()
        if filename:
            self.saveimage.save(filename)

def onDirectoryOpen(event):
    dirname = openDialog.show()
    if dirname:
        viewThumbs(dirname, kind=Toplevel)

def viewThumbs(imgdir, kind=Toplevel, numcols=None, height=400, width=500):
    win = kind()
    helptxt = 'Press Ctrl+o to open other'
    Button(win, text='Help', command=(lambda:showinfo(appname, helptxt))).pack()
    win.title(appname)
    Button(win, text='Quit', command=win.quit).pack(side=BOTTOM, expand=YES)
    canvas = scrolledCanvas(win)
    canvas.config(height=height, width=width)
    thumbs = makeThumbs(imgdir)
    numthumbs = len(thumbs)
    if not numcols:
        numcols = int(math.ceil(math.sqrt(numthumbs)))
    numrows= int(math.ceil(numthumbs/numcols))
    linksize = max(max(thumb[1].size) for thumb in thumbs)
    trace(linksize)
    fullsize = (0, 0,
                (linksize * numcols), (linksize * numrows))
    canvas.config(scrollregion=fullsize)

    rowpos = 0
    savephotos = []
    while thumbs:
        thumbsrow, thumbs = thumbs[:numcols], thumbs[numcols:]
        colpos = 0
        for (imgfile, imgobj) in thumbsrow:
            photo = PhotoImage(imgobj)
            link = Button(canvas, image=photo)
            def handler(savefile=imgfile):
                viewOne(imgdir, savefile)
            link.configure(command=handler, width=linksize, height=linksize)
            link.pack(side=LEFT, expand=YES)
            canvas.create_window(colpos, rowpos, anchor=NW, window=link, width=linksize, height=linksize)
            colpos += linksize
            savephotos.append(photo)
        rowpos += linksize
    win.bind('<Control-o>', onDirectoryOpen)
    win.savephotos = savephotos
    return win

if __name__ == '__main__':
    imgdir = 'images'
    if len(sys.argv) > 1:
        imgdir = sys.argv[1]
    if os.path.exists(imgdir):
        mainwin = viewThumbs(imgdir, kind=Tk)
    else:
        mainwin = Tk()
        mainwin.title(appname)
        handler = lambda:onDirectoryOpen(None)
        Button(mainwin, text='Open Image Directory', command=handler).pack()
    mainwin.mainloop()
