#!/usr/bin/env python
# -*- coding: utf-8 -*-

import Tkinter as tk
import tkMessageBox
import ScrolledText
import wsClient
import time
import Queue
import threading, signal  
import random
import json
import argparse
import os
import logging
import sys

global client
global app
global q
global args


class Chatroom(tk.Tk):
    def __init__(self, q):
        tk.Tk.__init__(self)
        self.title(args.handle)
        self.q = q
        self.username = ""
        self.askNameWidgets()
        self.stat = "init"
        self.timeout = 0

    def askNameWidgets(self):
        self.geometry('280x80+240+120')
        self.resizable(0, 0)

        self.askNameFrame = tk.Frame(self)
        self.askNameFrame.pack(fill=tk.BOTH, expand=True)

        self.label = tk.Label(self.askNameFrame, text='Welcome', width=15, height=2)
        self.label.pack(fill=tk.BOTH, expand=True, side=tk.TOP, ipady=3,padx=5, pady=5)

        self.entry = tk.Entry(self.askNameFrame, relief=tk.SUNKEN, width=15)
        self.entry.pack(side=tk.LEFT,fill=tk.X, expand=True, padx=5, pady=5)
        self.entry.focus_set()

        self.clear = tk.Button(self.askNameFrame, relief=tk.RAISED)
        self.clear["text"] = "Clear"
        self.clear["fg"]   = "red"
        self.clear["command"] =  lambda : self.entry.delete(0, 'end')
        self.clear.pack(fill=tk.X, side=tk.LEFT, pady=5, padx=5)

        self.join = tk.Button(self.askNameFrame, relief=tk.RAISED)
        self.join["text"] = "Join"
        self.join["fg"]   = "black"
        self.join["command"] =  self._startChat
        self.join.pack(fill=tk.X, side=tk.LEFT, pady=5, padx=5)


    def waitForConnectWidgets(self):
        self.geometry('240x80+240+120')
        self.resizable(0, 0)
        
        self.waitForConnectFrame = tk.Frame(self)
        self.waitForConnectFrame.pack(fill=tk.BOTH, expand=True)

        host = "Connecting to {}:{}".format(args.host, args.port)
        self.label = tk.Label(self.waitForConnectFrame, text=host, width=15, height=2)
        self.label.pack(fill=tk.BOTH, expand=True, side=tk.TOP, ipady=3,padx=5, pady=5)


        self.cancel = tk.Button(self.waitForConnectFrame, relief=tk.RAISED)
        self.cancel["text"] = "Cancel"
        self.cancel["fg"]   = "red"
        self.cancel["command"] =  self.destroy
        self.cancel.pack(fill=tk.X, side=tk.TOP, pady=5, padx=5)

    def _checkifConnect(self):
        if self.timeout == 0:
            logging.warning("Connect to {}:{} timeout".format(args.host, args.port))
            tkMessageBox.showwarning("Chatroom", "Connect timeout")
            self.destroy()            
            return
   
        if hasattr(client, 'alive') and client.alive():
            self.waitForConnectFrame.destroy()
            self.chatWidgets()
        else:
            self.timeout -= 1
            self.after(1000, self._checkifConnect)


    def _startChat(self):
        name = self.entry.get()
        isConnectOK = False
        if len(name) < 1:
            tkMessageBox.showwarning("Chatroom", "please give a name")
        else:
            self.username = name
            self.askNameFrame.destroy()
            self.waitForConnectWidgets()
            self.after(3000, self._checkifConnect)
            self.timeout = 10


    def chatWidgets(self):
        self.geometry('600x400+240+120')
        self.resizable(1, 1)
        self.minsize(width=360, height= 400)

        self.chatframe = tk.Frame(self)
        self.chatframe.pack(fill=tk.BOTH, expand=True)

        self.msgArea = ScrolledText.ScrolledText(self.chatframe,wrap=tk.WORD, font = "{Times new Roman} 10")
        for e in ["<Key>","<Tab>","<Delete>", "<BackSpace>"]:
            self.bind_class("Text", e, lambda e: None)
        self.msgArea.pack(fill=tk.BOTH, expand=True, padx=5)

        self.entry = tk.Entry(self.chatframe, relief=tk.SUNKEN)
        self.entry.bind('<Return>', lambda e: self._pushmsg())
        self.entry.pack(fill=tk.X, expand=True, side=tk.LEFT, padx=5, pady=5)
        
        self.send = tk.Button(self.chatframe, relief=tk.RAISED)
        self.send["text"] = "Send"
        self.send["fg"]   = "black"
        self.send["command"] = self._pushmsg
        self.send.pack(fill=tk.X, side=tk.LEFT, pady=5)

        self.quit = tk.Button(self.chatframe, relief=tk.RAISED)
        self.quit["text"] = "QUIT"
        self.quit["fg"]   = "red"
        self.quit["command"] =  self.destroy
        self.quit.pack(fill=tk.X, side=tk.LEFT, pady=5)

        self.stat = "chat"
  

    def _pushmsg(self):
        msg = u"{:s}: {:s}".format(self.username, self.entry.get().rstrip())
        self.q.put(msg)
        self.entry.delete(0, 'end')

    def update_msgArea(self, msg):
        self.msgArea.insert(tk.END, msg)  
        self.msgArea.see(tk.END) 



