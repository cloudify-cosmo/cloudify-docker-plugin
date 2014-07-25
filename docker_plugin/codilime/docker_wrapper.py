import re
import os

import docker

from cloudify import exceptions


def is_image_id_valid(ctx, image_id):
    return re.match('^[a-f0-9]{12,64}$', image_id) is not None


def import_image(ctx, client):

    def get_image_id(import_image_output):
        # import_image returns long string where in the second line
        # after last status is image id
        output_line = import_image_output.split('\n')[1]
        position_of_last_status = output_line.rfind('status')
        if position_of_last_status < 0:
            # If there was an error, there is no 'status'
            # in second output line
            # error message is after last 'error'
            position_of_error = output_line.rfind('error')
            error_message = output_line[position_of_error:].split('"')[2]
            ctx.logger.error("Error during image import " + error_message)
            raise exceptions.NonRecoverableError(error_message)
        image_id = output_line[position_of_last_status:].split('"')[2]
        if is_image_id_valid(ctx, image_id):
            return image_id
        else:
            UNKNOWN_ERROR_IMAGE_IMPORT = "Unknown error during image import"
            ctx.logger.error(UNKNOWN_ERROR_IMAGE_IMPORT)
            raise exceptions.NonRecoverableError(UNKNOWN_ERROR_IMAGE_IMPORT)

    ctx.logger.info("Importing image")
    image_id = get_image_id(
        client.import_image(**ctx.properties['image_import'])
    )
    ctx.logger.info("Image " + image_id + " has been imported")
    return image_id


def build_image(ctx, client):

    def get_image_id(stream_generator):
        UNKNOWN_ERROR_IMAGE_BUILD = "Unknown error while building image"
        stream = None
        for stream in stream_generator:
            pass
        # Fourth word in a string stream is an id
        # I can't find it in docker documentation
        if not stream:
            ctx.logger.error(UNKNOWN_ERROR_IMAGE_BUILD)
            raise exceptions.RecoverableError(UNKNOWN_ERROR_IMAGE_BUILD)
        image_id = re.sub(r'[\W_]+', ' ', stream).split()[3]
        if is_image_id_valid(ctx, image_id):
            return image_id
        else:
            ctx.logger.error(UNKNOWN_ERROR_IMAGE_BUILD)
            raise exceptions.NonRecoverableError(UNKNOWN_ERROR_IMAGE_BUILD)

    ctx.logger.info(
        "Building image from path " +
        ctx.properties['image']['path']
    )
    try:
        image_stream = client.build(**ctx.properties['image'])
    except OSError as e:
        ctx.logger.error("Error while building image: " + str(e))
        raise exceptions.NonRecoverableError(e)
    else:
        image_id = get_image_id(image_stream)
        ctx.logger.info("Image " + image_id + " has been built")
        return image_id


def get_client(ctx):
    daemon_client = ctx.properties.get('daemon_client', {})
    try:
        return docker.Client(**daemon_client)
    except docker.errors.DockerException as e:
        ctx.logger.error("Error while getting client " + str(e))
        raise exceptions.NonRecoverableError(e)


def create_container(ctx, client):
    ctx.logger.info("Creating container")
    container_create = ctx.properties.get('container_create', {})
    try:
        cont = client.create_container(
            ctx.runtime_properties['image'],
            **container_create
        )
    except docker.errors.APIError as e:
        ctx.logger.error("Error while creating container " + str(e))
        raise exceptions.NonRecoverableError(e)
    else:
        ctx.runtime_properties.update({'container': cont['Id']})
    log_container_info(ctx, "Created container ")


def start_container(ctx, client):
    log_container_info(ctx, "Starting container")
    container_start = ctx.properties.get('container_start', {})
    try:
        client.start(
            ctx.runtime_properties['container'],
            **container_start
        )
    except docker.errors.APIError as e:
        log_error_container_logs(ctx, client, str(e))
        raise exceptions.NonRecoverableError(e)
    log_container_info(ctx, "Started container")


def stop_container(ctx, client):
    log_container_info(ctx, "Stopping container")
    container_stop = ctx.properties.get('container_stop', {})
    try:
        client.stop(
            ctx.runtime_properties['container'],
            **container_stop
        )
    except docker.errors.APIError as e:
        log_error_container_logs(ctx, client, str(e))
        raise exceptions.NonRecoverableError(e)
    log_container_info(ctx, "Stopped container")


def remove_container(ctx, client):
    container = ctx.runtime_properties['container']
    ctx.logger.info("Removing container " + container)
    container_remove = ctx.properties.get('container_remove', {})
    try:
        client.remove_container(
            container,
            **container_remove
        )
    except docker.errors.APIError as e:
        log_error_container_logs(ctx, client, str(e))
        raise exceptions.NonRecoverableError(e)
    ctx.logger.info("Removed container " + container)


def remove_image(ctx, client):
    image = ctx.runtime_properties['image']
    log_container_info(ctx, "Removing image " + image + ", container:")
    try:
        client.remove_image(image)
    except docker.errors.APIError as e:
        log_error_container_logs(ctx, client, str(e))
        raise exceptions.NonRecoverableError(e)
    log_container_info(ctx, "Removed image " + image + ", container:")


def get_top_info(ctx, client):

    def top_table(ctx, top_dictionary):
        top_table = ''
        for label in top_dictionary['Titles']:
            top_table += label + ' '
        top_table += '\n'

        for process in top_dictionary['Processes']:
            for m in process:
                top_table += m + ' '
            top_table += '\n'

        return top_table

    log_container_info(ctx, "getting TOP info of container")
    try:
        top_dictionary = client.top(ctx.runtime_properties['container'])
    except docker.errors.APIError as e:
        log_error_container_logs(ctx, client, str(e))
        raise exceptions.NonRecoverableError(e)
    else:
        return top_table(ctx, top_dictionary)


def get_container_info(ctx,  client):
    container = ctx.runtime_properties.get('container')
    if container:
        for c in client.containers():
            if container in c.values():
                return c
    return None


def inspect_container(ctx, client):
    container = ctx.runtime_properties.get('container')
    if container:
        return client.inspect_container(container)
    return None


def log_container_info(ctx, message=''):
    if 'container' in ctx.runtime_properties:
        message += ' ' + ctx.runtime_properties['container']
    ctx.logger.info(message)


def log_error_container_logs(ctx, client, message=''):
    container = ctx.runtime_properties.get('container')
    if container:
        if message:
            message += '\n'
        message += "Container: " + container
        logs = client.logs(container)
        if logs:
            message += "\nLogs:\n" + logs
    if message:
        ctx.logger.error(message)
