#!/usr/bin/env bash

coverage3 run openshift_replica_config_test.py
coverage3 html --omit openshift_replica_config_test.py
