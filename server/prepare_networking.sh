#!/bin/bash

## Common Functions
create_vrf () {
    vrf=$1
    table=$2

    ip link add ${vrf} type vrf table ${table}
    ip link set dev ${vrf} up
    ip route add table ${table} unreachable default metric 4278198272
    ip rule add iif ${vrf} table ${table}
    ip rule add oif ${vrf} table ${table}

}

create_dummy () {
    name=$1
    ip link add ${name} type dummy
}

configure_interface_vrf () {
    iface=$1
    addr=$2
    vrf=$3

    ip link set ${iface} master ${vrf}
    ip link set up dev ${iface}

    ip addr add ${addr} dev ${iface}
}

configure_interface_pbr () {
    iface=$1
    addr=$2
    table=$3
    seq=$4
    network=$5

    ip link set up dev ${iface}

    ip addr add ${addr} dev ${iface}

    ip rule add pref ${seq} from ${network} lookup ${table}
    ip rule add pref ${seq} from ${network} blackhole

    ip route add ${network} dev ${iface} table ${table}
}

static_route () {
    table=$1
    network=$2
    destination=$3

    ip route add ${network} via ${destination} table ${table}
}

# VRF & Intf to Handle "N6" connectivity
create_vrf n6 6
configure_interface_vrf eth2 10.211.100.1/24 n6

# Static route or BGP?
# if needed:
static_route 6 10.211.211.0/24 10.211.100.100


# FAKE-VRF (PBR) to handle connection towards Fake-UE
### DISABLED FOR NOW.
#create_dummy lo_ran
#configure_interface_pbr lo_ran 10.255.255.2/32 200 10 10.255.255.2/32
#configure_interface_pbr eth1 10.250.2.102/24 200 11 10.250.2.0/24



### BIRD CONFIGURATION


echo > /etc/bird.conf
cat <<EOT >> /etc/bird.conf

log syslog all;

filter Export_N6
{
    if ( ifname = "up0" ) then accept;
    reject;
};

filter Export_RAN
{
    if ( net = 10.255.255.2/32 ) then accept;
    reject;
};

router id 10.211.100.1;

ipv4 table VRF_N6;
ipv4 table VRF_RAN;

template kernel tpl_k {
    scan time 5;
    learn;
    merge paths yes;
    persist yes;

    ipv4 {
        import all;
        export where source ~ [ RTS_STATIC, RTS_BGP ];
    };
}

template direct tpl_dir {
    ipv4 {
        import all;
    };
}

protocol device dvc {
    scan time 5;
    interface "lo_*";
    interface "eth*";
    interface "up*";
}

template bgp tpl_bgp {
    local as 100;
    ipv4 {
        import all;
        export none;
    };
}

protocol kernel k_ran from tpl_k {
    vrf default;
    kernel table 200;
    ipv4 {
        table VRF_RAN;
    };
}

protocol direct dir_ran from tpl_dir {
    vrf default;
    ipv4 {
        table VRF_RAN;
        import filter Export_RAN;
    };
}

protocol bgp bgp_ran from tpl_bgp
{
    vrf default;
    passive;
    neighbor 10.250.2.1 as 65000;
    password "Password123";
    ipv4 {
        table VRF_RAN;
        export filter Export_RAN;
    };
}

protocol kernel k_n6 from tpl_k {
    vrf "n6";
    kernel table 6;
    ipv4 {
        table VRF_N6;
    };
}

protocol direct dir_n6 from tpl_dir {
    vrf "n6";
    ipv4 {
        table VRF_N6;
    };
}

protocol bgp bgp_n6 from tpl_bgp
{
    vrf "n6";
    neighbor 10.211.100.100 as 99;
    ipv4 {
        table VRF_N6;
        export filter Export_N6;
    };
}
EOT

service bird stop
service bird start


