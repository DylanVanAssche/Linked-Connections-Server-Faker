#!/usr/bin/python3

import cherrypy
import os
import dateutil
import json

class Events(object):
    def __init__(self):
        self.file = "events/events.jsonld"

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def index(self, syncTime):
        events = {
            "syncTime": syncTime,
            "@graph": []
        }

        target_date = dateutil.parser.parse(syncTime)

        with open(self.file, "r") as json_file:
            json_data = json.load(json_file)

        json_data = sorted(json_data, key=lambda k: k["timestamp"])
        for c in json_data:
            current_date = dateutil.parser.parse(c["timestamp"])
            if current_date <= target_date:
                events["@graph"].append(c)
        return events
