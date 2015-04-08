#!/bin/bash

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
sudo pip install https://github.com/cloudify-cosmo/cloudify-dsl-parser/archive/$CORE_VERSION.zip
sudo pip install https://github.com/cloudify-cosmo/cloudify-rest-client/archive/$CORE_VERSION.zip
sudo pip install https://github.com/cloudify-cosmo/cloudify-plugins-common/archive/$CORE_VERSION.zip
sudo pip install https://github.com/cloudify-cosmo/cloudify-script-plugin/archive/$PLUGINS_VERSION.zip
sudo pip install https://github.com/cloudify-cosmo/cloudify-cli/archive/$CORE_VERSION.zip

if hash wget 2>/dev/null; then
	echo "...............................................wget already installed"
else
	echo "......................................................installing wget"
	sudo apt-get install -y wget
fi

wget https://github.com/cloudify-cosmo/cloudify-docker-plugin/archive/$PLUGINS_VERSION.zip

sudo pip install $PLUGINS_VERSION.zip

if hash unzip 2>/dev/null; then
	echo "..............................................unzip already installed"
else
	echo ".....................................................installing unzip"
	sudo apt-get install -y unzip
fi

unzip $PLUGINS_VERSION.zip

mv cloudify-docker-plugin-${PLUGINS_VERSION} $HOME/docker_system_test
sudo chmod $USER:$USER $HOME/docker_system_test

sudo pip install -r $HOME/docker_system_test/dev-requirements.txt
sudo pip install -r $HOME/docker_system_test/test-requirements.txt

exit 0
