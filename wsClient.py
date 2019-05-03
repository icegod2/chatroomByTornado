#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tornado.ioloop import IOLoop, PeriodicCallback
from tornado import gen
from tornado.websocket import websocket_connect
import sys
import threading, signal  
import time           
import Queue
import random
import logging

class wsClient(object):
    def __init__(self, url):
        self.url = url
        self.ws = None
        self.q = Queue.Queue()
        self.ioloop = IOLoop.instance()
        self.connecting = False
        self.doingConnect = False
        PeriodicCallback(self._keepalive,5000).start()

    def start(self):
        try:
            self.connect()
            self.ioloop.start()
        except Exception:
            pass

    def alive(self):
        if self.connecting:
            return True
        else:
            return False

    def _keepalive(self): 
        if not self.connecting:
            if not self.doingConnect: 
                self.connect()
            else:
                if hasattr(self.ws, 'write_message'):
                    self.connecting = True
                else:
                    self.connecting = False

    @gen.coroutine
    def connect(self):
        try:
            self.doingConnect = True
            self.ws = yield websocket_connect(self.url)
            self.connecting = True
            self.doingConnect = False
            self.run()
        except Exception:
            self.connecting = False
            self.doingConnect = False


    @gen.coroutine
    def run(self):
        while True:
            try:
                msg = yield self.ws.read_message()
                if len(msg) > 0:
                    self.q.put(msg)
            except Exception:
                self.connecting = False

    def get(self):
        msg = ""
        if self.q.empty():
            pass
        else:
            msg=self.q.get()
        
        return msg

    def send(self, msg):
        try:
            self.ws.write_message(msg, binary=True)
        except Exception:
            self.connecting = False

if __name__ == "__main__":
    pass

