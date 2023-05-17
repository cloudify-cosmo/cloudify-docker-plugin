#!/bin/bash -e
if [ -f /etc/redhat-release ]; then
  sed -i '/ExecStart/s/usr\/bin\/dockerd/usr\/bin\/dockerd --mtu=1450/' /lib/systemd/system/docker.service
  sed -i '/ExecStart/ s/$/ -H=tcp:\/\/0.0.0.0:2375 --dns 8.8.8.8 --bip 172.99.0.1\/16/' /lib/systemd/system/docker.service
  systemctl daemon-reload
  systemctl restart docker.service
fi
if [ -f /etc/lsb-release ]; then
  if [[ -n $(systemctl list-unit-files | grep -w "docker") ]]; then
    sed -i '/ExecStart/s/usr\/bin\/dockerd/usr\/bin\/dockerd --mtu=1450/' /lib/systemd/system/docker.service
    sed -i '/ExecStart/ s/$/ -H=tcp:\/\/0.0.0.0:2375 --dns 8.8.8.8 --bip 172.99.0.1\/16/' /lib/systemd/system/docker.service
    systemctl daemon-reload
    systemctl restart docker.service
  else
    echo "DOCKER_OPTS=\"--mtu=1450 --dns 8.8.8.8 --dns 8.8.4.4 \
        -H=tcp://0.0.0.0:2375 --bip 172.99.0.1/16\"" >> /etc/default/docker
    service docker restart
  fi
fi
