import unittest
import yaml
import subprocess
import openshift_replica_config


class FailoverTest(unittest.TestCase):

    def setUp(self):
        with open('openshift_replica_config_test.yaml') as f:
            self.config = yaml.load(f)

            self.applications = self.config['applications']
            self.clusters = self.config['clusters']

    def test_gather_commands_by_cluster(self):
        commands_by_cluster = openshift_replica_config.gather_commands_by_cluster(self.applications, self.clusters)

        self.assertIn('cluster1', commands_by_cluster)
        self.assertIn('cluster2', commands_by_cluster)

        self.assertEqual(2, len(commands_by_cluster['cluster1']))
        self.assertEqual(1, len(commands_by_cluster['cluster2']))

        self.assertIn('oc scale --replicas=3 dc app1 -n prod', commands_by_cluster['cluster1'])
        self.assertIn('oc scale --replicas=1 dc app2 -n prod', commands_by_cluster['cluster1'])
        self.assertIn('oc scale --replicas=1 dc app2 -n prod', commands_by_cluster['cluster2'])

    def test_execute_command_error(self):
        wrong_command = openshift_replica_config.get_login_command('', '')

        self.assertRaises(subprocess.CalledProcessError, openshift_replica_config.execute_command, wrong_command)