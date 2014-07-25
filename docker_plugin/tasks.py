import docker

from cloudify import exceptions

from codilime import docker_wrapper


def create(ctx):
    client = docker_wrapper.get_client(ctx)
    if (
        'image_import' in ctx.properties and
        ctx.properties['image_import'].get('src')
    ):
        image = docker_wrapper.import_image(ctx, client)
    elif (
        'image' in ctx.properties and
        ctx.properties['image'].get('path')
    ):
        image = docker_wrapper.build_image(ctx, client)
    else:
        ERROR_NO_IMAGE_SRC = ("Either path or url" +
                              "to image must be given")
        docker_wrapper.ctx.logger.error(ERROR_NO_IMAGE_SRC)
        raise exceptions.NonRecoverableError(ERROR_NO_IMAGE_SRC)
    ctx.runtime_properties.update({'image': image})
    docker_wrapper.create_container(ctx, client)


def run(ctx):
    client = docker_wrapper.get_client(ctx)
    docker_wrapper.start_container(ctx, client)
    containers = client.containers()
    container = docker_wrapper.get_container_info(ctx, client)
    top_info = docker_wrapper.get_top_info(ctx, client)
    ctx.logger.info(
        "Container: " + container['Id'] + "\n"
        "Ports: " + str(container['Ports']) + "\n"
        "Top: " + top_info
    )
    logs = client.logs(ctx.runtime_properties['container'])
    # TODO function will not return anything
    return (containers, top_info, logs)


def stop(ctx):
    client = docker_wrapper.get_client(ctx)
    docker_wrapper.stop_container(ctx, client)


def delete(ctx):
    client = docker_wrapper.get_client(ctx)
    container_info = docker_wrapper.inspect_container(ctx, client)
    if container_info and container_info['State']['Running']:
        docker_wrapper.stop_container(ctx, client)
    remove_image = None
    if 'container_remove' in ctx.properties:
        remove_image = ctx.properties['container_remove'].pop(
            'remove_image', None
        )
    docker_wrapper.remove_container(ctx, client)
    if remove_image:
        docker_wrapper.remove_image(ctx, client)
