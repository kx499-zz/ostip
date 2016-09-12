#!/usr/bin/env python
import datetime


class ResultsDict:

    def __init__(self, event_id, control, data_types):
        self.result = dict(event_id=event_id,control=control,indicators={})
        for data_type in data_types:
            self.result['indicators'].update({data_type: []})

    def new(self):
        return self.result

class LogEntry:

    def __init__(self, date, indicator, description):
        self.entry = dict(
            date=date or datetime.datetime.utcnow(),
            indicator=indicator,
            description = description)

    def new(self):
        return self.entry

