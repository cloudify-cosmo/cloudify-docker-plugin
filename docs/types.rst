.. highlight:: yaml

Types
=====


Node Types
----------

.. cfy:node:: cloudify.docker.Container

.. note::

    For more information on importing and pulling images, see `docker import command <https://docs.docker.com/reference/commandline/cli/#import>`_ and `docker pull command <https://docs.docker.com/reference/commandline/cli/#pull>`_.

**Mapped Operations:**

  * ``cloudify.interfaces.lifecycle.create`` creates the container.

    * **Inputs:**

      * ``params`` Any parameters exposed by the Docker Py library to the ``create_container`` operation::

          create:
            inputs:
              params:
                ports:
                  - 27017
                  - 28017
                stdin_open: true
                tty: true
                command: mongod --rest --httpinterface --smallfiles


      * Here, the plugin pulls images from the Docker Hub Registry, a private registry, or it may import an image from a tarball.

      * This operations adds the container_id to the instance runtime_properties.


  * ``cloudify.interfaces.lifecycle.start`` starts the container.

    * **Inputs:**

      * ``params`` Any parameters exposed by the Docker Py library to the ``start`` operation::

          start:
            inputs:
              params:
                port_bindings:
                  27017: 27017
                  28017: 28017

      * ``processes_to_wait_for`` A list of processes to wait for before finishing the start operation::

              ...
                processes_to_wait_for:
                  - /bin/sh

      * ``retry_interval`` Before the start operation finishes,
        Cloudify confirms that the container is started.
        This is the number of seconds between checking.
        Defaults to 1.

    * It also logs containers' network settings with IPs,
      ports, and top information.


  * ``cloudify.interfaces.lifecycle.stop`` stops the container.

    * **Inputs:**

      * ``params`` Any parameters exposed by the Docker Py library to the ``stop`` operation::

          stop:
            inputs:
              params:
                timeout: 30

      * ``retry_interval`` Before the stop operation finishes, Cloudify confirms that the container is stopped. This is the number of seconds between checking. Defaults to 10.

  * ``cloudify.interfaces.lifecycle.delete`` deletes the container.

    * **Inputs:**

      * ``params`` Any parameters exposed by the Docker Py library to the ``remove_container`` operation::

          delete:
            inputs:
              params:
                force: true

      * ``retry_interval`` Before the delete operation finishes, Cloudify confirms that the container is removed. This is the number of seconds between checking. Defaults to 10.

**Attributes:**

  * ``container_id`` The ID of the container in the Docker Server.
  * ``ports`` The ports as shown in the container inspect output.
  * ``network_settings`` The network_settings dict in the inspect output.
  * ``image_id`` The ID of the repository/tag pulled or imported.


