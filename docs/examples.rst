.. highlight:: yaml

Examples
========

Node Specification
------------------

::

  some_container:
    type: cloudify.docker.Container
    properties:
      name: some_name
      image:
        repository: dockeruser/dockerrepo
    interfaces:
      cloudify.interfaces.lifecycle:
        create:
          implementation: docker.docker_plugin.tasks.create_container
          inputs:
            params:
              ports:
                - 8080
              stdin_open: true
              tty: true
              command: /bin/sleep 20
        start:
          implementation: docker.docker_plugin.tasks.start
          inputs:
            params:
              port_bindings:
                8080: 8080


Importing from an URL
---------------------

::

  cloudify_manager:
    type: cloudify.docker.Container
    properties:
      name: cloudify-manager
      image:
        src: http://gigaspaces-repository-eu.s3.amazonaws.com/org/cloudify3/3.2.0/m6-RELEASE/cloudify-docker_3.2.0-m6-b176.tar
        tag: 3.2.0


Complete Example
----------------

For a complete working example, please see the `cloudify-nodecellar-docker-example <https://github.com/cloudify-cosmo/cloudify-nodecellar-docker-example>`_.


.. _os_example:

Create a suitable Docker host (OpenStack)
-----------------------------------------
This example node type configures an :cfy:node:`cloudify.openstack.nodes.Server` instance for use with the docker plugin::

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
