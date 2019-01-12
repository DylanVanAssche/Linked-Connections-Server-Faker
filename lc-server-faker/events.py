#!/usr/bin/python3

import tornado.web
import dateutil
import datetime
import json
from constants import *


class EventsHandler(tornado.web.RequestHandler):
    def initialize(self, supported_agencies):
        self.supported_agencies = supported_agencies
        self.file = EVENTS_FILE

    def get(self, agency):
        if agency in self.supported_agencies:
            last_sync_time = self.get_argument("lastSyncTime")
            self.write(self._fetch_events(last_sync_time))
        else:
            self.set_status(404)
            self.write(
                {
                    "error": "Unsupported agency: {0}".format(agency),
                    "status": 404
                }
            )

    def _fetch_events(self, last_sync_time):
        now_date = datetime.datetime.now().replace(tzinfo=None)
        try:
            target_date = dateutil.parser.parse(last_sync_time).replace(tzinfo=None)
            if target_date > now_date:
                raise ValueError("lastSyncTime must be before now")
        except ValueError:
            self.set_status(400)

        events = {
            "lastSyncTime": target_date.replace(tzinfo=None).isoformat() + "Z",
            "@graph": []
        }

        # Read pseudorandom events JSON-LD file
        with open(self.file, "r") as json_file:
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
