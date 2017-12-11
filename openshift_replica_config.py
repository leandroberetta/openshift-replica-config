#!/usr/bin/env python3

import yaml
import argparse
import subprocess
import os
import logging


def config_logging():
    logging.basicConfig(filename='openshift_replica_config.log', level=logging.INFO)


def get_config_from_yaml(config_file):
    return yaml.load(open(config_file))


def create_parser():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('config_file', metavar='config_file', type=str, help='configuration file')

    return parser


def get_input_parameters_if_valid():
    parser = create_parser()

    parameters = parser.parse_args()

    if parameters.mode == 'restore':
        return parameters.config_file, parameters.mode, None
    elif parameters.mode == 'failover' and parameters.cluster is not None:
        return parameters.config_file, parameters.mode, parameters.cluster
    elif parameters.mode != 'restore' and parameters.mode != 'failover':
        parser.error("mode is restore or failover.")
    else:
        parser.error("if mode is failover, --cluster is required.")


def gather_commands_by_cluster(applications, clusters):
    SCALE_COMMAND = 'oc scale --replicas={} dc {} -n prod'
    commands_by_cluster = {}

    for cluster in clusters:
        logging.info('generating commands list for {}'.format(cluster['name']))
        commands_by_cluster[cluster['name']] = []

    for application in applications:
        logging.info('gathering commands for {}'.format(application['name']))

        for replica in application['replicas']:
            try:
                command = SCALE_COMMAND.format(replica['pods'], application['name'])

                logging.info('command: "{}" for cluster {}'.format(command, replica['cluster']))

                commands_by_cluster[replica['cluster']].append(command)
            except KeyError:
                logging.error('{} not in the clusters list'.format(replica['cluster']))

    return commands_by_cluster


def gather_commands_by_failover_cluster(commands_by_cluster, failover_cluster):
    logging.info('keeping commands for cluster {}'.format(failover_cluster))

    return {failover_cluster: commands_by_cluster[failover_cluster]}


def execute_command(command):
    logging.info('executing command "{}"'.format(command))

    output = subprocess.check_output(command.split(' '), stderr=subprocess.STDOUT)

    logging.info('command output is "{}"'.format(output))


def get_token_for_cluster(cluster):
    env_var_name = 'TOKEN_' + cluster.upper()
    env_var_value = os.environ.get(env_var_name)

    logging.info('looking for env var {} in os'.format(env_var_name))

    if env_var_value is None:
        message = 'env var {} is not defined'.format(env_var_name)

        logging.error(message)

        raise TokenException(message)

    logging.info('env var {} found in os'.format(env_var_name))

    return os.environ.get(env_var_name)


def get_login_command(url, token):
    return 'oc login {} --token={}'.format(url, token)


def execute_commands_by_clusters(commands_by_cluster, clusters):
    logging.info('executing commands...')

    logging.info('gathering clusters url')
    clusters_url = {}
    for cluster in clusters:
        logging.info('url for cluster {} is {}'.format(cluster['name'], cluster['url']))
        clusters_url[cluster['name']] = cluster['url']

    try:
        for cluster, commands in commands_by_cluster.items():
            execute_command(get_login_command(clusters_url[cluster], get_token_for_cluster(cluster)))

            for command in commands:
                execute_command(command)
    except subprocess.CalledProcessError as e:
        logging.error('command failed with error {}'.format(e.output))

        print('error: see the log file')


class TokenException(Exception):
    pass


if __name__ == '__main__':
    config_logging()

    logging.info('failover process starting...')
    parser = create_parser()
    parameters = parser.parse_args()

    logging.info('getting configuration file from {}'.format(parameters.config_file))

    # Gets the YAML configuration
    config = get_config_from_yaml(parameters.config_file)

    clusters = config['clusters']
    applications = config['applications']

    # Gathers commands by clusters
    commands_by_cluster = gather_commands_by_cluster(applications, clusters)

    # Executes commands by clusters
    execute_commands_by_clusters(commands_by_cluster, clusters)