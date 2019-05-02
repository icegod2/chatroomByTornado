#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import tornado.web
import tornado.websocket
from tornado.ioloop import IOLoop, PeriodicCallback
import Queue
import sys
import threading 
import time  
import json
import argparse
#from types import *


global args
global q
q_channels = {}
wsMapingChannel = []


def PublishManager():
  global q_channels

  while True:
    for c in q_channels:
        if q_channels[c].empty():
            logging.debug("PublishManager channel {} no msg wait for send".format(c)) 
        else:     
            size = q_channels[c].qsize()
            logging.debug("PublishManager polling channel {} [{} msg wait for send]".format(c, size))
            PublishByChannel(c)
    time.sleep(0.5)

def PublishByChannel(channel):
    q = q_channels[channel]
    size = q_channels[channel].qsize()

    for i in range(size):
        msg = q.get()
        logging.debug("send {} to channel {}".format(msg, channel))
        users = ChatManager.channels[channel]
        if len(msg) > 0:
            for user in users:
                try:
                    if hasattr(user['ws'], 'write_message'):
                        user['ws'].write_message(msg, binary=False)
                except Exception as e:
                    pass

                #user.write_message(u"{}.You said: " + message)


class ChatManager(tornado.websocket.WebSocketHandler):
    channels = {}
    @classmethod
    def add_user(cls, user):
        c = user['channel']
        new_user = {'username': user['username'], 'ws' : user['ws']}
        cls.channels[c].append(new_user) 
        logging.debug("add new user {} to channel {}".format(user['username'], c))
        msg = "<<---------- {} enter ---------->>".format(user['username'])
        q_channels[c].put(msg)
    @classmethod
    def remove_user(cls, websocket):
        global wsMapingChannel
        global q_channels
        channel = ""
        for d in wsMapingChannel:
            if (d['ws'] == websocket):
                channel = d['channel']
                wsMapingChannel.remove(d)
                break

        if channel:
            for user in cls.channels[channel]:
                if (user['ws'] == websocket):
                    cls.channels[channel].remove(user)
                    msg = "<<---------- {} Leave---------->>".format(user['username'])
                    q_channels[channel].put(msg)
                    



class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/", MainHandler)]
        settings = dict(debug=False)
        tornado.web.Application.__init__(self, handlers, **settings)


class MainHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        logging.debug("A client connected.")


    def on_close(self):
        logging.debug("A client disconnected")
        ChatManager.remove_user(self)

    def on_message(self, message):
        msg = json.loads(message)
        if msg['type'] == "hello":
            #logging.debug("its welcome package to {:s}".format(msg['channel'])) 
            self.handler_hello(msg)
        elif msg['type'] == "message":
            #logging.debug("its message package to {:s}".format(msg['message'])) 
            self.handler_message(msg)
        else:
            logging.warning("{} => unknown package type".format(self.__class__.__name__))

    def handler_hello(self, msg):
        global q_channels
        c = str(msg['channel'])
        name = msg['username']

        if c in q_channels:
            pass
        else:
            q_channels[c] = Queue.Queue()
            ChatManager.channels[c] = []
            logging.debug("Create new channel {}".format(c))


        user = {'username' : name, 'channel': c, 'ws' : self}
        ChatManager.add_user(user)
        wsMapingChannel.append({'channel': c, 'ws': self})


    def handler_message(self, msg):
        c = msg['channel']
        m = msg['message']

        if c in q_channels:
            q_channels[c].put(m)
        else:
            logging.warning("{} => Can't find channel {}".format(self.__class__.__name__, c))



def main():
    global q
    global q_channels
    global args

    parser = argparse.ArgumentParser()
    parser.add_argument("--bind-ip", help="bind ip", required=True, type=str)
    parser.add_argument("--bind-port", help="bind port", required=True, type=int)
    parser.add_argument("--debug", help="debug mode", required=False, type=int)
    args = parser.parse_args()


    if args.debug:
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(asctime)s - %(levelname)s : %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s : %(message)s', filename="server.log", filemode='w')

    q_channels["server"] = Queue.Queue()
    q=Queue.Queue()
    t = threading.Thread(target = PublishManager)
    t.setDaemon(True)
    t.start()

    app = Application()
    app.listen(args.bind_port,address=args.bind_ip)

    IOLoop.instance().start()


if __name__ == "__main__":
    main()