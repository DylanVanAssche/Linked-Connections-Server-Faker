#!/usr/bin/python3

import cherrypy
import requests
import os
import dateutil.parser
import json
from urllib.parse import urlparse, parse_qs

from agency import Agency
from connections import Connections
from events import Events

URL = "https://graph.irail.be/sncb/connections?departureTime=2019-01-10T00:00:00.000Z"
STOP_TIME = "2019-01-11T00:00:00.000Z"

class LCServer(object):
    def __init__(self):
        self.sncb = SNCB()

        # Download a full day of Linked Connections data if needed
        if not os.path.isdir("data"):
            os.mkdir("data")
            self.fetch_fragments()

        else:
            # Loop through each fragment and see if they are all there
            pass

    def fetch_fragments(self):
        url = URL

        while True:
            print("Downloading: " + url)
            fragment = requests.get(url).json()

            # Save fragment
            departure_time_query = parse_qs(urlparse(url).query)["departureTime"][0];
            with open("data/" + departure_time_query + ".jsonld", "w") as json_file:
                json.dump(fragment, json_file)

            # Find next fragment
            url = fragment["hydra:next"]
            departure_time_query = parse_qs(urlparse(url).query)["departureTime"][0];
            date = dateutil.parser.parse(departure_time_query)
            if date >= dateutil.parser.parse(STOP_TIME):
                break

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
