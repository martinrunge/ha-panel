#!/bin/bash

OWNDIR=$(dirname $0)


if [[ ! -x $(which xidle) ]]; then 
	echo "'xidle' executable not found. Please install it first."
	exit -1
fi

if [[ ! -x $(which wmctrl) ]]; then
	echo "'wmctrl' executable not found. Please install it first."
	exit -1
fi

xrandr --output HDMI-1 --gamma 2.2:2.2:2.2


${OWNDIR}/../scripts/doorbird.sh --minimized &
${OWNDIR}/../scripts/ha-panel.sh &

sleep 10

nohup xidle -program ${OWNDIR}/notify-idle.sh -timeout 300  &

