from app import db, app
from celery.signals import task_postrun
from app import create_celery_app
from celery.task.schedules import crontab
from celery.decorators import periodic_task
from celery.utils.log import get_task_logger
from datetime import datetime
from feeder.feed import Feed
import requests


celery = create_celery_app(app)
logger = get_task_logger(__name__)


@celery.task
def send_event_notification():
    ''' send mail to the recipients '''
    print "sent the mail"

@periodic_task(run_every=(crontab(hour="*", minute="*", day_of_week="*")))
def pull_feeds():
    logger.info("Start task")
    now = datetime.now()
    f = Feed()
    results = f.process_all()
    logger.info("pulled feeds")
    logger.info("Task finished: total inserted %i" % len(results))

@task_postrun.connect
def close_session(*args, **kwargs):
    db.session.remove()