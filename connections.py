#!/usr/bin/python3

import cherrypy
import dateutil.parser
import json
import os

class Connections(object):
    def __init__(self):
        self.files = []
        for f in os.listdir("connections"):
            path = os.path.join("connections", f)
            if os.path.isfile(path):
                self.files.append(path)
        self.files.sort()

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def index(self, departureTime):
        target_date = dateutil.parser.parse(departureTime)
        target_file = None

        for i in range(0, len(self.files)-1):
            current_file = self.files[i]
            next_file = self.files[i+1]
            current_date = dateutil.parser.parse(os.path.basename(os.path.splitext(current_file)[0]))
            next_date = dateutil.parser.parse(os.path.basename(os.path.splitext(next_file)[0]))

            if current_date <= target_date < next_date:
                print("Target date: {0}, between files: {1} and {2}".format(departureTime, current_file, next_file))
                target_file = current_file
                break

        with open(target_file, "r") as json_file:
            json_data = json.load(json_file)

        # Return JSON data
        return json_data
