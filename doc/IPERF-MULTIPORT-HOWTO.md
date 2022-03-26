# Configure an iPerf3 Server to listen on multiple ports
```
#!/bin/bash

BASEPORT=5000
COUNT=100

for i in $(seq 0 $COUNT); do
    port=$((BASEPORT+$i))
    iperf3 -s -D -p $port
done
```
