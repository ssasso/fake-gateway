# FakeGateway DEMO

## Server starting...
VRF and main tunnel is created. Listening on port http **8994**.
![image](./demo/2022-03-26 16 54 54.png)

## Fetching the server status
With the list of existing connections, and client next actions.
![image](./demo/2022-03-26 16 55 12.png)

## Show next action for client ID=1
![image](./demo/2022-03-26 16 55 33.png)

## Setting next action (ping) for client ID=1
![image](./demo/2022-03-26 16 55 53.png)
with server logs:

![image](./demo/2022-03-26 16 56 04.png)

## Remote Syslogs for CLIENT_LOOP (connect and ping)
![image](./demo/2022-03-26 16 57 12.png)

## Setting next action (die) for client ID=1
![image](./demo/2022-03-26 16 57 26.png)

## Server logs for client connection
![image](./demo/2022-03-26 16 58 00.png)

## Remote Syslogs for CLIENT_LOOP (next action: die)
![image](./demo/2022-03-26 16 58 33.png)

## Remote Syslogs for CLIENT_LOOP (complete log)
![image](./demo/2022-03-26 16 58 39.png)

Also available as [TXT](./demo/complete_log.txt)
