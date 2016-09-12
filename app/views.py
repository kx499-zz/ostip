from flask import render_template, flash, redirect, request, jsonify
from sqlalchemy.exc import IntegrityError
from app import app
from .forms import EventForm, IndicatorForm, NoteForm
from .models import Event, Indicator, Itype, Control, Links, Level, Likelihood, Source, Status, Tlp, Note, db
from .utils import _load_related_data, _correlate, _enrich_data
import json
import datetime
from datatables import ColumnDT, DataTables


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home', events=Event.query.all())


@app.route('/event/add', methods=['GET', 'POST'])
def event_add():
    form = EventForm()
    form.confidence.choices = [(i, '%s' % i) for i in xrange(0, 100, 5)]
    if form.validate_on_submit():
        flash('"%s" event submitted, Confidence=%s' % (form.name.data, form.confidence.data))
        ev = Event(form.name.data,
                   form.details.data,
                   form.source.data,
                   form.tlp.data,
                   form.impact.data,
                   form.likelihood.data,
                   form.confidence.data)
        db.session.add(ev)
        db.session.commit()
        return redirect('/index')
    print(form.errors)
    return render_template('event_add.html',
                           title='Add Event',
                           form=form)


@app.route('/event/view/<int:event_id>', methods=['GET', 'POST'])
def event_view(event_id):
    def _indicator_add(form):
        ind = Indicator(form.event_id.data,
                        form.ioc.data,
                        form.comment.data,
                        form.control.data,
                        form.itype.data)
        db.session.add(ind)
        try:
            db.session.commit()
            res = '"%s" indicator submitted' % form.ioc.data
            _correlate([[ind.id, form.event_id.data, ind.ioc]])
        except IntegrityError:
            db.session.rollback()
            res = '"%s" indicator not submitted - duplicate' % form.ioc.data
        return res

    def _note_add(form):
        note = Note(form.event_id.data, form.details.data)
        db.session.add(note)
        try:
            db.session.commit()
            res = 'note submitted'
        except IntegrityError:
            db.session.rollback()
            res = 'note not submitted'
        return res

    def _event_edit(form, event):
        form.populate_obj(event)
        try:
            db.session.commit()
            res = '"%s" Event Updated' % event.id
        except IntegrityError:
            db.session.rollback()
            res = '"%s" Event Updated' % event.id
        return res

    ev = Event.query.get(event_id)
    ind_form = IndicatorForm()
    ind_form.event_id.data = event_id
    ev_form = EventForm(obj=ev)
    ev_form.confidence.choices = [(i, '%s' % i) for i in xrange(0, 100, 5)]
    nt_form = NoteForm()
    nt_form.event_id.data = event_id
    if ind_form.validate_on_submit():
        flash(_indicator_add(ind_form))
        return redirect('/event/view/%s' % event_id)
    elif ev_form.validate_on_submit():
        flash(_event_edit(ev_form, ev))
        return redirect('/event/view/%s' % event_id)
    elif nt_form.validate_on_submit():
        flash(_note_add(nt_form))
        return redirect('/event/view/%s' % event_id)
    return render_template('event_view.html',
                           title='View Event',
                           event=ev,
                           form=ind_form,
                           ev_form=ev_form,
                           nt_form=nt_form)


@app.route('/admin/table/view', methods=['GET', 'POST'])
def view_fields():
    fields = {'Data Type': [Itype.query.all(), 'type'],
              'Impact': [Level.query.all(), 'impact'],
              'Likelihood': [Likelihood.query.all(), 'likelihood'],
              'Data Source': [Source.query.all(), 'source'],
              'Event Status': [Status.query.all(), 'status'],
              'TLP': [Tlp.query.all(), 'tlp'],
              'Controls': [Control.query.all(), 'control']
              }
    return render_template('table_view.html', title='View/Edit Fields', fields=fields)


