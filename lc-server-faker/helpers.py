#!/usr/bin/python3

import dateutil.parser
import datetime
import requests
import json
import os
import random
from urllib.parse import urlparse, parse_qs
from constants import *


def fetch_connections(server_url):
    try:
        url = FRAGMENT_URL
        if not os.path.exists("connections"):
            os.mkdir("connections")

            while True:
                print("Downloading: " + url)
                fragment = requests.get(url).json()

                # Find next fragment
                url = fragment["hydra:next"]
                departure_time_query = parse_qs(urlparse(url).query)["departureTime"][0]
                date = dateutil.parser.parse(departure_time_query)

                # Fix hydra navigation
                fragment["hydra:next"] = fragment["hydra:next"].replace("https://graph.irail.be",
                                                                        server_url)
                fragment["hydra:previous"] = fragment["hydra:previous"].replace("https://graph.irail.be",
                                                                        server_url)

                # Save fragment
                departure_time_query = parse_qs(urlparse(fragment['@id']).query)["departureTime"][0]
                with open("connections/" + departure_time_query + ".jsonld", "w") as json_file:
                    json.dump(fragment, json_file)

                if date >= dateutil.parser.parse(STOP_TIME):
                    break
    except Exception as e:
        print("Generating connections FAILED: {0}".format(e))
        os.rmdir("connections")


def generate_pseudorandom_events(number_of_events, additional_event_time, max_delay, step_delay):
    try:
        if not os.path.exists("events"):
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

                for i in range(0, random.randint(0, number_of_events)):
                    connection = random.choice(data["@graph"])

                    # Generate random timestamp in the further and adjust the delays
                    timestamp = dateutil.parser.parse(connection["departureTime"]) \
                                + datetime.timedelta(minutes=random.randint(0, additional_event_time))

                    # Ignore events that are outside our 24h window
                    if timestamp >= dateutil.parser.parse(STOP_TIME):
                        continue

                    timestamp = timestamp.replace(tzinfo=None).isoformat() + "Z"

                    # Create an event object
                    e = {
                        "timestamp": timestamp,
                        "connectionURI": connection["@id"]
                    }
                    print("Connection #{0}: {1}".format(i, e))
                    events.append(e)

            # Save all events for this file
            with open(EVENTS_FILE, "w") as json_file:
                json.dump(events, json_file)
    except Exception as e:
        print("Generating pseudorandom events FAILED: {0}".format(e))
        os.rmdir("events")
