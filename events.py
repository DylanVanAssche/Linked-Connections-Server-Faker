#!/usr/bin/python3

import cherrypy


class Events(object):
    @cherrypy.expose
    def index(self):
        return "List of events"
