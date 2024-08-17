from tkinter import *

def show_msg():
    
    msg = Message(win,text='This message will disappear in 5 seconds')
    msg.pack()
    win.after(5000, msg.destroy)


win = Tk()

Button(win, text='Press to see message', command=show_msg).pack()

win.mainloop()