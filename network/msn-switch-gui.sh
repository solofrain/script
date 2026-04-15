#!/bin/bash

SWITCH_IP="10.1.1.207"
USER="msn"
ENC_PASS="a%25%2B7xi2TA4U%2CR"
COOKIE_FILE="/tmp/msn_cookie.txt"
OUTLET1="KR260"
OUTLET2="Motor"

switch_action() {
    local TARGET=$1
    local CONTROL=$2

    # Login
    curl -s -L -c "$COOKIE_FILE" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      --data-raw "login=1&user=$USER&password=$ENC_PASS" \
      "http://$SWITCH_IP/goform/login" >/dev/null

    # Extract CSRF token
    CSRFTOKEN=$(curl -s -b "$COOKIE_FILE" \
      "http://$SWITCH_IP/status.asp" \
      | tr '\n' ' ' \
      | sed -n 's/.*id="csrftoken"[^>]*value="\([^"]*\)".*/\1/p')

    [ -z "$CSRFTOKEN" ] && return

    # Send control
    curl -s -b "$COOKIE_FILE" \
      "http://$SWITCH_IP/cgi-bin/control.cgi?target=$TARGET&control=$CONTROL&time=$(date +%s%3N)&csrftoken=$CSRFTOKEN" \
      >/dev/null
}

export -f switch_action
export SWITCH_IP USER ENC_PASS COOKIE_FILE


yad --form \
    --title="MSNSwitch Power Control Center" \
    --width=520 \
    --columns=2 \
    --field="<b>$OUTLET1</b>:LBL" "" \
    --field="ON":fbtn "bash -c 'switch_action 1 1'" \
    --field="OFF":fbtn "bash -c 'switch_action 1 0'" \
    --field="RESET":fbtn "bash -c 'switch_action 1 3'" \
    --field="<b>All Devices</b>:LBL" "" \
    --field="ALL ON":fbtn "bash -c 'switch_action 3 1'" \
    --field="<b>$OUTLET2</b>:LBL" "" \
    --field="ON":fbtn "bash -c 'switch_action 2 1'" \
    --field="OFF":fbtn "bash -c 'switch_action 2 0'" \
    --field="RESET":fbtn "bash -c 'switch_action 2 3'" \
    --field="<b></b>:LBL" "" \
    --field="ALL OFF":fbtn "bash -c 'switch_action 3 0'" \
    --button="Exit:0"
