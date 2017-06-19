"""Add collectd to sprout appliance"""
from utils.conf import cfme_performance
from utils.log import logger
from utils.ssh import SSHTail
from utils.version import get_version
from utils.version import get_current_version_string
from textwrap import dedent
import time
import yaml
import subprocess
from utils.ssh import SSHClient


def setup_collectd(perf_data):
    command_str = "until ping -c1 " + str(perf_data['appliance']['ip_address']) + " &>/dev/null; do sleep 5; done"
    print subprocess.Popen(command_str, shell=True, stdout=subprocess.PIPE).stdout.read()

    id_pub = subprocess.Popen("ssh-keygen -y -f ~/.ssh/id_rsa_t", shell=True, stdout=subprocess.PIPE).stdout.read()
    commandstring = "echo \"" + str(id_pub) + "\" > ~/.ssh/authorized_keys"
    ssh_client = SSHClient()
    ssh_client.run_command(commandstring)

    version_string = get_current_version_string()
    appliance_name_update = perf_data['appliance']['appliance_name'].replace("LATEST",version_string)
    perf_data['appliance']['appliance_name'] = appliance_name_update

    stream = open("cfme-performance/conf/data.yml", "r")
    datayml = yaml.load(stream)

    perf_data['tools']['grafana']['ip_address'] = datayml['grafana']['ip']
    perf_data['tools']['grafana']['enabled'] = 'true'
    hosts_local = "[monitorhost]\n" + str(perf_data['tools']['grafana']['ip_address']) + "\n\n"
    hosts_local = hosts_local + "[cfme-vmdb]\n" + perf_data['appliance']['appliance_name'] + "\n\n"
    hosts_local = hosts_local + "[cfme-worker]\n\n[cfme-worker]\n\n[cfme-all-in-one]\n\n[rhevm]\n"
    hostfile = open("ansible/hosts.local","w")
    hostfile.write(hosts_local)
    hostfile.close()

    cstr = "\n\tIdentityFile ~/.ssh/id_rsa_t\n\tStrictHostKeyChecking no\n\tUserKnownHostsFile=/dev/null"
    ssh_config = "Host " + perf_data['appliance']['appliance_name'] + "\n\tHostname " + perf_data['appliance']['ip_address'] + cstr
    ssh_config = ssh_config + "\nHost "+datayml['grafana']['host']+"\n\tHostname "+datayml['grafana']['ip'] + cstr
    #print ssh_config
    sshfile = open('ansible/ssh-config.local','w')
    sshfile.write(ssh_config)
    sshfile.close()

    stream = open("cfme-performance/conf/all.yml", "r")
    allstream = yaml.load(stream)
    allstream['appliances'][perf_data['appliance']['appliance_name']] = {}
    allstream['appliances'][perf_data['appliance']['appliance_name']] = allstream['appliances']['CF-B2B-R0000-test']
    del allstream['appliances']['CF-B2B-R0000-test']
    with open('ansible/group_vars/all.local.yml', 'w') as outfile:
        yaml.dump(allstream, outfile, default_flow_style=False)

    subprocess.Popen("sleep 300", shell=True)
    print subprocess.Popen("ansible-playbook -i hosts.local configure/postdeploy.yml -vvv", shell=True, stdout=subprocess.PIPE, cwd="ansible").stdout.read()
