#!/usr/bin/python3

import cherrypy
import datetime
import dateutil
import json

FILE = "events/sncb.jsonld"


class Events(object):
    def __init__(self):
        self.file = FILE

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def index(self, lastSyncTime):
        now_date = datetime.datetime.now()
        try:
            target_date = dateutil.parser.parse(lastSyncTime)
            if target_date > now_date:
                raise ValueError("lastSyncTime must be before now")
        except ValueError:
            raise cherrypy.HTTPError(400, "lastSyncTime isn't a valid ISO date!")

        events = {
            "lastSyncTime": target_date.isoformat().split("+")[0] + ".000Z",
            "@graph": []
        }

        # Read pseudorandom events JSON-LD file
        with open(self.file, "r") as json_file:
            json_data = json.load(json_file)

        # Sort the events by timestamp and filter them based on the sync time
        json_data = sorted(json_data, key=lambda k: k["timestamp"])
        for c in json_data:
            current_date = dateutil.parser.parse(c["timestamp"])
            if target_date <= current_date <= now_date:
                events["@graph"].append(c)
        return events