def checkRecvMsgEvent():
    global client
    global app

    while True:
        try:
          client
        except NameError:
          time.sleep(2)
        else:
          break

    while not client.alive():
        time.sleep(1)

    while app.stat != "chat":
        time.sleep(1)

    sendDisconnectStringDone = False
    while True:
        if client.alive() :
            sendDisconnectStringDone = False
            msg = client.get()
            while len(msg) > 0:
                logging.debug("Recv:{}".format(msg))
                msg = msg.rstrip() + '\n'
                app.update_msgArea(msg)
                msg = client.get() 
            time.sleep(0.1)
        else:
            if not sendDisconnectStringDone:
                app.update_msgArea(u"Can't connect to Server\n")
                sendDisconnectStringDone = True
            time.sleep(2)


def Test_SendMsgEvent():
    global client
    global app

    isSendHelloDone = False 

    q = Queue.Queue(maxsize=100)
    
    while True:
        try:
          client
        except NameError:
          pass
          time.sleep(2)
        else:
          break


    while not client.alive():
        time.sleep(2)


    cnt = 0
    hello = {
        "type": "hello",
        "channel": "",
        "username": app.username,
        "timestamp": "",
        "message": ""
    }

    message = {
        "type": "message",
        "channel": "",
        "username": app.username,
        "timestamp": "",
        "message": ""
    }

    while True:
        if q.full():
            time.sleep(random.randint(2,5)) 
            continue

        if client.alive():
            if not isSendHelloDone:
                send_data = hello
                isSendHelloDone = True
            else:
                send_data = message
                send_data['message'] = u"{}:hello {}".format(app.username, cnt)
                cnt += 1

            send_data['channel'] = args.handle
            send_data['timestamp'] = int(time.time())
            
            q.put(send_data)
            while not q.empty():
                msg = q.get()
                logging.debug("Send:{}".format(msg))
                try:
                    client.send(json.dumps(msg))
                except Exception, e:
                    pass
        else:
            logging.debug("Disconnect with Server, change to hello packge")
            isSendHelloDone = False
        
        time.sleep(random.randint(2,5)) 


def checkSendMsgEvent():
    global client
    global app
    isSendHelloDone = False 
    previous_send_msg = ""

    while True:
        try:
          client
        except NameError:
          pass
          time.sleep(2)
        else:
          break


    while not client.alive():
        time.sleep(1)


    hello = {
        "type": "hello",
        "channel": args.handle,
        "username": app.username,
        "timestamp": "",
        "message": ""
    }

    message = {
        "type": "message",
        "channel": args.handle,
        "username": app.username,
        "timestamp": "",
        "message": ""
    }

    while True:
        if not client.alive():
            isSendHelloDone = False
            time.sleep(2)
            continue

        if not isSendHelloDone:
            send_data = hello
            send_data['timestamp'] = int(time.time())
            try:
                client.send(json.dumps(send_data))
                logging.debug("Send:{}".format(send_data))
                isSendHelloDone = True
            except Exception, e:
                logging.debug("catch checkSendMsgEvent exception")
 
        else:
            send_data = message
            while not q.empty():
                if client.alive():
                    send_data['timestamp'] = int(time.time())
                    if previous_send_msg:
                        msg= previous_send_msg
                    else:
                        msg = q.get().rstrip()

                    send_data['message'] = msg
                    try:
                        client.send(json.dumps(send_data))
                        previous_send_msg = ""
                    except Exception, e:
                        isSendHelloDone = False
                        previous_send_msg = msg                   
                else:
                    isSendHelloDone = False
                    break
        time.sleep(1)

 
def create_connect(url):
    global client
    global app
    global args

    while len(app.username) < 1:
        time.sleep(1) 

    logging.debug("{} start to connecting {}:{} channel:{}".format(app.username, 
                                                                  args.host, 
                                                                  args.port, 
                                                                  args.handle))
    client = wsClient.wsClient(url)
    client.start() 




if __name__ == "__main__":
    global app
    global q

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", help="host ip", required=True, type=str)
    parser.add_argument("--port", help="run on the given port", required=True, type=int)
    parser.add_argument("--handle", help="chat channel", required=True, type=str)
    parser.add_argument("--debug", help="debug mode", required=False, type=int)
    args = parser.parse_args()

    fn = "client_{}.log".format(os.getpid())
    if args.debug:
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(asctime)s - %(levelname)s : %(message)s')
    else:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s : %(message)s', filename=fn, filemode='w')

    q= Queue.Queue()
    app = Chatroom(q)
    address = "ws://{}:{}".format(args.host, args.port)
    t = threading.Thread(target = create_connect, args=[address,])
    t.setDaemon(True)
    t.start()

    
    t = threading.Thread(target = checkRecvMsgEvent)
    t.setDaemon(True)
    t.start()


    #t = threading.Thread(target = checkSendMsgEvent)
    t = threading.Thread(target = Test_SendMsgEvent)
    t.setDaemon(True)
    t.start()

    app.mainloop()






  

