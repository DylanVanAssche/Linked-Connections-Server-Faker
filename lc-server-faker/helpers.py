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


def generate_pseudorandom_events(number_of_events, additional_event_time, max_delay,
                                 max_additional_delay, step_delay):
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
                with open(f, "r") as json_file:
                    data = json.load(json_file)

                number_of_events = random.randint(1, int(len(data["@graph"]) * 0.10)) # 10% of the connections
                print("Generating {} events from: {}".format(number_of_events, f))
                for i in range(0, number_of_events):
                    connection = random.choice(data["@graph"])

                    # Generate random generated_at_time in the further and adjust the delays
                    generated_at_time = dateutil.parser.parse(connection["departureTime"]) \
                                + datetime.timedelta(minutes=random.randint(0, additional_event_time))

                    # Ignore events that are outside our 24h window
                    if generated_at_time >= dateutil.parser.parse(STOP_TIME):
                        continue

                    # Randomly cancel some connections
                    connection_type = "Connection"
                    if random.random() > 0.99:
                        connection_type = "CanceledConnection"
                        departure_time = dateutil.parser.parse(connection["departureTime"])
                        arrival_time = dateutil.parser.parse(connection["arrivalTime"])
                    # If not canceled, calculate arrival and departure time with delays, max 1 hour departure delay
                    else:
                        departure_delay = random.randrange(0, max_delay, step_delay)
                        if random.random() >= 0.5:
                            arrival_delay = departure_delay + random.randrange(0, max_additional_delay, step_delay)
                        else:
                            arrival_delay = departure_delay - random.randrange(0, 3*60, 60)
                        departure_time = dateutil.parser.parse(connection["departureTime"])\
                                + datetime.timedelta(seconds=departure_delay)
                        arrival_time = dateutil.parser.parse(connection["arrivalTime"])\
                                + datetime.timedelta(seconds=arrival_delay)

                    # Convert to ISO format
                    generated_at_time = generated_at_time.replace(tzinfo=None).isoformat() + ".000Z"
                    departure_time = departure_time.replace(tzinfo=None).isoformat() + ".000Z"
                    arrival_time = arrival_time.replace(tzinfo=None).isoformat() + ".000Z"

                    # Create an event object
                    e = {
                        "@id": connection["@id"] + "#" + generated_at_time,
                        "@type": "Event",
                        "hydra:view": "http://localhost:8080/sncb/connections?departureTime=" + departure_time,
                        "sosa:resultTime": generated_at_time,
                        "sosa:hasResult": {
                            "@type": "sosa:hasResult",
                            "Connection": {
                                "@id": connection["@id"],
                                "@type": connection_type,
                                "departureStop": connection["departureStop"],
                                "arrivalStop": connection["arrivalStop"],
                                "departureTime": departure_time,
                                "arrivalTime": arrival_time,
                                "direction": connection["direction"],
                                "gtfs:trip": connection["gtfs:trip"],
                                "gtfs:route": connection["gtfs:route"],
                            }
                        }
                    }

                    # Some properties aren't always available
                    if "departureDelay" in connection:
                        e["departureDelay"] = departure_delay

                    if "arrivalDelay" in connection:
                        e["arrivalDelay"] = arrival_delay

                    if "gtfs:pickupType" in connection:
                        e["gtfs:pickupType"] = connection["gtfs:pickupType"]

                    if "gtfs:dropOffType" in connection:
                        e["gtfs:dropOffType"] = connection["gtfs:dropOffType"]
                    events.append(e)

            # Save all events for this file
            with open(EVENTS_FILE, "w") as json_file:
                json.dump(events, json_file)
    except Exception as e:
        raise e
        #print("Generating pseudorandom events FAILED: {0}".format(e))
        #os.rmdir("events")
