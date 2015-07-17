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

def wake_everybody_up():
    dat = {
        "type": "WAKEUP",
        "data": 0
    }
    for n, a in USERS.items():
        serv.sendto(pickle.dumps(dat), a)

def broadcast(msg, _from):
    dat = {
        "type": "MSG",
        "data": [_from, str(msg)]
    }
    for n, a in USERS.items():
        serv.sendto(pickle.dumps(dat), a)

namewidth = 21
servtext = "[SERVER]".rjust(namewidth)

while True:
    try:
        data, addr = serv.recvfrom(1024)
        msg = pickle.loads(data)

        if msg["type"] == "CONN":
            if msg["data"] not in USERS.keys():
                USERS[msg["data"]] = addr
                info = "%s has joined the party." % msg["data"]

                print(servtext + ": " + info)
                broadcast(info, "[SERVER]")
            else:
                dat = {
                    "type": "ERR_FATAL",
                    "data": servtext+": The name \"%s\" is already taken." % msg["data"]
                }
                serv.sendto(pickle.dumps(dat), addr)
                
        elif msg["type"] == "DISCONN":
            del USERS[msg["data"]]
            info = "%s doesn't want to party anymore." % msg["data"]
            
            print(servtext + ": " + info)
            broadcast(info, "[SERVER]")
            
        elif msg["type"] == "CHATMSG":
            _from, message = msg["data"]
            info = "%s: %s" % (_from.rjust(namewidth), message)

            print(info)
            broadcast(message, _from)
            
        elif msg["type"] == "GETUSERLIST":
            ULIST = list(USERS.keys())
            dat = {
                "type": "MSG",
                "data": ["[SERVER]", "Users: " + ",".join(ULIST)]
            }
            serv.sendto(pickle.dumps(dat), addr)

        elif msg["type"] == "HEYWAKEUP":
            print(msg["data"] + " tried to get attention.")
            wake_everybody_up()
    except:
        pass
        
serv.close()
