#!/bin/bash

logfile=$1


if [[ $* -eq 0 ]]; then
  logfile='ose-cfme.log'
fi

date +"%Y-%m-%d %H:%M:%S,%3N" >> $logfile

infra_and_master_nodes=('192.1.23.66' '192.1.23.67' '192.1.23.68' '192.1.23.73' '192.1.23.74' '192.1.23.100')
exclude_pattern="($(echo ${infra_and_master_nodes[@]} | tr ' ' '|'))"

# get all non-master nodes excluding $NODE_TYPE
EXCLUDE_NODE_TYPE='NotReady'
# EXCLUDE_NODE_TYPE='Ready'
TYPE_NODES=(`oc get nodes | egrep -v $exclude_pattern | egrep -v '(^.*\s'$EXCLUDE_NODE_TYPE'.*$|NAME)' | awk -F' ' '{print $1}'`)
echo "Nodes count after excluding type '$EXCLUDE_NODE_TYPE': ${#TYPE_NODES[@]}" >> $logfile

# # first 3
# echo ${TYPE_NODES[@]::3}
# # excluding first 290
# echo ${TYPE_NODES[@]:290}

for i in ${TYPE_NODES[@]:3}; do
  # disconnect/connect node
  ssh root@$i "systemctl stop atomic-openshift-node" &
  # ssh root@$i "systemctl start atomic-openshift-node" &

  # deschedule / schedule nodes
  # oadm manage-node $i --schedulable=false
  # oadm manage-node $i --schedulable=true
  echo "processed node: $i"
done


# sleep for sometime for OSE to realize this
sleep 15

# nested ssh commands
# # sshpass -p password ssh  -T root@192.1.21.206 <<EOB
# ssh -F ssh-config.local -T root@jumphost-ose.svt-j <<EOA
# ssh -T root@192.1.21.206 <<EOB
# oc get pods
# EOB
# EOA

# oc cluster up
# oc login -u system:admin -n default
# oadm policy add-cluster-role-to-user cluster-admin admin --config=/var/lib/origin/openshift.local.config/master/admin.kubeconfig
# oadm policy add-role-to-user cluster-admin admin
# oc get pods
# oc get route

# delete projects
# for i in `oc get projects | grep clusterproject | awk -F' ' '{print $1}'`; do oc delete project $i; done

date +"%Y-%m-%d %H:%M:%S,%3N" >> $logfile

# journalctl -fu atomic-openshift-master | grep -E "E0720|F0720"

# for node in `oc get nodes | grep 'NotReady ' | awk '{print $1}'`; do ping -c 1  $node >> test_alive; done
# sed -n -e 's#^.*com (\(.*\)): icmp_seq.*#\1#p' test_alive
# for i in `oc get nodes | grep '18x1x.\.' | awk '{print $1}'`; do oc delete node $i; done
#
# token=$(oc sa get-token -n management-infra management-admin)
# curl -L -H "Authorization: Bearer $token" -k -XGET https://10.16.31.50:8443/oapi/v1/imagestreams > is.json
# egrep 'hello.*@sha256' is.json -m 10 | sed -n -e 's#.*/admin/hello[0-9]*@\(sha256.*\)",#\1#p'
# for i in `egrep 'hello.*@sha256' is.json -m 5000 | sed -n -e 's#.*/admin/hello[0-9]*@\(sha256.*\)",#\1#p'`; do oc delete image $i; done
