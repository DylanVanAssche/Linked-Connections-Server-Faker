#!/usr/bin/python3

import argparse
import os
import datetime
import helpers
import tornado.ioloop
import tornado.web
import shutil
from connections import ConnectionsHandler
from constants import *
from events import EventsHandlerHTTP, EventsHandlerSSE, EventsHandlerWS, EventsHandlerNew, EventsHandlerStatic


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        # Landing page
        self.render("assets/index.html")


def main():
    # Commandline configuration
    parser = argparse.ArgumentParser(
                        description="Linked Connections Server Faker, test your Linked Connections application in a \
                        reproducible environment.")
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
                        help="The size of the step to generate delays.")
    parser.add_argument("-aet", "--additionaleventtime",
                        default=ADDITIONAL_EVENT_TIME,
                        type=int,
                        help="Additional event time which is added to the connection.")
    parser.add_argument("-mad", "--maxadditionaldelay",
                        default=MAX_ADDITONAL_DELAY,
                        type=int,
                        help="Additional delay time which is added to the connection.")
    parser.add_argument("-c", "--clean", action="store_true",
                        help="Clean up data and download a fresh dataset.")
    args = parser.parse_args()
    port = args.port
    number_of_events = args.numberofevents
    max_delay = args.maxdelay
    max_additional_delay = args.maxadditionaldelay
    step_delay = args.stepdelay
    additional_event_time = args.additionaleventtime
    if args.clean:
        print("Removing old data...")
        shutil.rmtree("connections")
        shutil.rmtree("events")

    # Generate connections and events
    helpers.fetch_connections("http://localhost:8080")
    helpers.generate_pseudorandom_events(number_of_events, additional_event_time, max_delay,
                                         max_additional_delay, step_delay)

    # Start updater for static fragment by creating a handler for these static pages
    EventsHandlerStatic()

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
        tornado.web.url(r"/([a-z]+)/events",
                        EventsHandlerHTTP,
                        dict(supported_agencies=SUPPORTED_AGENCIES),
                        name="events_polling"),
        tornado.web.url(r"/([a-z]+)/events/sse",
                        EventsHandlerSSE,
                        dict(supported_agencies=SUPPORTED_AGENCIES),
                        name="events_sse"),
        tornado.web.url(r"/([a-z]+)/events/ws",
                        EventsHandlerWS,
                        dict(supported_agencies=SUPPORTED_AGENCIES),
                        name="events_ws"),
        tornado.web.url(r"/([a-z]+)/events/new",
                        EventsHandlerNew,
                        dict(supported_agencies=SUPPORTED_AGENCIES),
                        name="events_new")
    ])
    app.listen(port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()

