docker-{stress,monitor}
=======================

Simple Docker (http://docker.io/) stress testing and monitoring tools.

    $ ./docker-stress.py
    usage: docker-stress.py [-h] [-f JOBS] [-d CLI] [-H ENDPOINT] [-c CONCURRENCY]
                            [-e [EMAIL [EMAIL ...]]] [-v]

    docker stress test

    optional arguments:
      -h, --help            show this help message and exit
      -f JOBS, --jobs JOBS  jobs file (default: jobs.json)
      -d CLI, --cli CLI     docker cli (default: /usr/bin/docker)
      -H ENDPOINT, --endpoint ENDPOINT
                            docker endpoint (default: unix:///var/run/docker.sock)
      -c CONCURRENCY, --concurrency CONCURRENCY
                            number of containers to run concurrently (default: 1)
      -e [EMAIL [EMAIL ...]], --email [EMAIL [EMAIL ...]]
                            Email address to spam with failure alerts (default:
                            None)
      -v, --verbosity

    $ ./docker-monitor.py
    usage: docker-monitor.py [-h] [-d CLI] [-H ENDPOINT] [-t INTERVAL]
                             [-e [EMAIL [EMAIL ...]]] [-v] [--syslog SYSLOG]

    docker health check monitor

    optional arguments:
      -h, --help            show this help message and exit
      -d CLI, --cli CLI     docker cli (default: /usr/bin/docker)
      -H ENDPOINT, --endpoint ENDPOINT
                            docker endpoint (default: unix:///var/run/docker.sock)
      -t INTERVAL, --interval INTERVAL
                            health check interval (default: 300)
      -e [EMAIL [EMAIL ...]], --email [EMAIL [EMAIL ...]]
                            Email address to spam with failure alerts (default:
                            None)
      -v, --verbosity
      --syslog SYSLOG       log to syslog (default: None)