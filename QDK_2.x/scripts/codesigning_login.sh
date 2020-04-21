#!/bin/bash

SERVER=codesigning.qnap.com.tw
SCRIPTPATH="$( cd "$(dirname "$0")" ; pwd -P )"
read -p 'username: ' USERNAME
read -sp 'password: ' PASSWORD
echo
USERNAME=$(python -c "import urllib; print urllib.quote('''$USERNAME''')")
PASSWORD=$(python -c "import urllib; print urllib.quote('''$PASSWORD''')")
RESPONSE="$(eval "curl -X POST --cacert ${SCRIPTPATH}/codesigning_cert.pem -d \"username=${USERNAME}&password=${PASSWORD}\" \
	https://${SERVER}:5001/login 2>/dev/null")"
RET=$?
# If curl not installed
if [ $RET -eq 127 ]; then
	echo 'Cannot find curl command'
	exit 1
fi
if [ $RET -eq 7 ]; then
	echo 'Failed to connect to server'
	exit 1
fi
if ! [ $RET -eq 0 ]; then
	echo 'Error when running curl command'
	exit 1
fi
ERROR="$(echo "$RESPONSE" | python -c 'import sys, json; print json.load(sys.stdin)["error"]')"
MSG="$(echo "$RESPONSE" | python -c 'import sys, json; print json.load(sys.stdin)["msg"]')"
if [ "$ERROR" -ne 0 ]; then
	echo $MSG
	exit 1
fi
TOKEN="$(echo "$RESPONSE" | python -c 'import sys, json; print json.load(sys.stdin)["token"]')"
echo "Token: $TOKEN"
