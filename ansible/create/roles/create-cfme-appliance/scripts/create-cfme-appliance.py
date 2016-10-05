#!/usr/bin/env python

import ast
import sys
import time
from ovirtsdk.api import API
from ovirtsdk.xml import params
from ovirtsdk.infrastructure.errors import RequestError

appliance = ast.literal_eval(sys.argv[1])
rhevm_hostname = sys.argv[2]
user = sys.argv[3]
passw = sys.argv[4]
item_type = sys.argv[5]

MB = 1024 * 1024
GB = 1024 * MB

ca = '/tmp/rhevm_appliance_certs/{}'.format(rhevm_hostname)
rhevm_url = 'https://{}'.format(rhevm_hostname)

api = API(url=rhevm_url, username=user, password=passw, ca_file=ca)


def already_moved(domain_object, disk):
    return disk.storage_domains.storage_domain[0].id == domain_object.id


def locked_disks(vm):
    disk_list = vm.disks.list()
    for disk_reference in disk_list:
        disk = api.disks.get(id=disk_reference.id)
        if disk.status.state == 'locked':
            return True
    return False


def prepare_rhevm_template():
    tmp = {
        'template_disks': params.Disks(clone=appliance['clone_template']),
        'cluster_object': api.clusters.get(name=appliance['cluster']),
        'host_object': api.hosts.get(appliance['host']),
        'migrate': appliance['migrate'],
        'appliance_nics': appliance['NICS'][:],
        'appliance_memory': appliance['memory_size'],
        'appliance_type': appliance['vm_type'],
        'num_cores': appliance['cores'],
        'num_cpus': appliance['cpus'],
        'storage_name': appliance['disk_location'],
        'disks': appliance['disks']
    }

    tmp['cpu_topology'] = params.CpuTopology(
        cores=tmp['num_cores'],
        threads=tmp['num_cpus'])
    tmp['cpu_object'] = params.CPU(topology=tmp['cpu_topology'])
    tmp['domain_object'] = api.storagedomains.get(name=tmp['storage_name'])
    tmp['actions'] = params.Action(storage_domain=tmp['domain_object'])
    tmp['placement_object'] = params.VmPlacementPolicy(
        host=tmp['host_object'],
        affinity=tmp['migrate'])
    return tmp


def trigger_add_vm(**kwargs):

    vm_params = params.VM(
        name=kwargs['vm_name'],
        template=kwargs['template_object'],
        disks=kwargs['template_disks'],
        cluster=kwargs['cluster_object'],
        host=kwargs['host_object'],
        cpu=kwargs['cpu_object'],
        memory=kwargs['appliance_memory'] * GB,
        placement_policy=kwargs['placement_object'],
        type_=kwargs['appliance_type'])

    try:
        cfme_appliance = api.vms.add(vm_params)
    except RequestError as E:
        print("Error while creating vm(s)")
        sys.exit(E)

    while cfme_appliance.status.state == 'image_locked':
        time.sleep(10)
        cfme_appliance = api.vms.get(name=kwargs['vm_name'])

    for disk in kwargs['disks']:
        disk_size = kwargs['disks'][disk]['size'] * GB
        interface_type = kwargs['disks'][disk]['interface']
        disk_format = kwargs['disks'][disk]['format']
        allocation = kwargs['disks'][disk]['allocation']
        location = kwargs['disks'][disk]['location']
        store = api.storagedomains.get(name=location)
        domain = params.StorageDomains(storage_domain=[store])
        disk_param = params.Disk(
            description=disk,
            storage_domains=domain,
            size=disk_size,
            interface=interface_type,
            format=disk_format,
            type_=allocation)
        new_disk = cfme_appliance.disks.add(disk=disk_param)

    if len(kwargs['appliance_nics']) > 0:
        current_nics = cfme_appliance.get_nics().list()
        current_networks = []
        for nic in current_nics:
                network_id = nic.get_network().id
                current_networks.append(api.networks.get(id=network_id).name)

        new_set = set(kwargs['appliance_nics'])
        current_set = set(current_networks)
        appliance_nics = list(new_set - current_set)

    for i in range(len(appliance_nics)):
        network_name = params.Network(name=appliance_nics[i])
        nic_name = params.NIC(name='card{}'.format(i), network=network_name)
        cfme_appliance.nics.add(nic=nic_name)

    while locked_disks(cfme_appliance):
        time.sleep(10)
        cfme_appliance = api.vms.get(name=kwargs['vm_name'])

    dev = params.Boot(dev='network')
    cfme_appliance.os.boot.append(dev)
    cfme_appliance.update()

    for disk in cfme_appliance.disks.list():
        if disk.description in appliance['disks'] \
                or already_moved(kwargs['domain_object'], disk):
            continue
        disk.move(action=kwargs['actions'])

    cfme_appliance = api.vms.get(name=kwargs['vm_name'])
    while locked_disks(cfme_appliance):
        time.sleep(10)
        cfme_appliance = api.vms.get(name=kwargs['vm_name'])

    cfme_appliance.start()


def run():
    obj_dict = prepare_rhevm_template()

    if item_type == 'multiple_vms':
        for vm in appliance['vms']:
            obj_dict['vm_name'] = vm['vm_name']
            obj_dict['template_object'] = api.templates.get(name=vm['template'])
            trigger_add_vm(**obj_dict)
    elif item_type == 'single_vm':
        obj_dict['vm_name'] = appliance['vm_name']
        obj_dict['template_object'] = api.templates.get(name=appliance['template'])
        trigger_add_vm(**obj_dict)

    api.disconnect()


if __name__ == '__main__':
    run()
