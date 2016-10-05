# cfme-performance
A repo with the goal to provide end-to-end CFME/ManageIQ performance analysis and testing. Browse each folder for more details on how to install, configure, and run each playbook/workload.

## Installing for Testing

```shell

# virtualenv cfme-performance
# cd cfme-performance
# . bin/activate
# git clone https://github.com/redhat-performance/cfme-performance.git
# cd cfme-performance
# pip install -Ur requirements.txt
```

*Note there are several rpms you may have to install depending on what is already installed in your environment.*


## Major Components
This repo is contains two major components to facilitate its goals:
* [Ansible](#ansible)
* [cfme-performance](#cfme-performance)


### Ansible
[Ansible Playbooks](ansible/)
Ansible playbooks used for deploying and managing infrastructure used in the testing framework.


### cfme-performance
[Python Testing Framework](cfme-performance/)
Testing framework used to run workloads against CFME.

The current workloads are:
* Idle (default, no websocket/git_owner roles, all roles)
* Refresh Providers
* Refresh VMs
* Capacity and Utilization
* Capacity and Utilization with Replication (pglogical and rubyrep)
* SmartState Analysis (Scans VMs)
* Provisioning

In addition to the above workloads, UI Workloads are being built and added as well.  Currently we have one experimental UI Performance workload.
* test_ui_single_page - Produces navigations to the dashboard and back to a single page.

In order to analyze UI performance you must be using Grafana and a patched appliance that has the `statsd_uiworker_patch` applied.  This can be applied via the provided Ansible playbooks.  This will allow you to view page render timings graphed over time in Grafana.  Additionally, UI workloads should be run against appliances with a pre-populated database that is representative of the environment you intend the UI to be performance tested against.
