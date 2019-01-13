#!/usr/bin/python3

import argparse
import os
import random

import helpers
import tornado.ioloop
import tornado.web
from connections import ConnectionsHandler
from constants import *
from events import EventsHandlerHTTP, EventsHandlerSSE
from tornado.locks import Event
from tornado import gen
from tornadose.handlers import EventSource
from tornadose.stores import QueueStore


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Main page of the LC server")
        self.write('<a href="{0}">SNCB Linked Connections</a><br>'.format(self.reverse_url("connections", "sncb")))
        self.write('<a href="{0}">SNCB Linked Events POLLING</a><br>'.format(self.reverse_url("events_polling", "sncb")))
        self.write('<a href="{0}">SNCB Linked Events POLLING</a><br>'.format(self.reverse_url("events_sse", "sncb")))


finish = Event()
store = QueueStore()

import datetime
import dateutil
import json

def _fetch_events(last_sync_time):
    now_date = datetime.datetime.now().replace(tzinfo=None)
    try:
        target_date = dateutil.parser.parse(last_sync_time).replace(tzinfo=None)
        if target_date > now_date:
            raise ValueError("lastSyncTime must be before now")
    except ValueError:
        pass

    events = {
        "lastSyncTime": target_date.replace(tzinfo=None).isoformat() + "Z",
        "@graph": []
    }

    # Read pseudorandom events JSON-LD file
    with open("events/sncb.jsonld", "r") as json_file:
        json_data = json.load(json_file)

    # Ignore the date, only use the time
    target_date = target_date.replace(year=now_date.year,
                                      month=now_date.month,
                                      day=now_date.day)

    # Sort the events by timestamp and filter them based on the sync time
    json_data = sorted(json_data, key=lambda k: k["timestamp"])
    for c in json_data:
        current_date = dateutil.parser.parse(c["timestamp"]).replace(year=now_date.year,
                                                                     month=now_date.month,
                                                                     day=now_date.day,
                                                                     tzinfo=None)
        if target_date <= current_date <= now_date:
            events["@graph"].append(c)

    return events


@gen.coroutine
def generate_sequence():
    lastSyncTime = str(datetime.datetime.now())
    while True:
        e = _fetch_events(lastSyncTime)
        if len(e["@graph"]) > 0:
            print("Found {0} events".format(len(e["@graph"])))
            store.submit(e)
            lastSyncTime = str(datetime.datetime.now())
        yield gen.sleep(1)
        if finish.is_set():
            break

@gen.coroutine
def main():
    # Commandline configuration
    parser = argparse.ArgumentParser(
        description="Linked Connections Server Faker, test your Linked Connections application in a reproducible environment.")
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

    # Generate connections and events
    helpers.fetch_connections()
    helpers.generate_pseudorandom_events(number_of_events, additional_event_time, max_delay, step_delay)

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

    # Configure the Tornado server and run it
    app = tornado.web.Application([
        tornado.web.url(r"/",
                        MainHandler),
        tornado.web.url(r"/([a-z]+)/connections",
                        ConnectionsHandler,
                        dict(supported_agencies=SUPPORTED_AGENCIES),
                        name="connections"),
        tornado.web.url(r"/([a-z]+)/events/poll",
                        EventsHandlerHTTP,
                        dict(supported_agencies=SUPPORTED_AGENCIES),
                        name="events_polling"),
        tornado.web.url(r"/([a-z]+)/events/sse",
                        EventsHandlerSSE,
                        dict(supported_agencies=SUPPORTED_AGENCIES),
                        name="events_sse"),
        tornado.web.url(r"/sse", EventSource, {"store": store})
    ])
    app.listen(port)
    yield generate_sequence()


if __name__ == "__main__":
    tornado.ioloop.IOLoop.instance().run_sync(main)

