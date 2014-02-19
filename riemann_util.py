from socket import gethostname, error

class RiemannReporter:
    def __init__(self, client, default_ttl = 600):
        self.hostname = gethostname()
        self.service = 'docker-monitor'
        self.client = client
        self.default_ttl = default_ttl

    def send(self, attrs):
        if not self.client:
            return
        d = {'host': self.hostname, 'service': self.service, "ttl": self.default_ttl}
        d.update(attrs)
        try:
            log.error("sending %s" % (d,))
            self.client.send(d)
        except error, e:
            log.error("error caught attempting to send to riemann %s", e)

    def send_docker_unhealthy(self):
        self.send({'description': 'docker is unhealthy', 'state': 'critical', 
                   'tags': ['docker', 'error'], 'metric': 0})

    def send_docker_healthy(self):
        self.send({'description': 'docker is in a happy place', 'state': 'ok',
                   'tags': ['docker'], 'metric': 1})


def get_riemann(riemann_arg, default_ttl, log_param):
    import bernhard
    client = None
    if riemann_arg:
        global log
        log = log_param
        protocol, host, port = riemann_arg.split(':')
        port = int(port)
        if protocol == 'udp':
            proto_impl = bernhard.UDPTransport
        elif protocol == 'tcp':
            proto_impl = bernhard.TCPTransport
        else:
            log.error("protocol [%s] is not valid.  Should be udp or tcp" % protocol)
        client = bernhard.Client(host, port, transport = proto_impl)
    return RiemannReporter(client, default_ttl)
