#!/bin/bash

TRANSPORT=$(ifconfig eth0 | awk -F ' *|:' '/inet addr/{print $4}')
ID=$(echo $TRANSPORT | cut -d'.' -f4)

echo "*** CONTAINER PARAMS ***"
echo " TRANSPORT ADDRESS: $TRANSPORT"
echo " ID: $ID"
echo " PSK: $PSK"
echo " HOST: $HOST"
echo " PORT: $PORT"
echo "************************"
echo ""
echo ""

status="DOWN"
errsleep=60

log () {
    logger -n $HOST -t "UE-$ID" -p local7.info "$1"
}

red_log() {
    logger -n $HOST -t "UE-$ID" -p local7.info
}

reset_tunnel_dev() {
    ip tunnel del ue0 2>/dev/null || e=1
}

connect() {
    r=$(http --ignore-stdin --check-status PUT http://$HOST:$PORT/connect id=$ID psk=$PSK ip=$TRANSPORT)
    if [ $? -gt 0 ]; then
        log "Error on CONNECT"
        log " -> $r"
        return 1
    fi
    ue_ip=$(echo $r | jq -r .tunnel_ip)
    routes=$(echo $r | jq -r '.routes  | .[]')
    log "Got UE IP $ue_ip"
    
    ip tunnel add ue0 mode gre remote $HOST local $TRANSPORT key 1234
    ip link set up dev ue0
    ip addr add $ue_ip/32 dev ue0
    for uroute in $routes; do
        ip route add $uroute dev ue0
    done
    
    log "Routing table summary:"
    log "<start>"
    ip route show | red_log
    log "<end>"
}

disconnect() {
    r=$(http --ignore-stdin --check-status DELETE http://$HOST:$PORT/connect id=$ID psk=$PSK)
    ret=0
    if [ $? -gt 0 ]; then
        log "Error on DISCONNECT"
        log " -> $r"
        ret=1
    fi
    reset_tunnel_dev
    return $ret
}

get_action() {
    r=$(http --ignore-stdin --check-status GET http://$HOST:$PORT/nextaction id=$ID)
    if [ $? -gt 0 ]; then
        log "Error on NEXTACTION"
        log " -> $r"
        return 1
    fi
    echo $r
}

act_sleep() {
    time=$(echo "$1" | jq -r '.time | select( . != null )')
    [ -z $time ] && time=60
    log "ACT sleep $time"
    date
    echo "ACT sleep $time"
    sleep $time
}

act_iperf() {
    # TODO support for:
    # - parallel -P 4
    # - protocol (-u) --> --bitrate (for udp)
    # - direction (--bidir, --reverse)
    # - mss
    
    i=$(echo "$1" | jq -r '.i | select( . != null )')
    i=${i:-'1'}
    
    target=$(echo "$1" | jq -r '.target | select( . != null )')
    target=${target:-'10.211.211.211'}
    
    baseport=$(echo "$1" | jq -r '.base_port | select( . != null )')
    baseport=${baseport:-5000}
    port=$((baseport+ID))
    
    time=$(echo "$1" | jq -r '.time | select( . != null )')
    [ -z $time ] && time=10
    
    log "ACT iperf target $target time $time i $i port $port"
    echo "ACT iperf target $target time $time i $i port $port"
    iperf3 -t $time -i $i --forceflush -p $port --get-server-output --title "UE:$ID" -c $target | red_log
}

act_ping() {
    c=$(echo "$1" | jq -r '.c | select( . != null )')
    c=${c:-'4'}
    
    i=$(echo "$1" | jq -r '.i | select( . != null )')
    i=${i:-'1'}
    
    s=$(echo "$1" | jq -r '.s | select( . != null )')
    s=${s:-'100'}
    
    target=$(echo "$1" | jq -r '.target | select( . != null )')
    target=${target:-'10.211.211.211'}
    
    log "ACT ping target $target c $c i $i s $s"
    echo "ACT ping target $target c $c i $i s $s"
    ping -c $c -i $i -s $s $target | red_log
}

log "Starting APP"
reset_tunnel_dev
log " - current status: $status"


while true; do
    log "loop cycle"
    # If status is down, try connect.
    if [ "x$status" == "xDOWN" ]; then
        log "status is DOWN - connecting..."
        connect
        if [ $? -gt 0 ]; then
            # I got error on connect... at this point I will sleep
            sleep $errsleep
        else
            status="UP"
            log " - current status: $status"
        fi
    fi
    if [ "x$status" == "xUP" ]; then
        # OK, so I am up, I need to get action & execute
        a=$(get_action)
        if [ $? -gt 0 ]; then
            # I got error on action... at this point I will sleep
            sleep $errsleep
        else
            action=$(echo $a | jq -r .action)
            params=$(echo $a | jq -r .params)
            log "Got remote action $action"
            log " ... with params:"
            log "<start>"
            echo $params | red_log
            log "<end>"
            case $action in
                sleep)
                    act_sleep "$params"
                    ;;
                ping)
                    act_ping "$params"
                    ;;
                iperf)
                    act_iperf "$params"
                    ;;
                die)
                    log "I have to die... Bye."
                    disconnect
                    reset_tunnel_dev
                    echo "EXIT... Bye!"
                    exit 0
                    ;;
                *)
                    log "Unhandled action... sleeping."
                    sleep $errsleep
                    ;;
            esac
            reconn=$(echo $a | jq -r '.reconnect | select( . != null )')
            if [ "x$reconn" == "x1" ]; then
                # I have to disconnect
                disconnect
                status="DOWN"
                log "Disconnected (reconn=$reconn)"
                sleep 1
            fi
            sleepafter=$(echo $a | jq -r '.sleepafter | select( . != null )')
            if [ ! -z $sleepafter ]; then
                log "Sleepafter: $sleepafter"
                echo "Sleepafter: $sleepafter"
                sleep $sleepafter
            fi
        fi
    fi
done

