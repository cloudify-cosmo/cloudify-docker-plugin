#!/bin/sh

# fix broken packages in the Vagrant box :)
vagrant ssh -- sudo apt-get -yf install

vagrant ssh -- 'cd ~/simple; git clone https://github.com/cloudify-cosmo/cloudify-system-tests.git'
vagrant ssh -- 'cd ~/simple/cloudify-system-tests; git checkout 3.0rc1 -b 3.0rc1'
vagrant ssh -- '. ~/cloudify/bin/activate; pip install sh==1.09 path.py==5.1 nose==1.3.3'

vagrant ssh -- mkdir -p '~/simple/cloudify_docker_plugin'
tar -C cloudify_docker_plugin -cf - `ls cloudify_docker_plugin` | vagrant ssh -- tar -C '~/simple/cloudify_docker_plugin' -xvf -
vagrant ssh -- 'cd ~/simple; cp -r cloudify-system-tests/cosmo_tester cloudify_docker_plugin'
vagrant ssh -- 'cd; . cloudify/bin/activate; cd simple/cloudify_docker_plugin; pip install .'
vagrant ssh -- '~/simple/cloudify_docker_plugin/bin/install_docker.sh'
