#!/usr/bin/python3

import cherrypy
import requests
import os
import dateutil
import datetime
import json
import random
from urllib.parse import urlparse, parse_qs

from agency import Agency
from connections import Connections
from events import Events

URL = "https://graph.irail.be/sncb/connections?departureTime=2019-01-10T00:00:00.000Z"
STOP_TIME = "2019-01-11T00:00:00.000Z"

class LCServer(object):
    def __init__(self):
        # Download a full day of Linked Connections data if needed
        if not os.path.isdir("connections"):
            print("Downloading a complete day of Linked Connections ...")
            os.mkdir("connections")
            self.fetch_fragments()
        else:
            print("Connections are already generated")
            # Loop through each fragment and see if they are all there
            pass

        # Create events folder if needed
        if not os.path.isdir("events"):
            print("Generating pseudorandom events ...")
            os.mkdir("events")
            self.generate_pseudorandom_events()
        else:
            print("Pseudorandom events are already generated")

        self.sncb = SNCB()

    def fetch_fragments(self):
        url = URL

        while True:
            print("Downloading: " + url)
            fragment = requests.get(url).json()

            # Save fragment
            departure_time_query = parse_qs(urlparse(url).query)["departureTime"][0]
            with open("connections/" + departure_time_query + ".jsonld", "w") as json_file:
                json.dump(fragment, json_file)

            # Find next fragment
            url = fragment["hydra:next"]
            departure_time_query = parse_qs(urlparse(url).query)["departureTime"][0]
            date = dateutil.parser.parse(departure_time_query)
            if date >= dateutil.parser.parse(STOP_TIME):
                break

    def generate_pseudorandom_events(self):
        # Find all connections files
        files = []
        for f in os.listdir("connections"):
            path = os.path.join("connections", f)
            if os.path.isfile(path):
                files.append(path)
        files.sort()

        # Generate a random number of events for each file
        events = []
        for f in files:
            print(f)
            with open(f, "r") as json_file:
                data = json.load(json_file)

            for i in range(0, random.randint(0, 10)):
                connection = random.choice(data["@graph"])

                # Generate random timestamp in the futher and adjust the delays
                timestamp = dateutil.parser.parse(connection["departureTime"]) \
                            + datetime.timedelta(minutes=random.randint(0, 60*12))
                connection["departureDelay"] = random.randrange(0, 600, 60)
                connection["arrivalDelay"] = random.randrange(0, 600, 60)

                # Create an event object
                e = {
                    "timestamp": timestamp.isoformat(),
                    "connection": connection
                }
                print("Connection #{0}: {1}".format(i, e))
                events.append(e)

        # Save all events for this file
        with open("events/events.jsonld", "w") as json_file:
            json.dump(events, json_file)

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
