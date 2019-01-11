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

URL = "https://graph.irail.be/sncb/connections?departureTime={0}".format(datetime.datetime.utcnow()
                                                                 .replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
                                                                 .isoformat() + ".000Z")
STOP_TIME = (datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
            + datetime.timedelta(days=1)).isoformat() + ".000Z"
EVENTS_FILE = "events/sncb.jsonld"
NUMBER_OF_EVENTS = 10
MAX_DELAY = 600
STEP_DELAY = 60
ADDITIONAL_EVENT_TIME = 120


class LCServer(object):
    def __init__(self):
        # Download a full day of Linked Connections data if needed
        if not os.path.isdir("connections"):
            print("Downloading a complete day of Linked Connections ...")
            self.fetch_connections()
        else:
            print("Connections are already generated")

        # Create events folder if needed
        if not os.path.isdir("events"):
            print("Generating pseudorandom events ...")
            self.generate_pseudorandom_events()
        else:
            print("Pseudorandom events are already generated")

        self.sncb = SNCB()

    def fetch_connections(self):
        try:
            url = URL
            os.mkdir("connections")

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
        except Exception as e:
            print("Generating connections FAILED: " + str(e))
            os.rmdir("connections")

    def generate_pseudorandom_events(self):
        try:
            os.mkdir("events")
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

                for i in range(0, random.randint(0, NUMBER_OF_EVENTS)):
                    connection = random.choice(data["@graph"])

                    # Generate random timestamp in the further and adjust the delays
                    timestamp = dateutil.parser.parse(connection["departureTime"]) \
                                + datetime.timedelta(minutes=random.randint(0, ADDITIONAL_EVENT_TIME))

                    # Ignore events that are outside our 24h window
                    if timestamp >= dateutil.parser.parse(STOP_TIME):
                        continue

                    timestamp = timestamp.replace(tzinfo=None).isoformat() + ".000Z"
                    connection["departureDelay"] = connection.get("departureDelay", 0) \
                                                   + random.randrange(0, MAX_DELAY, STEP_DELAY)
                    connection["arrivalDelay"] = connection.get("arrivalDelay", 0) \
                                                 + random.randrange(0, MAX_DELAY, STEP_DELAY)

                    # Create an event object
                    e = {
                        "timestamp": timestamp,
                        "connection": connection
                    }
                    print("Connection #{0}: {1}".format(i, e))
                    events.append(e)

            # Save all events for this file
            with open(EVENTS_FILE, "w") as json_file:
                json.dump(events, json_file)
        except Exception as e:
            print("Generating pseudorandom events FAILED: " + str(e))
            os.rmdir("events")

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
