#!/bin/bash

xprintidle

if [[ $(xprintidle) -gt 3000 ]]; then 
	echo "$(date +%F\ \ %T) got idle" >> ~/tmp/notify-idle.log
	/usr/bin/curl http://localhost:8080/kuechenpanel/idle
else
	echo "$(date +%F\ \ %T)  idle time too small, assuming gettting active" >> ~/tmp/notify-idle.log 
	/usr/bin/curl http://localhost:8080/kuechenpanel/none
fi

