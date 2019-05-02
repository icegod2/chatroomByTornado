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
        PeriodicCallback(self._keepalive,2000).start()
   
    def start(self):
        try:
            self.connect()
            self.ioloop.start()

        except Exception, e:
            logging.DEBUG("{} => {}".format(self.__class__.__name__, e))

    def alive(self):
        if self.connecting:
            return True
        else:
            return False

    def _keepalive(self):
        if hasattr(self.ws, 'write_message'):
            self.connecting = True
        else:
            self.connecting = False
            self.connect()


    @gen.coroutine
    def connect(self):
        try:
            self.ws = yield websocket_connect(self.url)
            self.run()
        except Exception, e:
            pass


    @gen.coroutine
    def run(self):
        while True:
            msg = yield self.ws.read_message()
            if len(msg) > 0:
                self.q.put(msg)

    def get(self):
        msg = ""
        if not self.q.empty():
            msg=self.q.get()
        
        return msg

    def send(self, msg):
        self.ws.write_message(msg, binary=True)


if __name__ == "__main__":
    pass





