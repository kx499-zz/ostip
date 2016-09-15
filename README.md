To set up:  
git clone https://github.com/kx499/ostip.git   
virtualenv ostip  
cd ostip  
bin/pip install -r requirements.txt  
.scripts/install-redis.sh  
  
running:  
.redis-stable/src/redis-server  
bin/celery -A tasks.celery  worker --loglevel=info --beat  
./run.py  



