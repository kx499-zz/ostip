#!bin/python
from app import db
from app.models import Control, Level, Itype, Tlp, Source, Likelihood, Status

controls = ["Inbound", "Outbound"]
levels = ["None", "Low", "Medium", "High"]
tlps = ["White", "Green", "Amber", "Red"]
types = ["ipv4", "domain"]
sources = ["Feed", "Email List", "Blog"]
statuses = ["New", "Open", "Resolved"]

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
    obj = Itype()
    obj.name = i
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

