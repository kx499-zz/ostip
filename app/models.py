from sqlalchemy.orm import Session

from app import db
import datetime
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import select, func


class Event(db.Model):
    __tablename__ = "event"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True, nullable=False)
    details = db.Column(db.Text())
    created = db.Column(db.DateTime, nullable=False)
    confidence = db.Column(db.Integer, nullable=False)
    status_id = db.Column(db.Integer, db.ForeignKey('status.id'), nullable=False)
    source_id = db.Column(db.Integer, db.ForeignKey('source.id'), nullable=False)
    tlp_id = db.Column(db.Integer, db.ForeignKey('tlp.id'), nullable=False)
    impact_id = db.Column(db.Integer, db.ForeignKey('level.id'), nullable=False)
    likelihood_id = db.Column(db.Integer, db.ForeignKey('likelihood.id'), nullable=False)

    source = db.relationship('Source', foreign_keys=source_id)
    tlp = db.relationship('Tlp', foreign_keys=tlp_id)
    impact = db.relationship('Level', foreign_keys=impact_id)
    likelihood = db.relationship('Likelihood', foreign_keys=likelihood_id)
    status = db.relationship('Status', foreign_keys=status_id)

    indicators = db.relationship('Indicator', backref='event', lazy='dynamic')
    rel_events = db.relationship('Links', backref='event', lazy='dynamic')
    notes = db.relationship('Note', backref='event', lazy='dynamic')

    @hybrid_property
    def indicator_count(self):
        return self.indicators.count()

    @indicator_count.expression
    def indicator_count(cls):
        return (select([func.count(Indicator.id)]).
                where(Indicator.event_id == cls.id).
                label("indicator_count")
                )

    def __init__(self, name, details, source, tlp, impact, likelihood, confidence=50):
        self.name = name
        self.details = details
        self.confidence = confidence
        self.source = source
        self.tlp = tlp
        self.impact = impact
        self.likelihood = likelihood
        self.status = Status.query.get(1)
        self.created = datetime.datetime.utcnow()

    def as_dict(self):
        return '%s' % {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return '<Event %r>' % (self.name)


class Indicator(db.Model):
    __tablename__ = "indicator"
    id = db.Column(db.Integer, primary_key=True)
    ioc = db.Column(db.String(64), index=True, nullable=False)
    comment = db.Column(db.String(255))
    enrich = db.Column(db.String(255))
    first_seen = db.Column(db.DateTime, nullable=False)
    last_seen = db.Column(db.DateTime, index=True, nullable=False)
    pending = db.Column(db.Boolean, nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    control_id = db.Column(db.Integer, db.ForeignKey('control.id'), nullable=False)
    itype_id = db.Column(db.Integer, db.ForeignKey('itype.id'), nullable=False)

    control = db.relationship('Control', foreign_keys=control_id)
    itype = db.relationship('Itype', foreign_keys=itype_id)
    rel_indicators = db.relationship('Links', backref='indicator', lazy='dynamic')

    __table_args__ = (db.UniqueConstraint("ioc", "event_id", "itype_id", "control_id"), )

    @hybrid_property
    def rel_list(self):
        return ','.join([str(i.rel_event_id) for i in self.rel_indicators])

    def __init__(self, event_id, ioc, comment, control, itype, pending=False, enrich=None):
        self.event_id = event_id
        self.ioc = ioc
        self.comment = comment
        self.control = control
        self.itype = itype
        self.pending = pending
        self.enrich = enrich
        self.first_seen = datetime.datetime.utcnow()
        self.last_seen = datetime.datetime.utcnow()


    def as_dict(self):
        return '%s' % {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return '<Indicator %r>' % (self.ioc)


class Links(db.Model):
    __tablename__ = "links"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    indicator_id = db.Column(db.Integer, db.ForeignKey('indicator.id'), nullable=False)
    rel_event_id = db.Column(db.Integer, nullable=False)
    rel_indicator_id = db.Column(db.Integer, nullable=False)

    def __init__(self, event_id, indicator_id, rel_event_id, rel_indicator_id):
        self.event_id = event_id
        self.indicator_id = indicator_id
        self.rel_event_id = rel_event_id
        self.rel_indicator_id = rel_indicator_id

    def __repr__(self):
        return '<Links %r:%r -> %r:%r>' % (self.event_id, self.indicator_id, self.rel_event_id, self.rel_indicator_id)

class Note(db.Model):
    __tablename__ = "note"
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, nullable=False)
    details = db.Column(db.Text())
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)

    def __init__(self, event_id, details):
        self.details= details
        self.event_id = event_id
        self.created = datetime.datetime.utcnow()

    def __repr__(self):
        return '<Note %r>' % (self.details)

class Tlp(db.Model):
    __tablename__ = "tlp"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))

    def __repr__(self):
        return '<Tlp %r>' % (self.name)


class Level (db.Model):
    __tablename__ = "level"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))

    def __repr__(self):
        return '<Level %r>' % (self.name)


class Likelihood (db.Model):
    __tablename__ = "likelihood"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))

    def __repr__(self):
        return '<Level %r>' % (self.name)


class Source(db.Model):
    __tablename__ = "source"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))

    def __repr__(self):
        return '<Source %r>' % (self.name)


class Itype(db.Model):
    __tablename__ = "itype"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    regex = db.Column(db.String(255))

    def __init__(self, name, regex):
        self.name = name
        self.regex = regex

    def __repr__(self):
        return '<Itype %r>' % (self.name)


class Control(db.Model):
    __tablename__ = "control"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))

    def __repr__(self):
        return '<Control %r>' % (self.name)


class Status(db.Model):
    __tablename__ = "status"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))

    def __repr__(self):
        return '<Status %r>' % (self.name)