#!/bin/bash

SCRIPTDIR=$(dirname $0)
SCRIPTNAME=$(basename $0)
PIDFILE=${SCRIPTDIR}/../run/${SCRIPTNAME}.pid

if [ -f $PIDFILE ]; then
	echo "alread running as pid: $(cat $PIDFILE)"
	${SCRIPTDIR}/../../build/QDoorBirdViewer $@

	mapfile -t LINES < <(/usr/bin/wmctrl -lp)

	for LINE in "${LINES[@]}"
	do
	    # echo "$LINE"
	    wid=$(echo $LINE | awk '{print $1}') 
	    pid=$(echo $LINE | awk '{print $3}')
	    # echo "wid: $wid  pid: $pid"
	    if [ $pid -eq $(cat $PIDFILE) ]; then
            /usr/bin/wmctrl -i -a $wid
	    fi
	done	

fi

[ "${FLOCKER}" != "$0" ] && exec env FLOCKER="$0" flock -en "$0" "$0" "$@" || : 

trap 'rm -f $PIDFILE' EXIT

${SCRIPTDIR}/../../build/QDoorBirdViewer $@ &> ~/tmp/QDoorBirdViewer.log &
CHILDPID=$!
echo "$CHILDPID" > $PIDFILE 

trap 'kill $CHILDPID; rm -f $PIDFILE' EXIT

echo "running in pid $CHILDPID"
wait $CHILDPID
echo "finished"

