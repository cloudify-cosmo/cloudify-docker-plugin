#!/bin/bash -e

if ! (ps ax | grep -v grep | grep 'docker'); then
    echo ".................................................DOCKER NOT INSTALLED"
    exit 1
fi

sudo apt-get update
sudo apt-get install -y python-dev

if hash curl 2>/dev/null; then
	echo "...............................................curl already installed"
else
	echo "......................................................installing curl"
	sudo apt-get install -y curl
fi

curl -L https://bootstrap.pypa.io/get-pip.py -o get-pip.py

sudo python get-pip.py
sudo pip install virtualenv
cd $HOME
virtualenv cloudify_system_test
source cloudify_system_test/bin/activate
pip install https://github.com/cloudify-cosmo/cloudify-cli/archive/$CORE_BRANCH.zip -r https://raw.githubusercontent.com/cloudify-cosmo/cloudify-cli/$CORE_BRANCH/dev-requirements.txt

if hash wget 2>/dev/null; then
	echo "...............................................wget already installed"
else
	echo "......................................................installing wget"
	sudo apt-get install -y wget
fi

wget https://github.com/cloudify-cosmo/cloudify-docker-plugin/archive/$DOCKER_PLUGIN_BRANCH.zip

pip install $DOCKER_PLUGIN_BRANCH.zip

if hash unzip 2>/dev/null; then
	echo "..............................................unzip already installed"
else
	echo ".....................................................installing unzip"
	sudo apt-get install -y unzip
fi

unzip $DOCKER_PLUGIN_BRANCH.zip

mv cloudify-docker-plugin-${DOCKER_PLUGIN_BRANCH} $HOME/docker_system_test

pip install -r $HOME/docker_system_test/dev-requirements.txt
pip install -r $HOME/docker_system_test/test-requirements.txt
