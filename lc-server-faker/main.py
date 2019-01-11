#!/usr/bin/python3

import cherrypy
import requests
import os
import dateutil
import datetime
import json
import random
import argparse
from urllib.parse import urlparse, parse_qs
from agency import Agency
from connections import Connections
from events import Events
from constants import EVENTS_FILE, FRAGMENT_URL, STOP_TIME, NUMBER_OF_EVENTS, MAX_DELAY, STEP_DELAY, ADDITIONAL_EVENT_TIME, PORT


class LCServer(object):
    def __init__(self, port, number_of_events, max_delay, step_delay, additional_event_time):
        self.port = port
        self.number_of_events = number_of_events
        self.max_delay = max_delay
        self.step_delay = step_delay
        self.additional_event_time = additional_event_time

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
            url = FRAGMENT_URL
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

                for i in range(0, random.randint(0, self.number_of_events)):
                    connection = random.choice(data["@graph"])

                    # Generate random timestamp in the further and adjust the delays
                    timestamp = dateutil.parser.parse(connection["departureTime"]) \
                                + datetime.timedelta(minutes=random.randint(0, self.additional_event_time))

                    # Ignore events that are outside our 24h window
                    if timestamp >= dateutil.parser.parse(STOP_TIME):
                        continue

                    timestamp = timestamp.replace(tzinfo=None).isoformat() + "Z"
                    connection["departureDelay"] = connection.get("departureDelay", 0) \
                                                   + random.randrange(0, self.max_delay, self.step_delay)
                    connection["arrivalDelay"] = connection.get("arrivalDelay", 0) \
                                                 + random.randrange(0, self.max_delay, self.step_delay)

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
    # Commandline configuration
    parser = argparse.ArgumentParser(description="Linked Connections Server Faker, test your Linked Connections application in a reproducible environment.")
    parser.add_argument("-p", "--port",
                        default=PORT,
                        type=int,
                        help="Set the HTTP port of the server.")
    parser.add_argument("-noe", "--numberofevents",
                        default=NUMBER_OF_EVENTS,
                        type=int,
                        help="Change the number of generated events for each fragment.")
    parser.add_argument("-md", "--maxdelay",
                        default=MAX_DELAY,
                        type=int,
                        help="The maximum amount of delays that can be added to the connection.")
    parser.add_argument("-sd", "--stepdelay",
                        default=STEP_DELAY,
                        type=int,
                        help="The size of the steps to generate delays.")
    parser.add_argument("-aet", "--additionaleventtime",
                        default=ADDITIONAL_EVENT_TIME,
                        type=int,
                        help="Additional event time which is added to the connection.")
    parser.add_argument("-c", "--clean",
                        help="Clean up data and download a fresh dataset.")
    args = parser.parse_args()
    port = args.port
    number_of_events = args.numberofevents
    max_delay = args.maxdelay
    step_delay = args.stepdelay
    additional_event_time = args.additionaleventtime
    if hasattr(argparse, "clean"):
        os.rmdir("connections")
        os.rmdir("events")

    # Print configuration
    print("=" * 80)
    print("SERVER CONFIGURATION")
    print("-" * 80)
    print("HTTP port: {0}".format(port))
    print("Number of events for each fragment: {0}".format(number_of_events))
    print("Max delay (seconds): {0}".format(max_delay))
    print("Step delay (seconds): {0}".format(step_delay))
    print("Additional event time (minutes): {0}".format(additional_event_time))
    print("=" * 80)

    # Configure server and launch it
    cherrypy.config.update({"server.socket_port": port})
    cherrypy.config.update({"tools.gzip.on": True})
    cherrypy.quickstart(LCServer(port, number_of_events, max_delay, step_delay, additional_event_time))
