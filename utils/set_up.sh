#!/bin/sh
#
# A utility script that sets up Vagrant VM.
# Designed for Cloudify box 3.0.0 - use it only on version 3.0.0.


# Fix broken packages in the Vagrant box.
vagrant ssh -- sudo apt-get -yf install

# Copy our plugin into the Vagrant VM.
vagrant ssh -- mkdir -p '~/simple/cloudify_docker_plugin'
tar -C cloudify_docker_plugin -cf - `ls cloudify_docker_plugin` | vagrant ssh -- tar -C '~/simple/cloudify_docker_plugin' -xvf -

# Clone system-tests, switch to the right tag, install required packages
# (minimal installation), copy cosmo_tester into the plugin directory.
vagrant ssh -- 'cd ~/simple; git clone https://github.com/cloudify-cosmo/cloudify-system-tests.git'
vagrant ssh -- 'cd ~/simple/cloudify-system-tests; git checkout 3.0rc1 -b 3.0rc1'
vagrant ssh -- '. ~/cloudify/bin/activate; pip install sh==1.09 path.py==5.1 nose==1.3.3'
vagrant ssh -- 'cd ~/simple; cp -r cloudify-system-tests/cosmo_tester cloudify_docker_plugin'

# Install our plugin and use it's docker installation script to be able to
# execute tests.
vagrant ssh -- 'cd; . cloudify/bin/activate; cd simple/cloudify_docker_plugin; pip install .'
vagrant ssh -- '~/simple/cloudify_docker_plugin/bin/install_docker.sh'