@app.route('/admin/table/<table_name>/<action>', methods=['POST'])
def view_edit_table(table_name, action):
    objects = {'type': Itype(),
               'impact': Level(),
               'likelihood': Likelihood(),
               'source': Source(),
               'status': Status(),
               'tlp': Tlp(),
               'Control': Control()}
    if table_name in objects.keys():
        base_obj = objects[table_name]
    else:
        return redirect('/fields/view')

    if action == 'add':
        base_obj.name = request.form['field_name']
        db.session.add(base_obj)
    elif action == 'edit':
        item = base_obj.query.get(request.form['field_id'])
        item.name = request.form['field_name']
        db.session.add(item)
    elif action == 'delete':
        item = base_obj.query.get(request.form['field_id'])
        db.session.delete(item)
    else:
        return redirect('/admin/table/view')
    db.session.commit()
    flash('Successfully Updated - Action: %s; Table: %s' % (table_name, action))

    return redirect('/admin/table/view')


@app.route('/indicator/pending/view', methods=['GET', 'POST'])
def indicator_pending():
    if request.method == 'POST':
        update_list = [int(i) for i in request.form.getlist('selected')]
        del_list = [int(i) for i in request.form.getlist('not_selected')]

        upd_query = db.session.query(Indicator).filter(Indicator.id.in_(update_list))
        upd_query.update({'pending':False}, synchronize_session=False)
        del_query = db.session.query(Indicator).filter(Indicator.id.in_(del_list))
        del_query.delete(synchronize_session=False)
        db.session.commit()

        ioc_query = Indicator.query.with_entities(Indicator.id, Indicator.event_id, Indicator.ioc)
        ioc_list = ioc_query.filter(Indicator.id.in_(update_list)).all()
        _correlate(ioc_list)

        return redirect('/indicator/pending/view')
    return render_template('indicator_pending.html', title='Pending Indicators')


@app.route('/indicator/<status>/data/<int:event_id>')
def pending_data(status, event_id):
    """Return server side data."""
    # defining columns
    columns = []
    columns.append(ColumnDT('id'))
    columns.append(ColumnDT('ioc'))
    columns.append(ColumnDT('itype.name'))
    columns.append(ColumnDT('control.name'))
    columns.append(ColumnDT('comment'))
    columns.append(ColumnDT('enrich'))
    columns.append(ColumnDT('first_seen'))

    if status == 'pending':
        columns.append(ColumnDT('event_id'))
        columns.append(ColumnDT('event.name'))
        query = db.session.query(Indicator).filter(Indicator.pending == True)
    elif status == 'approved':
        columns.append(ColumnDT('last_seen'))
        columns.append(ColumnDT('rel_list'))
        query = db.session.query(Indicator).filter(Indicator.event_id == event_id).filter(Indicator.pending == False )
    else:
        query = db.session.query(Indicator).filter(Indicator.pending == True)

    # instantiating a DataTable for the query and table needed
    rowTable = DataTables(request.args, Indicator, query, columns)

    # returns what is needed by DataTable
    return jsonify(rowTable.output_result())


###
# API Calls
###

@app.route('/api/indicator/bulk_add', methods=['POST'])
def indicator_bulk_add():
    req_keys = ('control', 'data_type', 'event_id', 'pending', 'data')
    inserted_indicators = []

    try:
        pld = request.get_json(silent=True)
    except Exception, e:
        return json.dumps({'results': 'error', 'data': '%s' % e})

    if all(k in pld for k in req_keys) and isinstance(pld['event_id'], (int, long)):
        # load related stuff
        ioc_list, cont_id, type_id = _load_related_data(pld)

        if not (ioc_list and cont_id and type_id):
            return json.dumps({'results': 'error', 'data': 'Could not load Control, Type, or IOC list'})

        # loop through data and add/update ioc
        for val, desc in pld['data']:
            ind_id = ioc_list.get(val)
            if ind_id:
                ind = Indicator.query.get(ind_id)
                ind.last_seen = datetime.datetime.utcnow()
            else:
                ind = Indicator(pld['event_id'], val, desc, cont_id, type_id, pld['pending'], _enrich_data(pld))
                db.session.add(ind)
                db.session.flush()
                ind_id = ind.id
                if not pld['pending']:
                    inserted_indicators.append([ind_id, pld['event_id'], val])
        # commit
        db.session.commit()
        _correlate(inserted_indicators)

    res_json = {'results': 'success'}
    return json.dumps(res_json)
