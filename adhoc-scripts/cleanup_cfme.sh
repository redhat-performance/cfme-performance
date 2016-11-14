# cleanup appliance

# login to db
# psql -U root -d vmdb_production

start=`date +"%Y-%m-%d %H:%M:%S,%3N"`

service evmserverd stop

sync; sync; echo 3 > /proc/sys/vm/drop_caches

service collectd stop
service rh-postgresql94-postgresql restart

# evm:dbsync:local_uninstall

# 5.6 requires DISABLE_DATABASE_ENVIRONMENT_CHECK=1
# cd /var/www/miq/vmdb;DISABLE_DATABASE_ENVIRONMENT_CHECK=1 bin/rake evm:db:reset
# db:seed

service collectd start

# Work around for https://bugzilla.redhat.com/show_bug.cgi?id=1337525
service httpd stop
rm -rf /run/httpd/*

service evmserverd start

end=`date +"%Y-%m-%d %H:%M:%S,%3N"`

echo "start time: $start"
echo "end time: $end"

# /'(60*60*24)' | bc -l
new_start=$(date -d "$start" +%s)
new_end=$(date -d "$end" +%s)

used=`echo "$new_end - $new_start" | bc -l`
echo "cleanup time: $used"
