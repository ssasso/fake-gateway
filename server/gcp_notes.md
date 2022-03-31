# GCP Stuff

By default, GCP Linux instances eth nics have addresses in /32 form.

The "GCP Virtual Router" by default answers for ARP only for the "gateway IP", it does not proxy arp the other VM addresses.

So, we have to:
```
create_vrf n6 6
ip link set ens5 master n6
ip route add 10.211.100.1 dev ens5 vrf n6
ip route add 10.211.100.0/24 via 10.211.100.1 vrf n6
```

While this can work for static routing, it does not work with bird, which needs to have a "direct" connectivity with the Cloud Router for establishing the BGP Session.

Google allows to create VM images with the "hidden feature" called **MULTI_IP_SUBNET**:
```
gcloud compute images create rtr-1-multi-ip-subnet --source-snapshot=snap-rtr-1 --guest-os-features MULTI_IP_SUBNET
```
In this case the VM can use the "standard" IP/Mask form, and the Cloud will perform proxy arp for the other VMs.
