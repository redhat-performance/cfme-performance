curl -XDELETE http://admin:admin@10.12.23.122:9201/cfme-*
curl -XDELETE http://admin:admin@10.12.23.122:9201/_template/cfme*
./es-create-cfme-templates
./postprocess/cfme_csv2elastic.py ../results/20170105161527-workload-cap-and-util-5.7.0.1/

