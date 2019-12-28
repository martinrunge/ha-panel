#!/bin/bash

xprintidle

if [[ $(xprintidle) -gt 3000 ]]; then 
	echo "calling curl"
	/usr/bin/curl http://localhost:8080/kuechenpanel/Info
else
	echo "idle time too small"
	/usr/bin/curl http://localhost:8080/kuechenpanel/none
fi

