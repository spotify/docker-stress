#!/usr/bin/env python
import logging

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from logging import WARNING, DEBUG
from socket import create_connection
from threading import Thread
from time import sleep
from traceback import format_exc
from urlparse import urlparse
from uuid import uuid4

from mail import send_mail
from await import await, TimeoutError, PreconditionError
from docker_client import CliDockerClient, DockerClientError, DEFAULT_DOCKER_CLI, DEFAULT_DOCKER_ENDPOINT
from docker_util import running, connectable, register_teardown
from rate_limit import rate_limited
from riemann_util import get_riemann


log = logging.getLogger('docker-monitor')


@rate_limited('email', 20, 0.005)
def send_alert(email=None, message=None):
    send_mail(to=email, message=message)


def ping(hostname, port, nametag):
    sleep(10) # don't ask me why, but this makes things happy
    log.debug("connecting to %s:%s" % (hostname, port))
    s = create_connection((hostname, port))
    message = 'ping! %s' % (nametag, )
    try:
        log.debug("Sending [%s]" % message)
        s.sendall(message)
        log.debug("attempting to receive")
        reply = s.recv(64)
        if reply != message:
            raise Exception('bad reply: %s' % reply)
    finally:
        s.close()


def work(client=None, hostname=None, nametag=None):
    assert client and hostname
    name = "monitor_" + nametag + "_" + uuid4().hex[:10]
    container_id = client.start_new(image='ubuntu:12.04',
                                    command=['/bin/sh', '-c', 'apt-get install nmap -qq --force-yes && ' +
                                                         'ncat -e /bin/cat -k -l 4711'],
                                    ports=[4711],
                                    name=name)
    try:
        await('running', lambda: running(client, container_id))
        await('connectable', lambda: connectable(client, container_id, hostname, [4711]),
              precondition=lambda: running(client, container_id))
        info = client.inspect_container(container_id)
        external = int(info[0]['NetworkSettings']['Ports']['4711/tcp'][0]['HostPort'])
        ping(hostname, external, nametag)
    finally:
        client.kill(container_id)
        client.destroy(container_id)


def worker(client=None, hostname=None, interval=None, nametag=None, email=None, riemann=None):
    assert client and hostname and interval and nametag and riemann
    while True:
        try:
            log.debug("work starting")
            work(client=client, hostname=hostname, nametag=nametag)
            log.debug("work complete")
        except (DockerClientError, TimeoutError, PreconditionError), e:
            riemann.send_docker_unhealthy()
            log.error('docker is unhealthy: %s', e)
            send_alert(email=email, message='failure: %s\n\n%s' % (e, format_exc()))
        except Exception, e:
            riemann.send_docker_unhealthy()
            log.error('docker is unhealthy: %s', e)
            send_alert(email=email, message='failure: %s\n\n%s' % (e, format_exc()))
        else:
            riemann.send_docker_healthy()
            log.info('docker is healthy')
        try:
            stragglers = client.list_containers(needle=nametag)
            for container in stragglers:
                client.kill(container)
                client.destroy(container)
                log.debug('destroyed straggler: %s', container)
        except Exception, e:
            pass
        sleep(interval)


def spawn(f, *args, **kwargs):
    t = Thread(target=f, args=args, kwargs=kwargs)
    t.setDaemon(True)
    t.start()
    return t


def after(delay, f):
    sleep(delay)
    return f()


def main():
    parser = ArgumentParser(description='docker health check monitor', formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-d', '--cli', default=DEFAULT_DOCKER_CLI, help='docker cli')
    parser.add_argument('-H', '--endpoint', default=DEFAULT_DOCKER_ENDPOINT, help='docker endpoint')
    parser.add_argument('-t', '--interval', type=int, default=5 * 60, help='health check interval')
    parser.add_argument('-e', '--email', nargs='*', type=str, help='Email address to spam with failure alerts')
    parser.add_argument('-v', '--verbosity', action='count', default=0)
    parser.add_argument('-r', '--riemann', default=None, help='(optional) riemann proto:host:port to emit events to.  e.g. udp:localhost:5555')
    parser.add_argument('--syslog', help='log to syslog')

    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s %(levelname)-7s %(filename)s:%(lineno)d %(message)s',
                        level=max(DEBUG, WARNING - args.verbosity * 10))

    nametag = uuid4().hex[:10]

    client = CliDockerClient(docker=args.cli, endpoint=args.endpoint)

    register_teardown(client, lambda: client.list_containers(needle=nametag))

    riemann = get_riemann(args.riemann, 2 * args.interval, log)

    worker(client=client,
           hostname=urlparse(args.endpoint).hostname,
           interval=args.interval,
           nametag=nametag,
           email=args.email,
           riemann=riemann)


if __name__ == '__main__':
    main()
