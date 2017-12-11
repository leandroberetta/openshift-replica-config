import unittest
import yaml
import openshift_replica_config


class FailoverTest(unittest.TestCase):

    def setUp(self):
        config = yaml.load(open('openshift_replica_config_test.yaml'))

        self.applications = config['applications']
        self.clusters = config['clusters']

    def test_gather_commands_by_cluster(self):
        commands_by_cluster = openshift_replica_config.gather_commands_by_cluster(self.applications, self.clusters)

        self.assertIn('cluster1', commands_by_cluster)
        self.assertIn('cluster2', commands_by_cluster)

        self.assertEquals(2, len(commands_by_cluster['cluster1']))
        self.assertEquals(1, len(commands_by_cluster['cluster2']))

        self.assertIn('oc scale --replicas=3 dc app1 -n prod', commands_by_cluster['cluster1'])
        self.assertIn('oc scale --replicas=1 dc app2 -n prod', commands_by_cluster['cluster1'])
        self.assertIn('oc scale --replicas=1 dc app2 -n prod', commands_by_cluster['cluster2'])
