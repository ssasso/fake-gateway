# RSYSLOG Configuration Example (for receiving Client Log Data)

```
$ModLoad imudp.so
$UDPServerRun 514

$template DynamicFile,"/var/log/remote/%FROMHOST-IP%.log"
local7.* -?DynamicFile
```
