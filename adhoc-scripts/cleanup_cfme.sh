###########################################################################
################################# 57x #####################################
# cleanup appliance

# psql -U root -d vmdb_production

start=`date +"%Y-%m-%d %H:%M:%S,%3N"`

# miqtop miqvmstat
systemctl stop httpd evmserverd collectd

sync; sync; echo 3 > /proc/sys/vm/drop_caches

systemctl restart rh-postgresql95-postgresql

cd /var/www/miq/vmdb; DISABLE_DATABASE_ENVIRONMENT_CHECK=1 bin/rake evm:db:reset
cd /var/www/miq/vmdb; bin/rake db:seed

# Work around for https://bugzilla.redhat.com/show_bug.cgi?id=1337525
service httpd stop
rm -rf /run/httpd/*

mkdir -p ~/evm_logs/"$start"
mv /var/www/miq/vmdb/log/evm.log* ~/evm_logs/"$start"/
rm -rf /var/www/miq/vmdb/log/*.log*
rm -rf /var/www/miq/vmdb/log/apache/*.log*

# miqtop miqvmstat
systemctl start httpd evmserverd collectd
systemctl status httpd evmserverd collectd

end=`date +"%Y-%m-%d %H:%M:%S,%3N"`

echo "start time: $start"
echo "end time: $end"

# /'(60*60*24)' | bc -l
new_start=$(date -d "$start" +%s)
new_end=$(date -d "$end" +%s)

used=`echo "$new_end - $new_start" | bc -l`
echo "cleanup time: $used"

###########################################################################
################################# 56x #####################################

# # psql -U root -d vmdb_production
#
# start=`date +"%Y-%m-%d %H:%M:%S,%3N"`
#
# # miqtop miqvmstat
# systemctl stop httpd evmserverd collectd
#
# sync; sync; echo 3 > /proc/sys/vm/drop_caches
#
# systemctl restart rh-postgresql94-postgresql
#
# cd /var/www/miq/vmdb; bin/rake evm:dbsync:local_uninstall
# cd /var/www/miq/vmdb; DISABLE_DATABASE_ENVIRONMENT_CHECK=1 bin/rake evm:db:reset
# cd /var/www/miq/vmdb; bin/rake db:seed
#
# # Work around for https://bugzilla.redhat.com/show_bug.cgi?id=1337525
# service httpd stop
# rm -rf /run/httpd/*
# mkdir -p ~/evm_logs/"$start"
# mv /var/www/miq/vmdb/log/evm.log* ~/evm_logs/"$start"/
# rm -rf /var/www/miq/vmdb/log/*.log*
# rm -rf /var/www/miq/vmdb/log/apache/*.log*
#
# # miqtop miqvmstat
# systemctl start httpd evmserverd collectd
# systemctl status httpd evmserverd collectd
#
# end=`date +"%Y-%m-%d %H:%M:%S,%3N"`
#
# echo "start time: $start"
# echo "end time: $end"
#
# # /'(60*60*24)' | bc -l
# new_start=$(date -d "$start" +%s)
# new_end=$(date -d "$end" +%s)
#
# used=`echo "$new_end - $new_start" | bc -l`
# echo "cleanup time: $used"
