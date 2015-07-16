from socket import *
import pickle
from configparser import ConfigParser

conf = ConfigParser()
conf.readfp(open(r'config.ini'))

host = conf.get("network", "host")
port = int(conf.get("network", "port"))

serv = socket(AF_INET, SOCK_DGRAM)
serv.bind((host, port))

print("Simple Chat Server [%s:%d]" % (host, port))
print("----------------------------------------------")

USERS = {}

def broadcast(msg):
    dat = {
        "type": "MSG",
        "data": str(msg)
    }
    for n, a in USERS.items():
        serv.sendto(pickle.dumps(dat), a)

def broadcast_chat(msg, exp):
    dat = {
        "type": "MSG",
        "data": str(msg)
    }
    for n, a in USERS.items():
        if n == exp: continue
        serv.sendto(pickle.dumps(dat), a)

namewidth = 20
servtext = "[SERVER]".rjust(namewidth)
while True:
    try:
        data, addr = serv.recvfrom(1024)
        msg = pickle.loads(data)

        if msg["type"] == "CONN":
            if msg["data"] not in USERS.keys():
                USERS[msg["data"]] = addr
                USERLIST = "Currently Online: ".rjust(namewidth)+",".join(list(USERS.keys()))
                info = servtext+": %s has joined the party.\n%s" % (msg["data"], USERLIST)
                print(info.strip("\n"))
                broadcast(info)
            else:
                dat = {
                    "type": "ERR_FATAL",
                    "data": servtext+": The name \"%s\" is already taken." % msg["data"]
                }
                serv.sendto(pickle.dumps(dat), addr)
        elif msg["type"] == "DISCONN":
            del USERS[msg["data"]]
            USERLIST = "Currently Online: ".rjust(namewidth)+",".join(list(USERS.keys()))
            info = servtext+": %s doesn't want to party anymore.\n%s" % (msg["data"], USERLIST)
            print(info.strip("\n"))
            broadcast(info)
        elif msg["type"] == "CHATMSG":
            _from, message = msg["data"]
            info = "%s: %s" % (_from.rjust(namewidth), message)
            print(info.strip("\n"))
            broadcast(info)
        elif msg["type"] == "USERLIST":
            ULIST = list(USERS.keys())
            dat = {
                "type": "DATA",
                "data": ULIST
            }
            serv.sendto(pickle.dumps(dat), addr)
            
    except:
        pass
        
serv.close()
