Vagrant.configure(2) do |config|
  config.vm.box = "ubuntu/trusty64"
  config.vm.network "forwarded_port", guest: 5000, host: 5000
  config.vm.provision "shell", inline: <<-SHELL
    sudo apt-get update
    sudo apt-get install -y git python-virtualenv python-pip python-dev
    mkdir -p /opt
    cd /opt
    git clone https://github.com/kx499/ostip.git
    virtualenv ostip
    cd ostip
    bin/pip install -r requirements.txt
    scripts/install-redis.sh --DoNotStartRedis
  SHELL
  config.vm.provision "shell", run: 'always', inline: <<-SHELL
    cd /opt
    redis-stable/src/redis-server &
    cd /opt/ostip
    mkdir -p tmp
    touch tmp/ostip_access.log
    sudo chown -R vagrant:vagrant /opt/ostip
  SHELL
  config.vm.provision "shell", inline: <<-SHELL
    cd /opt/ostip
    ./db_create.py
  SHELL
  config.vm.provision "shell", run: 'always', inline: <<-SHELL
    cd /opt/ostip
    mkdir -p tmp
    touch tmp/ostip_access.log
    sudo chown -R vagrant:vagrant /opt/ostip
    sudo -u vagrant -- bin/celery -A tasks.celery worker --loglevel=info --beat &
    sudo -u vagrant -- ./run.py --prod &
  SHELL
end
