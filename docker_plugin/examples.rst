.. highlight:: yaml

Examples
========

Create a suitable Docker host (OpenStack)
-----------------------------------------
This example node type configures an OpenStack (:cfy:node:`cloudify.openstack.nodes.Server`) instance for use with the docker plugin::

  vm_with_docker:
    derived_from: cloudify.openstack.nodes.Server
    properties:
      cloudify_agent:
        default:
          user: { get_input: agent_user }
          home_dir: /home/ubuntu
      server:
        default:
          image: { get_input: image }
          flavor: { get_input: flavor }
          userdata: |
            #!/bin/bash
            sudo service ssh stop
            curl -o install.sh -sSL https://get.docker.com/
            sudo sh install.sh
            sudo groupadd docker
            sudo gpasswd -a ubuntu docker
            sudo service docker restart
            sudo service ssh start
