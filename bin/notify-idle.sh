#!/bin/bash

xprintidle

if [[ $(xprintidle) -gt 3000 ]]; then 
	echo "calling curl"
	/usr/bin/curl http://localhost:8080/idle
else
	echo "idle time too small"
fi

