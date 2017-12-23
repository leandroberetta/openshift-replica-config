import unittest
import subprocess
import openshift_replica_config
import os

from unittest.mock import patch


commands_executed = []


def execute_command(command):
    commands_executed.append(command)


def execute_command_error(command):
    raise subprocess.CalledProcessError(-1, command)


class OpenShiftReplicaConfigTest(unittest.TestCase):

    def test_gather_commands_by_cluster(self):
        clusters, applications = openshift_replica_config.get_config_from_yaml('openshift_replica_config_test.yaml')

        commands_by_cluster = openshift_replica_config.gather_commands_by_cluster(applications, clusters)

        self.assertIn('cluster1', commands_by_cluster)
        self.assertIn('cluster2', commands_by_cluster)

        self.assertEqual(2, len(commands_by_cluster['cluster1']))
        self.assertEqual(1, len(commands_by_cluster['cluster2']))

        self.assertIn('oc scale --replicas=3 dc app1 -n prod', commands_by_cluster['cluster1'])
        self.assertIn('oc scale --replicas=1 dc app2 -n prod', commands_by_cluster['cluster1'])
        self.assertIn('oc scale --replicas=1 dc app2 -n dev', commands_by_cluster['cluster2'])

    def test_gather_commands_by_cluster_error(self):
        clusters, applications = openshift_replica_config.get_config_from_yaml('openshift_replica_config_error_test.yaml')

        commands_by_cluster = openshift_replica_config.gather_commands_by_cluster(applications, clusters)

        self.assertIn('cluster1', commands_by_cluster)
        self.assertIn('cluster2', commands_by_cluster)

        self.assertEqual(2, len(commands_by_cluster['cluster1']))
        self.assertEqual(0, len(commands_by_cluster['cluster2']))

        self.assertIn('oc scale --replicas=3 dc app1 -n prod', commands_by_cluster['cluster1'])
        self.assertIn('oc scale --replicas=1 dc app2 -n prod', commands_by_cluster['cluster1'])
        self.assertNotIn('oc scale --replicas=1 dc app2 -n dev', commands_by_cluster['cluster2'])

    def test_execute_command_error(self):
        wrong_command = openshift_replica_config.get_login_command('', '')

        self.assertRaises(subprocess.CalledProcessError, openshift_replica_config.execute_command, wrong_command)

    def test_get_login_command(self):
        command = openshift_replica_config.get_login_command('https://cluster1:8443', 'token')

        self.assertEqual('oc login https://cluster1:8443 --token=token', command)

    @patch('openshift_replica_config.execute_command', execute_command)
    def test_get_token_exception(self):
        clusters, applications = openshift_replica_config.get_config_from_yaml('openshift_replica_config_test.yaml')

        if 'TOKEN_CLUSTER1' in os.environ:
            del os.environ['TOKEN_CLUSTER1']
        if 'TOKEN_CLUSTER2' in os.environ:
            del os.environ['TOKEN_CLUSTER2']

        commands_by_cluster = openshift_replica_config.gather_commands_by_cluster(applications, clusters)

        self.assertRaises(openshift_replica_config.TokenException,
                          openshift_replica_config.execute_commands_by_clusters,
                          commands_by_cluster,
                          clusters)

    @patch('openshift_replica_config.execute_command', execute_command)
    def test_execute_commands_by_cluster(self):
        clusters, applications = openshift_replica_config.get_config_from_yaml('openshift_replica_config_test.yaml')

        os.environ['TOKEN_CLUSTER1'] = 'token'
        os.environ['TOKEN_CLUSTER2'] = 'token'

        commands_by_cluster = openshift_replica_config.gather_commands_by_cluster(applications, clusters)

        openshift_replica_config.execute_commands_by_clusters(commands_by_cluster, clusters)


        commands_to_exec = []

        commands_to_exec.append('oc login https://cluster1:8443 --token=token')
        commands_to_exec.append('oc login https://cluster2:8443 --token=token')

        commands_to_exec = commands_to_exec + commands_by_cluster['cluster1'] + commands_by_cluster['cluster2']

        for command_to_exec in commands_to_exec:
            self.assertIn(command_to_exec, commands_executed)

    @patch('openshift_replica_config.execute_command', new=execute_command_error)
    def test_get_called_process_error(self):
        clusters, applications = openshift_replica_config.get_config_from_yaml('openshift_replica_config_test.yaml')

        os.environ['TOKEN_CLUSTER1'] = 'token'
        os.environ['TOKEN_CLUSTER2'] = 'token'

        commands_by_cluster = openshift_replica_config.gather_commands_by_cluster(applications, clusters)

        self.assertRaises(subprocess.CalledProcessError, openshift_replica_config.execute_commands_by_clusters, commands_by_cluster, clusters)


if __name__ == '__main__':
    unittest.main()