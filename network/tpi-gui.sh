#============================================================
# This is the GUI program for TrendNet TPI-06 PDU control.
# Requires yad package. Install with:
#   sudo apt install yad
#============================================================
#!/bin/bash

# --- CONFIGURATION ---
PDU_IP="172.16.0.80"
USER="admin"
PASS='Dit!BjTCyf66'

# --- API FUNCTION ---
pdu_action() {
    local PORT=$1
    local STATE=$2
    local ACTION_NAME=$([ "$STATE" -eq 1 ] && echo "ON" || echo "OFF")
    
    # 1. AUTHENTICATION
    LOGIN_RESPONSE=$(curl -s -X POST "http://$PDU_IP/api/sys/login" \
       -H "Content-Type: text/plain;charset=UTF-8" \
       -d "{\"userLogin\":{\"usr\":\"$USER\",\"pwd\":\"$PASS\"}}")

    TOKEN=$(echo "$LOGIN_RESPONSE" | sed -n 's/.*"token":"\([^"]*\)".*/\1/p')

    if [ -z "$TOKEN" ]; then
        yad --error --title="PDU Error" --text="Login failed for Port $PORT" --timeout=3 &
        return
    fi

    # 2. EXECUTE COMMAND
    RESULT=$(curl -s -X PUT "http://$PDU_IP/api/overview/outlet/enable" \
       -H "Authorization: bearer $TOKEN" \
       -H "Content-Type: text/plain;charset=UTF-8" \
       -d "{\"outletEnConfs\":{\"outlet_id\":$PORT,\"outlet_enable\":$STATE}}")

    # 3. SHOW RESULT BOX
    if [[ "$RESULT" == *"success"* ]]; then
        # This creates a small popup that disappears after 2 seconds
        yad --info --title="PDU Status" --text="Port $PORT: <b>$ACTION_NAME SUCCESS</b>" --timeout=2 --no-buttons &
    else
        yad --error --title="PDU Status" --text="Port $PORT: <b>FAILED</b>\n$RESULT" --timeout=5 &
    fi
}

export -f pdu_action
export PDU_IP USER PASS

# --- THE GUI ---
# Using :fbtn (Function Button) ensures the main window stays open.
yad --form --title="PDU Power Control Center" \
    --columns=2 --width=350 --fixed \
    --text="<b>Select a port to toggle power:</b>" \
    --field="SmartLynq:LBL" "" \
    --field="ON!gtk-media-play":fbtn "bash -c 'pdu_action 1 1'" \
    --field="OFF!gtk-media-stop":fbtn "bash -c 'pdu_action 1 0'" \
    --field="Port 2:LBL" "" \
    --field="ON!gtk-media-play":fbtn "bash -c 'pdu_action 2 1'" \
    --field="OFF!gtk-media-stop":fbtn "bash -c 'pdu_action 2 0'" \
    --field="PicoZed:LBL" "" \
    --field="ON!gtk-media-play":fbtn "bash -c 'pdu_action 3 1'" \
    --field="OFF!gtk-media-stop":fbtn "bash -c 'pdu_action 3 0'" \
    --field="GeRM:LBL" "" \
    --field="ON!gtk-media-play":fbtn "bash -c 'pdu_action 4 1'" \
    --field="OFF!gtk-media-stop":fbtn "bash -c 'pdu_action 4 0'" \
    --field="Port 5:LBL" "" \
    --field="ON!gtk-media-play":fbtn "bash -c 'pdu_action 5 1'" \
    --field="OFF!gtk-media-stop":fbtn "bash -c 'pdu_action 5 0'" \
    --field="KR260:LBL" "" \
    --field="ON!gtk-media-play":fbtn "bash -c 'pdu_action 6 1'" \
    --field="OFF!gtk-media-stop":fbtn "bash -c 'pdu_action 6 0'" \
    --button="Exit:0"
