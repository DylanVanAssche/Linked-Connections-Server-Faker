#!/usr/bin/python3

import cherrypy
import os
import dateutil
import json

FILE = "events/sncb.jsonld"


class Events(object):
    def __init__(self):
        self.file = FILE

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def index(self, lastSyncTime):
        events = {
            "lastSyncTime": lastSyncTime,
            "@graph": []
        }
        target_date = dateutil.parser.parse(lastSyncTime)

        # Read pseudorandom events JSON-LD file
        with open(self.file, "r") as json_file:
            json_data = json.load(json_file)

        # Sort the events by timestamp and filter them based on the sync time
        json_data = sorted(json_data, key=lambda k: k["timestamp"])
        for c in json_data:
            current_date = dateutil.parser.parse(c["timestamp"])
            if current_date >= target_date:
                events["@graph"].append(c)
        return events
