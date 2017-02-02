
smem -t | egrep '[M]IQ|[P]ID'
for i in `ps afx | grep [W]orker   | awk '{print $1}'`; do echo "PID: $i" && egrep --color 'VmSwap|VmRSS' /proc/$i/status && ps afx | grep $i && echo; done
# for i in `ps afx | grep [W]orker   | awk '{print $1}'`; do grep --color VmSwap /proc/$i/status; done
for file in /proc/*/status ; do awk '/VmSwap|Name/{printf $2 " " $3}END{ print ""}' $file; done | sort -k 2 -n -r | less
for file in /proc/*/status ; do awk '/VmRSS|Name/{printf $2 " " $3}END{ print ""}' $file; done | sort -k 2 -n -r | less
