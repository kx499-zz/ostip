To set up:  
git clone https://github.com/kx499/ostip.git   
virtualenv ostip  
cd ostip  
bin/pip install -r requirements.txt  
scripts/install-redis.sh  
./db_create.py
cp feeder/feed.json.example feeder/feed.json

running:  
../redis-stable/src/redis-server # Note this is started in install-redis.sh, but in subsequent runs, it's required.
bin/celery -A tasks.celery  worker --loglevel=info --beat  
./run.py  

Note: if not running on localhost, add host=0.0.0.0 to app.run() in run.py, or use ./run.py --prod

On Debian or Ubuntu systems, you will need to `sudo apt install git python-virtualenv python-pip python-dev`
