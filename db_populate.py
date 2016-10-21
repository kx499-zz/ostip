#!bin/python
from app import db
from app.models import Control, Level, Itype, Tlp, Source, Likelihood, Status, Destination

controls = ["Inbound", "Outbound"]
levels = ["None", "Low", "Medium", "High"]
tlps = ["White", "Green", "Amber", "Red"]
types = [["ipv4","^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"],
         ["domain", "^(?:[-A-Za-z0-9]+\.)+[A-Za-z]{2,12}$"],
         ["md5", "^[a-fA-F0-9]{32}$"],
         ["sha256", "^[A-Fa-f0-9]{64}$"],
         ["url", "^(http[s]?://(?:[-A-Za-z0-9]+\.)+[A-Za-z]{2,12}(/[^\s]+)?|(?:[-A-Za-z0-9]+\.)+[A-Za-z]{2,12}/[^\s]*)$"]]
sources = ["Feed", "Email List", "Blog"]
statuses = ["New", "Open", "Resolved"]
destinations = [["pan", "Palo Alto", "fmtPan"], ["json", "Generic Json", "fmtJson"]]

for i in controls:
    obj = Control()
    obj.name = i
    db.session.add(obj)
    db.session.commit()

for i in levels:
    obj = Level()
    obj2 = Likelihood()
    obj.name = i
    obj2.name = i
    db.session.add(obj)
    db.session.add(obj2)
    db.session.commit()


for i in tlps:
    obj = Tlp()
    obj.name = i
    db.session.add(obj)
    db.session.commit()

for i in types:
    obj = Itype(i[0], i[1])
    db.session.add(obj)
    db.session.commit()

for i in sources:
    obj = Source()
    obj.name = i
    db.session.add(obj)
    db.session.commit()

for i in statuses:
    obj = Status()
    obj.name = i
    db.session.add(obj)
    db.session.commit()

for i in destinations:
    obj = Destination()
    obj.name = i[0]
    obj.description = i[1]
    obj.formatter = i[2]
    db.session.add(obj)
    db.session.commit()

