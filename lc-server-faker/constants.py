#!/usr/bin/python3

import datetime

FRAGMENT_URL = "https://graph.irail.be/sncb/connections?departureTime={0}".format(datetime.datetime.utcnow()
                                                                 .replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
                                                                 .isoformat() + ".000Z")
STOP_TIME = (datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
            + datetime.timedelta(days=1)).isoformat() + "Z"
EVENTS_FILE = "events/sncb.jsonld"
NUMBER_OF_EVENTS = 10
MAX_DELAY = 600
STEP_DELAY = 60
MAX_ADDITONAL_DELAY = 180
ADDITIONAL_EVENT_TIME = 120
PORT = 8080
SUPPORTED_AGENCIES = ["sncb"]
