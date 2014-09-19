#!/bin/sh

QPKG_PKG_DIR=/share/XXX/custom-webserver
PID_FILE=/var/run/custom-webserver.pid

JAVA_CMD=/usr/local/bin/java

case $1 in

	start)
		# start script here
		cd $QPKG_PKG_DIR/lib/
		$JAVA_CMD WebServer $QPKG_PKG_DIR/public_html/ 7777 > /dev/null &
		echo $! > $PID_FILE
		;;

	stop)
		# stop script here
		kill -9 `cat $PID_FILE` 2> /dev/null
		rm -rf $PID_FILE
		;;

	*)
		echo "usage: $0 {start|stop}"
		exit 1
		;;
		
esac

exit 0
