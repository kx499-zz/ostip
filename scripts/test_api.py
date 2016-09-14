#!../bin/python
import requests
json = {
  "event_id": 3,
  "control": "Inbound",
  "data_type": "ipv4",
  "pending": True,
  "data": [ ["6.1.1.4", "test ip"], ["6.1.1.8", "test ip"], ["6.1.1.9", "test ip"], ["6.1.1.10", "test ip"] ]
}

res = requests.post('http://localhost:5000/api/indicator/bulk_add', json=json)
if res.ok:
    print res.json()
