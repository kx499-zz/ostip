To set up:

git clone https://blah
virtenv ostip
cd ostip
bin/pip install -r requirements.txt
run install-redis.sh

running:
redis-stable/src/redis-server
bin/celery -A tasks.celery  worker --loglevel=info --beat
./run.py



