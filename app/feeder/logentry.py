#!/usr/bin/env python
import datetime


class LogEntry:

    def __init__(self, event_id, data_type, indicator, control, description):
        self.entry = dict(
            date=datetime.datetime.utcnow(),
            indicator=indicator,
            data_type=data_type,
            event_id=int(event_id),
            control=control,
            description = description)

    def new(self):
        return self.entry

