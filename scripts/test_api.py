#!../bin/python
import requests



indicator_json = {
  "event_id": 3,
  "control": "Inbound",
  "data_type": "ipv4",
  "pending": True,
  "data": [ ["6.1.1.4", "test ip"], ["6.1.1.8", "test ip"], ["6.1.1.9", "test ip"], ["6.1.1.10", "test ip"] ]
}

event_json = {
  "name": "Test API event",
  "details": "Some text",
  "confidence": 90,
  "source": "Blog",
  "tlp": "Amber",
  "impact": "Low",
  "likelihood":"Low"
}


ind_get_json = {
    "fields": [{
        "field": "confidence",  # confidence, ioc, last_seen, first_seen
        "operator": "Some text",  # eq, lt, gt, like
        "val": 90
    }],
    "operator": "or", #or, and
    "pending": True
}

res = requests.post('http://localhost:5000/api/indicator/bulk_add', json=indicator_json)
print 'Indicator Add Results:'
if res.ok:
    print res.json()
else:
    print 'Something bad happened'

res = requests.post('http://localhost:5000/api/event/add', json=event_json)
print 'Event Add Results:'
if res.ok:
    print res.json()
else:
    print 'Something bad happened'
