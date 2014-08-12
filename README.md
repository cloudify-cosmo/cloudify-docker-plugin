Cloudify Docker plugin
======================

A Cloudify plugin enabling it to create and manipulate Docker containers.


Installation and upgrading
--------------------------

To install just run: `pip install .`.


Running tests
-------------

To run tests the following packages are additionally needed:

* *sh* (v. 1.09),
* *path.py* (v. 5.1),
* *nose* (v. 1.3.3),
* *cloudify-system-tests* (v. 3.0.0).

Currently, the `cloudify-system-tests` package does not contain anything but
the `__init__.py` file. This issue can be easily worked around by installing
all the requirements and copying the entire `cosmo_tester` directory into
the plugin's root.


### UnitTests ###
We recommend using nose to run tests.

Tests are divided into three directories. 

* `tests/basic_tests_cloudify_docker_plugin` 

Consists of short tests that test only basic functionalities, like creating,
running and removing containers.

* `tests/advanced_tests_cloudify_docker_plugin` 

Consits of more complicated tests that sometimes take longer time to complete.
They test if advanced options are working, like networks or ports
configuration in containers.

* `tests/internal_functions`

Consits of tests that don't use docker containers and only test more 
complicated internal functions. For example the  function that checks if given
ID is valid docker ID.

To run tests on specific group use `nosetests tests/[directory]`.

### System Test ###
System Test behaves just like python UnitTest. It uses Cloudify to check if
execution of a test deployment works on a docker container.

Before running it, set the environmental variable `CLOUDIFY_TEST_MANAGEMENT_IP`.
Then launch it using nose: `nosetests tests/system_tests`.


Blueprints
----------

In plugin.yaml there are defined several types: 

* `cloudify.types.docker.web_server`

* `cloudify.types.docker.app_server`

* `cloudify.types.docker.db_server`

* `cloudify.types.docker.message_bus_server`

* `cloudify.types.docker.app_module`

All of the types have the same properties:

* `daemon_client`

* `image_import`

* `image_build`

* `container_create`

* `container_start`

* `container_stop`

* `container_remove`

Which are described in `Properties` section.

An example node specification:

```

    name: server

    type: cloudify.types.docker.db_server

    properties:

        daemon_client: {}
        
        image_build: {}
        
        image_import:
        
            src: http://insert/url/to/image/here
        
        container_create:
        
            command: /bin/echo hello
        
        container_start: {}
        
        container_stop: {}
        
        container_remove: {}

```

### Properties: ###
Properties in blueprints are dictionaries. Dictionaries correspond
to parameters used in 
[an api client for docker.](https://github.com/docker/docker-py)

If there is a lack of description of certain parameters, 
more details can be found in 
[docker command line documentation.](https://docs.docker.com/reference/commandline/cli/)

Here are listed all dictionaries and some of the keys:

* `daemon_client`
    
    Similar to the parameters of `Client` function in Docker API client.

* `image_import`:
    
    Similar to the parameters of `import_image` function in Docker API client.

    - `src`(string): an URL to the image.

* `image_build`:

    Similar to the parameters of `build` function in Docker API client.

    - `path`(string): a path to a directory containing a Dockerfile.

    - `fileobj` is not supported.

    - `rm`(bool): Are the intermediate containers to be deleted.

Either `src` in `image_import` dictionary or `path` in `image_build` 
must be specified.

* `container_create`:

    Similar to the parameters of `create_container` function in 
    Docker API client.

    - Do not provide `image`, it is automatically added to context runtime
      properties during task create.

    - `command`(string): is mandatory. Specifies command that will be executed
      in container.

    - `environment`(dictionary of strings): Specifies environmental variables
      that will be available in container.

    - `ports`(list of integers): a list of ports to open inside the container.

    - `volumes`(list of strings) a list of mountpoints.

* `container_start`:
    
    Similar to the parameters of `start` function in Docker API client.

    - Do not provide `container`, it is automatically added to context runtime
      properties during task create.

    - `port_bindings`(dictionary of integers): declaration of port bindings.

    - `network_mode`(string)

    - `binds`(dictionary of dictionaries of strings): volume mappings

* `container_stop`:
    
    Similar to the parameters of `stop` function in Docker API client.

    - Do not provide `container`, it is automatically added to context runtime
      properties during task create.

    - `timeout`(integer): number of seconds to wait for the container to stop 
      before killing it.

* `container_remove`:
    
    Similar to the parameters of `remove_container` function in 
    Docker API client.
    
    - Do not provide `container`, it is automatically added to context runtime
      properties during task create.

    - `remove_image`(bool): additional key, specifies weather or not to
      remove image when removing container.

Description of the rest of the keys can be found in desctiption
of methods in 
[an api client for docker.](https://github.com/docker/docker-py)


Using plugin
------------

All tasks get docker client using `daemon_client` dictionary from 
context properties. 

Dictionaries are described in Blueprints chapter.
They have to be given but if not otherwise specified they can be empty.

Create task:

* Installs docker (if it isn't already installed).

* Imports or builds image:

    if in context properties there is an `image_import` dictionary it imports
    an image using this dictionary as options.

    if in context properties there is an `image_build` dictionary it builds
    an image using this dictionary as options.

    Either `src` in `image_import` dictionary or `path` in `image_build` 
    must be specified.


Configure task:

* Adds `docker_env_var` from context runtime propertieis with 
  context properties `container_create``environment` as environmental 
  variables in container.

* Creates container using the image from `runtime_properties` and options from
  context propertieis `container_create`. `command` in `container_create` must
  be specified.

Run task:

* Starts conatiner with `container_start` dictionary as options.
  
* Logs containers id, list of network interfaces with IPs, ports, 
  and top information.

Stop task:

* Stops container with `container_stop` dictionary as options.

Delete task:

* If `remove_image` in `container_remove` dictionary is True then image of
  this container is deleted. If the image is used by another container 
  error is raised.

* Deletes container with `container_remove` dictionary as options.
