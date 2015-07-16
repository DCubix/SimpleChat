from socket import *
import pickle
import random
import sys, os

# GUI
try:
    from tkinter import *
    from tkinter.scrolledtext import ScrolledText
    from tkinter.ttk import *
except:
    from Tkinter import *
    from ScrolledText import *
    
# Config Parser
try:
    from configparser import ConfigParser
except:
    from ConfigParser import ConfigParser

# Threading
try:
    from threading import Thread
    def new_thread(proc, args=()):
        Thread(target=proc, args=args).start()
except:
    import thread
    def new_thread(proc, args=()):
        thread.start_new_thread(proc, args)

name = input(" User Name >>>> ")
name = name if name != "" else "GUEST"+str(random.randint(1, 999))

class CustomText(ScrolledText):
    '''A text widget with a new method, highlight_pattern()

    example:

    text = CustomText()
    text.tag_configure("red", foreground="#ff0000")
    text.highlight_pattern("this should be red", "red")

    The highlight_pattern method is a simplified python
    version of the tcl code at http://wiki.tcl.tk/3246
    '''
    def __init__(self, *args, **kwargs):
        ScrolledText.__init__(self, *args, **kwargs)

    def highlight_pattern(self, pattern, tag, start="1.0", end="end",
                          regexp=False):
        '''Apply the given tag to all text that matches the given pattern

        If 'regexp' is set to True, pattern will be treated as a regular
        expression.
        '''

        start = self.index(start)
        end = self.index(end)
        self.mark_set("matchStart", start)
        self.mark_set("matchEnd", start)
        self.mark_set("searchLimit", end)

        count = IntVar()
        while True:
            index = self.search(pattern, "matchEnd","searchLimit",
                                count=count, regexp=regexp)
            if index == "": break
            self.mark_set("matchStart", index)
            self.mark_set("matchEnd", "%s+%sc" % (index, count.get()))
            self.tag_add(tag, "matchStart", "matchEnd")

class CLIENT_APP(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.parent = parent

        self.init_ui()
        self.init_chat()

        self.msgs = []
        self.state = 1
        
        self._col = 0

    def del_chat(self):
        global name
        
        from datetime import datetime
        tm = str(datetime.now())
        tm = tm.replace(":", "_")
        tm = tm.replace(" ", "_")

        import codecs
        with codecs.open('data/temp/messages_tmp_'+tm+'.log', 'w', 'utf-8') as f:
            for m in self.msgs:
                f.write(m+"\n")
        
        msg = {
            "type": "DISCONN",
            "data": name
        }
        self.sock.sendto(pickle.dumps(msg), self.address)
        self.sock.close()
        self.state = 0
        self.parent.destroy()
        
    def client_thread(self):
        while True:
            try:
                if self.state == 0: break
                
                data, addr = self.sock.recvfrom(4096)
                if not data:
                    pass
                resp = pickle.loads(data)

                if resp["type"] == "MSG":
                    self.msgs.append(resp["data"])
                    print(resp["data"])
                    
                    self.messages.config(state=NORMAL)
                                        
                    if "[SERVER]" in resp["data"]:
                        self.messages.insert(END, "|"+resp["data"]+"\n")
                        self.messages.highlight_pattern(r"\|.+?:", "serv_message", regexp=True)
                    else:
                        _tag = "odd" if self._col == 1 else "even"
                        self.messages.insert(END, "|"+resp["data"]+"\n", _tag)

                    self._col = 0 if self._col == 1 else 1
                    
                    self.messages.see(END)                    
                    self.messages.config(state=DISABLED)
                                        
                elif resp["type"] == "ERR_FATAL":
                    self.msgs.append(resp["data"])
                    print(resp["data"])
                    
                    self.messages.config(state=NORMAL)
                    self.messages.insert(END, resp["data"], "err")
                    self.messages.config(state=DISABLED)
                    self.sock.close()
                    self.parent.destroy()
                    sys.exit()
            except:
                pass
    
    def init_chat(self):
        global name
        
        conf = ConfigParser()
        conf.readfp(open(r'config.ini'))
        
        self.host = conf.get("network", "host")
        self.port = int(conf.get("network", "port"))
        self.address = (self.host, self.port)

        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.setblocking(False)
        
        print("Simple Chat Client [%s:%d]" % (self.host, self.port))
        print("---------------------------------------------------")

        msg = {
            "type": "CONN",
            "data": name
        }
        self.sock.sendto(pickle.dumps(msg), self.address)

        new_thread(self.client_thread)
        
    def init_ui(self):
        global name

        s = Style()
        s.theme_use('clam')
        
        self.parent.title("L-Dev's Simple Chat")
        self.pack(fill=BOTH, expand=1)

        self.messages = CustomText(self)
        self.messages.config(font=("consolas", 9), wrap='word', state=DISABLED)
        self.messages.pack(side=TOP, fill=BOTH, expand=TRUE)

        self.messages.tag_configure("serv_message", foreground="black", background="yellow")
        self.messages.tag_configure("even", foreground="black", background="#dddddd")
        self.messages.tag_configure("odd", foreground="black", background="#ffffff")
        self.messages.tag_configure("err", foreground="white", background="red")
        
        msgarea = Frame(self)
        msgarea.pack(fill=X, side=BOTTOM)
        
        self.message = Entry(msgarea)
        self.message.pack(fill=X, side=LEFT, expand=1)

        def send_click():
            global name

            if self.message.get() == "/quit" or self.message.get() == "/q":
                self.del_chat()
            else:
                if self.message.get() == "" or self.message.get() == " ":
                    return
                cmsg = {
                    "type": "CHATMSG",
                    "data": [name, self.message.get()]
                }
                self.sock.sendto(pickle.dumps(cmsg), self.address)
                self.message.delete(0, END)

        def send_click_ev(event):
            send_click()

        self.message.bind("<Return>", send_click_ev)
        
        self.send = Button(msgarea, text="Send", command=send_click)
        self.send.pack(side=RIGHT)

root = Tk()
app = CLIENT_APP(root)

def on_close():
    app.del_chat()

if __name__ == "__main__":    
    root.geometry("512x512+40+40")
    root.resizable(width=FALSE, height=FALSE)
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
