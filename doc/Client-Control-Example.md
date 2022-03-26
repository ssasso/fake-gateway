# Client Actions Control
Using RESTful calls. Calls are made with *httpie*.

## GET Actions for ID
```
http GET http://127.0.0.1:8994/nextaction id=1
```

## DELETE Action (reset to default action)
```
http DELETE http://127.0.0.1:8994/nextaction id=1
```

## PUT Action - PING
Optional Params:
* **c**: count
* **i**: interval
* **s**: size
* **target**: target

```
http PUT http://127.0.0.1:8994/nextaction id=1 action=ping sleepafter=60 params:='{"c": 100, "i": 0.1, "s": 1200 }'
http PUT http://127.0.0.1:8994/nextaction id=1 action=ping sleepafter=60 params:='{"c": 100, "i": 1 }'
```

## PUT Action - SLEEP
Optional Params:
* **time**: sleep time
```
http PUT http://127.0.0.1:8994/nextaction id=1 action=sleep params:='{"time": 600 }'
```

## PUT Action - DIE
```
http PUT http://127.0.0.1:8994/nextaction id=1 action=die
```

## PUT Action - IPERF
Optional Params:
* **base_port**: base port, where the server is listening on
* **i**: interval
* **time**: time
* **target**: target

```
http PUT http://127.0.0.1:8994/nextaction id=1 action=iperf params:='{"time": 600 }'
```

## DEFAULT PARAMETERS
```
ACTIONS_DEFAULT_PARAMS = {
    'ping': {
        'c': 100,
        'i': 0.1,
        's': 1200,
        'target': '10.211.211.211'
    },
    'iperf': {
        'base_port': 5000,
        'protocol': 'tcp',
        'i': 1,
        'target': '10.211.211.211',
        'time': 10,
        'parallel': 1,
        'direction': 1
    },
    'sleep': {
        'time': 60
    },
    'die': {}
}
```
