What I did on GCP instance:

```
create_vrf n6 6
ip link set ens5 master n6
ip route add 10.211.100.1 dev ens5 vrf n6
ip route add 10.211.100.0/24 via 10.211.100.1 vrf n6
```
