# openshift-replica-config

The script sets the DeploymentConfig's replica value of applications in several clusters.

## Usage

    ./openshift-replica-config.py -h

### Authentication

The script uses service accounts token to log into OpenShift.

Every cluster configured needs an environment variable present in the OS.

    TOKEN_{CLUSTER}={TOKEN}

#### Example

For the cluster 'cluster1':

    export TOKEN_CLUSTER1={TOKEN}

## Config file

    clusters:
      - name: cluster1
        url: https://cluster1.com:8443
      - name: telecom
        url: https://cluster2.com:8443
    applications:
      - name: app1
        replicas:
          - cluster: cluster1
            pods: 3
      - name: app2
        replicas:
          - cluster: cluster1
            pods: 1
          - cluster: cluster2
            pods: 1
