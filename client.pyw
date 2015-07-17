from socket import *
import pickle
import random
import sys, os, time
import pygame

# GUI
try:
    from tkinter import *
    from tkinter.scrolledtext import ScrolledText
    from tkinter.ttk import *
    from tkinter.simpledialog import askstring
except:
    from Tkinter import *
    from ScrolledText import *
    from tkSimpleDialog import askstring
    
# Config Parser
try:
    from configparser import ConfigParser
except:
    from ConfigParser import ConfigParser

# Threading
try:
    from threading import Thread
    def new_thread(proc, args=()):
        th = Thread(target=proc, args=args)
        th.daemon = True
        th.start()
except:
    import thread
    def new_thread(proc, args=()):
        thread.start_new_thread(proc, args)

if sys.version_info[0] == 2:
    input = raw_input

def relative(path):
    basePath = os.path.dirname(__file__)
    rPath = os.path.join(basePath, path)
    return rPath

class CLIENT_APP(Frame):
    def __init__(self, parent, name="guest"):
        Frame.__init__(self, parent)
        self.parent = parent
        self.name = name

        self.init_ui()
        self.init_chat()

        self.msgs = []
        self.state = 1
        
        self._col = 0

        self.snd_wakeup = None
        self.snd_message = None
        self.snd_online = None
        self.snd_mention = None
        self.sounds = True

    def del_chat(self):        
        from datetime import datetime
        tm = str(datetime.now())
        tm = tm.replace(":", "_")
        tm = tm.replace(" ", "_")

        import codecs
        if not os.path.exists("temp"):
            os.mkdir("temp")
            
        with codecs.open('temp/messages_tmp_'+tm+'.log', 'w', 'utf-8') as f:
            for m in self.msgs:
                f.write(str(m)+"\n")
        
        msg = {
            "type": "DISCONN",
            "data": self.name
        }
        self.sock.sendto(pickle.dumps(msg), self.address)
        self.sock.close()
        self.state = 0
        self.parent.destroy()

    def playsnd(self, snd):
        if snd is None: return
        c = snd.play()
        while c.get_busy():
            pygame.time.delay(100)
    
    def client_thread(self):
        
        # Init PYGAME :)
        pygame.mixer.init(44100, -16, 1, 1024)

        try:
            self.snd_wakeup = pygame.mixer.Sound(relative('data\\LC_USER_WAKEUP.wav'))
            self.snd_message = pygame.mixer.Sound(relative('data\\LC_USER_MSG.wav'))
            self.snd_online = pygame.mixer.Sound(relative('data\\LC_USER_ONLINE.wav'))
            self.snd_mention = pygame.mixer.Sound(relative('data\\LC_USER_MENTION.wav'))
        except:
            self.sounds = False
            print("Could not load sounds.")
        
        datul = {
            "type": "GETUSERLIST",
            "data": 0
        }
        self.sock.sendto(pickle.dumps(datul), self.address)
        while True:
            try:
                if self.state == 0: break
                
                data, addr = self.sock.recvfrom(4096)
                if not data:
                    pass
                resp = pickle.loads(data)

                if resp["type"] == "MSG":
                    _from, msg = resp["data"]
                    recv = "%s: %s" % (_from, msg)
                    self.msgs.append(resp["data"])
                    print(recv)
                    
                    self.messages.config(state=NORMAL)

                    padfrom = _from.rjust(22)
                    padmsg = padfrom+": "+msg
                    if _from == "[SERVER]":
                        self.messages.insert(END, "|"+padmsg+"\n", "serv_message")
                        self.messages.see(END)
                        
                        if "joined" in msg:
                            if self.sounds:
                                self.playsnd(self.snd_online)
                    else:
                        _tag = "odd" if self._col == 1 else "even"

                        self.messages.insert(END, "|"+padmsg+"\n", _tag)
                        self.messages.see(END)
                        
                        if self.sounds:
                            if self.name in msg and _from != self.name:                            
                                self.playsnd(self.snd_mention)
                            else:
                                self.playsnd(self.snd_message)
                                
                    self._col = 0 if self._col == 1 else 1
                    
                    self.messages.config(state=DISABLED)
                    
                elif resp["type"] == "WAKEUP":
                    self.playsnd(self.snd_wakeup)

                elif resp["type"] == "ERR_FATAL":
                    self.msgs.append(resp["data"])
                    print(resp["data"])
                    
                    self.messages.config(state=NORMAL)
                    self.messages.insert(END, resp["data"], "err")
                    self.messages.config(state=DISABLED)
                    self.sock.close()
                    self.parent.destroy()
                    sys.exit()
                pygame.time.delay(1)
            except:
                pygame.time.delay(1)
    
    def init_chat(self):
        
        conf = ConfigParser()
        conf.readfp(open(r'config.ini'))
        
        self.host = conf.get("network", "host")
        self.port = int(conf.get("network", "port"))
        self.address = (self.host, self.port)

        snd = int(conf.get("chat", "sounds"))
        self.sounds = True if snd == 1 else False
                
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.setblocking(False)
        
        print("Simple Chat Client [%s:%d]" % (self.host, self.port))
        print("---------------------------------------------------")

        msg = {
            "type": "CONN",
            "data": self.name
        }
        self.sock.sendto(pickle.dumps(msg), self.address)

        new_thread(self.client_thread)
        
    def init_ui(self):
        if sys.version_info[0] > 2:
            s = Style()
            s.theme_use('clam')
        
        self.parent.title("L-Dev's Simple Chat")
        self.pack(fill=BOTH, expand=1)

        self.messages = ScrolledText(self)
        self.messages.config(font=("consolas", 9), wrap='word', state=DISABLED)
        self.messages.pack(side=TOP, fill=BOTH, expand=TRUE)

        self.messages.tag_configure("serv_message", foreground="black", background="yellow")
        self.messages.tag_configure("even", foreground="black", bgstipple="gray50", background="#dddddd")
        self.messages.tag_configure("odd", foreground="black", bgstipple="gray50", background="white", borderwidth=1, relief=RIDGE)
        self.messages.tag_configure("err", foreground="white", bgstipple="gray50", background="red", borderwidth=1, relief=RIDGE)
        
        msgarea = Frame(self)
        msgarea.pack(fill=X, side=BOTTOM)
        
        self.message = Entry(msgarea)
        self.message.pack(fill=X, side=LEFT, expand=1)

        def send_click():
            cmd = self.message.get()
            if cmd == "/quit" or cmd == "/q":
                self.del_chat()
            elif cmd == "/userlist" or cmd == "/ul":
                datul = {
                    "type": "GETUSERLIST",
                    "data": 0
                }
                self.sock.sendto(pickle.dumps(datul), self.address)
            elif cmd == "/wakeup" or cmd == "/wu":
                cmsg = {
                    "type": "HEYWAKEUP",
                    "data": self.name
                }
                self.sock.sendto(pickle.dumps(cmsg), self.address)
            else:
                if cmd == "" or cmd == " ":
                    return
                cmsg = {
                    "type": "CHATMSG",
                    "data": [self.name, cmd]
                }
                self.sock.sendto(pickle.dumps(cmsg), self.address)
            self.message.delete(0, END)

        def send_click_ev(event):
            send_click()

        def get_last_msg(e):
            if len(self.msgs) <= 0: return
            userms = [m for m in self.msgs if m[0] != "[SERVER]"]
            self.message.delete(0, END)
            self.message.insert(0, "%s: %s" % (userms[-1][0], userms[-1][1]))
        
        self.message.bind("<Return>", send_click_ev)
        self.message.bind("<Up>", get_last_msg)
        
        self.send = Button(msgarea, text="Send", command=send_click)
        self.send.pack(side=RIGHT)

root = Tk()
root.withdraw()

name = askstring("L-Dev Chat", "User Name", initialvalue="guest", parent=root)
while name == "" or len(name) > 18 or len(name) < 3:
    name = askstring("L-Dev Chat", "User Name(Cannot be null or have more than 18 characters or less than 3 characters)", initialvalue="guest", parent=root)

app = CLIENT_APP(root, name)

def on_close():
    app.del_chat()

if __name__ == "__main__":    
    root.geometry("512x512+40+40")
    #root.resizable(width=FALSE, height=FALSE)
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.deiconify()
    root.mainloop()
