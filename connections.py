#!/usr/bin/python3

import cherrypy


class Connections(object):
    @cherrypy.expose
    def index(self):
        return "List of connections"
