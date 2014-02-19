#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2014 Spotify AB

import os.path

from distutils.core import setup

# Read and store version from latest changelog entry
version = open('debian/changelog').readline().split()[1][1:-1]
setup(version=version,
      packages=['spotify', 'spotify.docker_stress'],
      scripts=['docker-monitor', 
               'docker-stress']
      )
