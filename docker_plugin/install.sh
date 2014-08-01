#!/bin/bash

set -e

term_handler(){
  sudo killall -s 9 apt-get
  exit 1
}

trap term_handler TERM

sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 36A1D7869245C8950F966E92D8576A8BA88D21E9
echo deb https://get.docker.io/ubuntu docker main | sudo tee /etc/apt/sources.list.d/docker.list 1>/dev/null
sudo apt-get update
sudo apt-get -y --no-install-recommends install lxc-docker
sudo usermod -a -G docker $USER
