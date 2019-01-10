#!/usr/bin/python3

import cherrypy
from agency import Agency
from connections import Connections
from events import Events


class LCServer(object):
    def __init__(self):
        self.sncb = SNCB()

    @cherrypy.expose
    def index(self):
        return "LCServer"


class SNCB(Agency):
    def __init__(self):
        self.connections = Connections()
        self.events = Events()
        self.name = "SNCB"

    @cherrypy.expose
    def index(self):
        return self.name + " agency"


if __name__ == "__main__":
    cherrypy.quickstart(LCServer())
