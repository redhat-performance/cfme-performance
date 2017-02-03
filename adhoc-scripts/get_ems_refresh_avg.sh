#!/bin/bash

# optional prerequisites for visulizing timings on bash
# sh -c "curl https://raw.githubusercontent.com/holman/spark/master/spark -o /usr/local/bin/spark && chmod +x /usr/local/bin/spark"

logfile=$1
# last_lines=$2
last_events=$2
log_start=$3
log_end=$4
ems_event_id=$5

cd /var/www/miq/vmdb/log/

if [[ $* -eq 0 ]]; then
  evm_log='/var/www/miq/vmdb/log/evm.log'
  logfile='ems_refresh_last_avg.log'
  last_events=20
  log_start='2016-12-13T09:48'
  log_end='2016-12-13T10:48'
  ems_event_id='EmsRefresh.refresh' #|ems_refresh
fi

echo > ~/$logfile

echo This reading was recorded on: `date +"%Y-%m-%d %H:%M:%S,%3N"` >> ~/$logfile

echo "...Reading logs from $evm_log
      and extracting last $last_events events.
      Begin time: $log_start
      End time: $log_end" >> ~/$logfile

# get inventory refresh timings
log_frag="$(awk -F'[]]|[[]| ' '$0 ~ /^\[----\] I, \[/ &&
                   $6 >= "'$log_start'" { p=1 }
                   $6 >= "'$log_end'" { p=0 } p { print $0 }' \
                   $evm_log )"

ids=(`echo "$log_frag" | egrep '('$ems_event_id')' |  grep ready | \
                   grep MiqQueue.put\) | grep -oE '(Message id: \[[0-9]*\])' | \
                   sed 's/Message id: \[//' | sed 's/.\{1\}$//' | tail -n $last_events`)

echo "${#ids[@]} IDs found.." >> ~/$logfile

timings=()
timestamps=()
for current_id in ${ids[@]}; do
  matched=`echo "$log_frag" | grep -oE '.*(Message id: \['$current_id'\].*Delivered in \[[0-9]*.[0-9]*\])'`
  timings+=(`echo "$matched" | sed 's/.*Delivered in \[//' | sed 's/.\{1\}$//'`)
  timestamps+=(`echo $matched | awk -F'[]]|[[]| ' '{print $6}'`)
done

echo >> ~/$logfile
printf '%s\t | %s\t\t\t | %s | %s\n' "#" "Timestamp" "IDs" "$ems_event_id" >> ~/$logfile
printf "%0.s-" {1..70} >> ~/$logfile
echo >> ~/$logfile

echo "${#timings[@]} ${#ids[@]} ${#timestamps[@]}"
for ((i=0; i<${#timings[@]}; i++)); do
    printf '%s\t | %s\t | %s | %s\n' "$i" "`date -d ${timestamps[i]}`" "${ids[i]}" "${timings[i]}" >> ~/$logfile
done
printf "%0.s-" {1..70} >> ~/$logfile
echo >> ~/$logfile

total=`echo "${timings[@]}" |tr ' ' '\n' | awk '{sum+=$1};END{print sum}'`
# awk '{print substr($0, 2, length($0) - 2)}'
average=`echo "$total/${#timings[@]}" | bc -l`

if [[ -f /usr/local/bin/spark ]]; then
  spark ${timings[@]} >> ~/$logfile
fi

printf "Average: $average\n" >> ~/$logfile
printf "%0.s-" {1..70} >> ~/$logfile
echo >> ~/$logfile
echo "${#ids[@]} events were queued, out of which ${#timings[@]} events were delivered with [ok] status..." >> ~/$logfile

echo "showing output from log file: ~/$logfile:"
cat ~/$logfile
cd ~
