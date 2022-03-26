# FakeUE Container Version

## Intro
docker-compose, with a MACVLAN or IPVLAN networking, can easily span up multiple FakeUE Virtual Devices.

## Env Preparation
docker's *daemon.json* will have:
```
{
  "bip": "10.211.248.1/29",
  "iptables": false
}
```

MACVLAN network can be created with:
```
docker network create -d macvlan --subnet=10.211.1.0/24  --ip-range=10.211.1.128/28 --gateway=10.211.1.1 -o parent=eth1 fakebackbone
```
(*ip range: 10.211.1.128-10.211.1.143*)
