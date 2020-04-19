# Cloudify Docker Plugin

This plugin provides the following functionality:

  * Installation, configuration and uninstallation of Docker on a machine
    [ could be the manager as well but better to have it on a different node ]
  * Representation of Docker modules [Image, Container] as Cloudify nodes
  * Building Docker Images
  * Run Docker container given the built images that you have
  * Retrieve host details
  * Retrieve all images on the system
  * Retrieve all containers on the system
  * Handle container volume mapping to the docker host for use inside the container

  --------
  Two more things:

  * Handle Ansible Playbook inside a docker container given the same node_type
    as in [cloudify-ansible-plugin](https://github.com/cloudify-cosmo/cloudify-ansible-plugin)

    **NOTE**
    * in addition to the properties, some more were added in order to specify
    which docker machine to execute that container on

  * Handle Terraform module inside a docker container given the same node_type
    as in [cloudify-terraform-plugin](https://github.com/cloudify-incubator/cloudify-terraform-plugin)

    **NOTE**

    * in addition to the properties, some more were added in order to specify
      which docker machine to execute that container on,

    * one more thing is the terraform_plugins which is the list to install to that container


    docker specific properties:

    - ```
      cloudify.types.docker.DockerMachineConfig:
        properties:
          docker_ip:
            description: Docker Machine IP
            type: string
            default: ''
          docker_user:
            description: Docker Machine User
            type: string
            default: ''
          docker_key:
            description: Docker Machine Private Key
            type: string
            default: ''
          container_volume:
            description: Docker Container volume_mapping
            type: string
            default: ''
        ```

One more thing if you want to provision a host given a Cloudify manager,
you could use a blueprint that handles that task of configure docker,
see [Blueprints](https://github.com/cloudify-community/blueprint-examples/tree/master/docker-machine-example)

## Examples

For official blueprint examples using this Cloudify plugin, please see [Cloudify Community Blueprints Examples](https://github.com/cloudify-community/blueprint-examples/).



## Usage

See [Docker Plugin](https://docs.cloudify.co/5.0.5/working_with/official_plugins/)
