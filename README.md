To set up:  
git clone https://github.com/kx499/ostip.git   
virtualenv ostip  
cd ostip  
bin/pip install -r requirements.txt  
.scripts/install-redis.sh  
./db_create.py
  
running:  
.redis-stable/src/redis-server  
bin/celery -A tasks.celery  worker --loglevel=info --beat  
./run.py  

Note: of not running on localhost, add host=0.0.0.0 to app.run() in run.py



