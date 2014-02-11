import logging
import atexit
from os import _exit
from signal import signal, SIGINT, SIGTERM, SIGQUIT
from socket import create_connection
from time import sleep

from docker_client import DockerClientError


log = logging.getLogger(__name__)


def running(client, container_id):
    container_info = client.inspect_container(container_id)
    return container_info and container_info[0]['State']['Running']


def successfully_destroyed(client, container_id):
    try:
        client.destroy(container_id)
        return True
    except DockerClientError, e:
        log.debug('failed to destroy container: %s', e)
        sleep(0.5)
        return False


def connectable(client, container_id, hostname, ports):
    infos = client.inspect_container(container_id)
    info = infos and infos[0]
    settings = info and info.get('NetworkSettings')
    port_settings = settings and settings.get('Ports')
    for port in ports:
        mappings = port_settings and port_settings.get('%d/tcp' % (port, ))
        if not mappings:
            return False
        for mapping in mappings:
            external = int(mapping['HostPort'])
            try:
                address = (hostname, external)
                log.debug('connecting: %s:%d', *address)
                conn = create_connection(address, 5)
                log.debug('connected: %s:%d', *address)
            except IOError, e:
                log.debug('failed to connect: %s', e)
                return False
            else:
                conn.close()
    return True


def teardown(client, containers):
    print 'Tearing down...'
    for name in containers:
        exists = True
        try:
            exists = client.inspect_container(name)
        finally:
            if exists:
                try:
                    client.kill(name)
                except:
                    pass
                try:
                    client.destroy(name)
                except:
                    pass


def register_teardown(client, containers, before=None):
    def handle_signals(signal, frame):
        before and before()
        teardown(client, containers())
        _exit(1)

    atexit.register(lambda: teardown(client, containers()))

    signal(SIGINT, handle_signals)
    signal(SIGTERM, handle_signals)
    signal(SIGQUIT, handle_signals)
