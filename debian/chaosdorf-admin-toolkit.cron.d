# /etc/cron.d/nagios-run-checks

PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
MAILTO=root

0,5,10,20,25,30,35,40,45,50,55 * * * * nagios /usr/lib/nagios/run_checks 2> /dev/null
15 * * * * nagios /usr/lib/nagios/run_checks 60 2> /dev/null
