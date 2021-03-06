# fake-gateway

Welcome to the **FakeGateway Weekend Project**!

## Intro

You know, I work for a Telco vendor (yeah, visit https://athonet.com), we do 4G and 5G packet core.

Sometimes, it could be useful (at least, to me) to emulate a packet gateway (that is, a SPGW or a UPF) with proper traffic encapsulation and overlays (the GTPu part), but without the full complexity of 3GPP Telco Signalling.

So, I created this weekend project, this small "FakeGateway", which emulates a packet gateway and also a set of UEs (on different machines, of course).
Multiple "Fake UE" can connect, negotiate tunnel IP addresses, and do traffic over real tunnels! And everything is dynamic.
This is useful to test overlay routing, traffic isolation, dynamic routing, cloud and network integration, ...

The control plane part uses a simple restful http protocol, while the tunnel userplane part uses multipoint gre.
Routing and encapsulation is done by standard Linux functionalities.

## Some details
### Server part
The FakeGateway server part is composed by a python script, which runs an http server (based on *SimpleHTTPRequestHandler*). The same python program uses *iproute2* to control the tunnel and routing.

The FakeGateway server assigns UE IP from the range 100.64.0.0/24 (simply: 100.64.0.*Client-ID*), and is also capable of pushing *client routes*, which are installed by the client in its own routing table (for sending the right traffic over the tunnel).

Obviously FakeGateway tunnels are VRF-aware. The VRF right now is called **n6**.

Point-to-Multipoint GRE is used as tunneling tecnique, as follows (example):
```
ip link add n6 type vrf table 6
ip link set dev n6 up
ip route add table 6 unreachable default metric 4278198272
ip rule add iif n6 table 6
ip rule add oif n6 table 6

ip tunnel add up0 mode gre local 10.211.1.1 key 1234

ip link set up0 master n6

ip addr add 100.64.255.255/32 dev up0

ip link set up dev up0

ip route add 100.64.0.0/24 dev up0 vrf n6

ip neighbor add 100.64.0.1 lladdr 10.211.1.121 dev up0
ip neighbor add 100.64.0.2 lladdr 10.211.1.122 dev up0
```
All this magic is done by the python script.

### Client part
The Fake UE is a simple bash script with an infinite loop, which uses *iproute2*, *jq*, and *httpie*.
It "connects" to the server, creates the gre interface and set-ups the correct routing, and fetch a list of activities to perform (and performs them, of course).

Currently I support the following "client tasks" (with multiple parameters):
* ping
* iperf3
* sleep
* die (which, basically, terminates the client)

The client part uses the *logger* tools to send the log messages to a remote syslog server (see [RSYSLOG Remote Configuration](./doc/RSYSLOG-Remote-Config.md)).

Every Client is identified by and ID and a PSK, and does a very simple authentication when doing the connect/disconnect procedures.

### Client tasks control
As I said, every client dynamically fetches from the servers the actions to perform on any iteration. These can be dynamically set using restful calls. See [Client-Control](./doc/Client-Control-Example.md) for some examples.

Additionally, you can see here [How To Configure iPerf3 Server to listen on multiple ports](./doc/IPERF-MULTIPORT-HOWTO.md).

## Demo
See [DEMO](./doc/DEMO.md) page for some screenshots.

## Outro
I know that my coding abilities sucks, but I don't care ;) coding is not my job.

## Roadmap / TODO
* [x] Move VRF and iface config out of server.py
* [ ] Automatic handling of client, including:
  * [ ] auto derive ID from IP
  * [ ] netboot and/or cloud auto scaling group
    * [ ] ref: https://blog.haschek.at/2019/build-your-own-datacenter-with-pxe-and-alpine.html
  * [ ] fetch updated client_loop.sh script from the server (parallel http server) - use env file for initial discovery (i.e. user-data, kernel cmdline, ...)
  * [x] docker-compose for simplified scalability
* [ ] Improve iperf3 client action with additional parameters (see client/server source files)
* [ ] Support for IPv6
* [ ] Support for "Framed-Routing"
* [x] Configuration examples for BIRD
* [ ] Separate Control and Forwarding planes (i.e. multiple forwardings with ECMP)
* [ ] Performance statistics (i.e. netfilter/nftables counters based on IP)
* [ ] Trap Ctrl-C on Fake-UE (to perform clean disconnect)
* [ ] Multi vrf (datanetworks) + ip pools (based on gre key?)
* [ ] Asymm routing on fake "N6"
* [ ] Conf file / external auth db?
