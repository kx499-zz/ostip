from flask_wtf import Form
from wtforms import StringField, IntegerField, SelectField, BooleanField
from wtforms.validators import DataRequired
from wtforms.widgets import TextArea, HiddenInput
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from .models import Source, Tlp, Level, Itype, Control, Status, Likelihood, Event, Destination


class FeedConfigForm(Form):
    index_id = IntegerField(widget=HiddenInput())
    name = StringField('Name', validators=[DataRequired()])
    frequency = StringField('Frequency', validators=[DataRequired()])
    event = QuerySelectField('Event',
                                  query_factory=lambda: Event.query.join(Source).filter(Source.name == 'Feed'),
                                  get_label='name')
    module = details = StringField('Modules', widget=TextArea(), validators=[DataRequired()])



class EventForm(Form):
    name = StringField('Name', validators=[DataRequired()])
    details = StringField('Details', widget=TextArea(), validators=[DataRequired()])
    confidence = SelectField('Confidence', coerce=int, validators=[DataRequired()])
    source = QuerySelectField('Source', query_factory=lambda: Source.query, get_label='name')
    tlp = QuerySelectField('TLP', query_factory=lambda: Tlp.query, get_label='name')
    impact = QuerySelectField('Potential Impact', query_factory=lambda: Level.query, get_label='name')
    likelihood = QuerySelectField('Likelihood', query_factory=lambda: Likelihood.query, get_label='name')
    status = QuerySelectField('Status', query_factory=lambda: Status.query, get_label='name')


class IndicatorForm(Form):
    event_id = IntegerField(widget=HiddenInput())
    ioc = StringField('IOC', validators=[DataRequired()])
    comment = StringField('Comment')
    control = QuerySelectField('Control Path', query_factory=lambda: Control.query, get_label='name')
    itype = QuerySelectField('Data Type', query_factory=lambda: Itype.query, get_label='name')


class IndicatorEditForm(Form):
    event_id = IntegerField(widget=HiddenInput())
    comment = StringField('Comment')
    control = QuerySelectField('Control Path', query_factory=lambda: Control.query, get_label='name')
    enrich = StringField('Enrich Summary')
    enrich_full = StringField('Enrich Details', widget=TextArea())
    update_enrich = BooleanField('Update Enrichment')

class MitigationForm(Form):
    mit_id = IntegerField(widget=HiddenInput())
    description = StringField('Description', validators=[DataRequired()])
    ttl = SelectField('TTL', coerce=int)
    destination = QuerySelectField('Destination', query_factory=lambda: Destination.query, get_label='name')
    pending = BooleanField('Pending')
    active = BooleanField('Active')



class NoteForm(Form):
    event_id = IntegerField(widget=HiddenInput())
    details = StringField('Note', widget=TextArea(), validators=[DataRequired()])


class ControlForm(Form):
    name = StringField('Name', validators=[DataRequired()])


class ItypeForm(Form):
    field_id = IntegerField()
    field_name = StringField('Name', validators=[DataRequired()])
    field_regex = StringField('Regex')


class LevelForm(Form):
    name = StringField('Name', validators=[DataRequired()])


class LikelihoodForm(Form):
    name = StringField('Name', validators=[DataRequired()])


class SourceForm(Form):
    name = StringField('Name', validators=[DataRequired()])


class StatusForm(Form):
    name = StringField('Name', validators=[DataRequired()])

class TlpForm(Form):
    name = StringField('Name', validators=[DataRequired()])
