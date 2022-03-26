#!/usr/bin/python3

# FakeUE identities:
IDENTITY_DB = {
    '1': 'abcdef',
    '128': 'abcdef',
    '129': 'abcdef',
    '130': 'abcdef',
    '131': 'abcdef',
    '132': 'abcdef',
    '133': 'abcdef',
    '134': 'abcdef',
    '135': 'abcdef',
    '136': 'abcdef',
    '137': 'abcdef',
    '138': 'abcdef',
    '139': 'abcdef',
    '140': 'abcdef',
    '141': 'abcdef',
    '142': 'abcdef',
    '143': 'abcdef',
}

PORT = 8994

UE_ROUTES = [
    '10.211.211.0/24'
]

TRANSPORT_IP = '10.211.1.1'

import http.server
import socketserver
import json
import simplejson
import os

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
DEFAULT_ACTION = {
    'action': 'ping',
    'params': ACTIONS_DEFAULT_PARAMS['ping'],
    'reconnect': 1,
    'sleepafter': 60
}

# define global vars/states
connections = {}
actions = {
    '_default': DEFAULT_ACTION,
    '4': DEFAULT_ACTION
}


# IP Route handling

def runs(cmds, **kwargs):
    for cmd in cmds:
        cmd_line = cmd.format(**kwargs)
        print("CMD->"+cmd_line)
        os.system(cmd_line)

def create_vrf(vrf, table):
    runs([
        "ip link add {vrf} type vrf table {table}",
        "ip link set dev {vrf} up",
        "ip route add table {table} unreachable default metric 4278198272",
        "ip rule add iif {vrf} table {table}",
        "ip rule add oif {vrf} table {table}",
    ], vrf=vrf, table=table)

def delete_vrf(vrf):
    runs([
        "ip link del {vrf}"
    ], vrf=vrf)

def config_interface_vrf(iface, addr, vrf):
    runs([
        "ip link set {iface} master {vrf}",
        "ip link set up dev {iface}",
        "ip addr add {addr} dev {iface}"
    ], iface=iface, addr=addr, vrf=vrf)
    
def reset_interface(iface):
    runs([
        "ip link set down dev {iface}",
        "ip addr flush dev {iface}"
    ], iface=iface)

def static_route_vrf(route, via, vrf):
    runs([
        "ip route add {route} via {via} vrf {vrf}"
    ], route=route, via=via, vrf=vrf)

def tunnel_up(local_ip, vrf, addr, route):
    runs([
        "ip tunnel add up0 mode gre local {local_ip} key 1234",
        "ip link set up0 master {vrf}",
        "ip addr add {addr} dev up0",
        "ip link set up dev up0",
        "ip route add {route} dev up0 vrf {vrf}"
    ], local_ip=local_ip, vrf=vrf, addr=addr, route=route)

def tunnel_down():
    runs(["ip tunnel del up0"], a=1)

def tunnel_neigh_add(addr, ll):
    runs(["ip neighbor add {addr} lladdr {ll} dev up0"], addr=addr, ll=ll)

def tunnel_neigh_del(addr, ll):
    runs(["ip neighbor del {addr} lladdr {ll} dev up0"], addr=addr, ll=ll)


def calc_tunnel_ip(id):
    idx = int(id)
    return "100.64.0.{}".format(idx)

def session_data(id):
    global connections
    return {
        'id': id,
        'transport_ip': TRANSPORT_IP,
        'tunnel_ip': connections[id]['tunnel_ip'],
        'routes': UE_ROUTES
    }

def handle_del_connection(data):
    global connections
    print("Handle del conn - data: {}".format(str(data)))
    id = data.get('id')
    psk = data.get('psk')
    if not id:
        return (False, 'INVALID ID')
    if not psk:
        return (False, 'INVALID PSK')
    if IDENTITY_DB[id] != psk:
        print("ID {} PSK MISMATCH")
        return (False, 'PSK MISMATCH')
    if id in connections:
        tunnel_neigh_del(connections[id]['tunnel_ip'], connections[id]['ip'])
        del connections[id]
        return (True, {})
    else:
        return (False, 'NOT EXISTS')

def handle_new_connection(data):
    global connections
    print("Handle new conn - data: {}".format(str(data)))
    id = data.get('id')
    psk = data.get('psk')
    ip = data.get('ip')
    if not id:
        return (False, 'INVALID ID')
    if not psk:
        return (False, 'INVALID PSK')
    if not ip:
        return (False, 'INVALID IP')
    if IDENTITY_DB[id] != psk:
        print("ID {} PSK MISMATCH")
        return (False, 'PSK MISMATCH')
    if id in connections:
        print("ID {} ALREADY CONNECTED... Supposing reconnection.".format(id))
        if ip != connections[id]['ip']:
            print("... but IP mismatch. Sending error.")
            return (False, 'RECONN IP MISMATCH')
        # sending existing session data:
        return (True, session_data(id))
    # Create new Conn
    connections[id] = {
        'ip': ip,
        'tunnel_ip': calc_tunnel_ip(id)
    }
    tunnel_neigh_add(connections[id]['tunnel_ip'], ip)
    return (True, session_data(id))
    
    return (False, 'GENERIC ERROR')


def nextaction_delete(data):
    global actions
    id = data.get('id')
    if not id or not id in actions:
        return (False, 'NOT PRESENT')
    if id == '_default':
        actions['_default'] = DEFAULT_ACTION
        return (True, {'msg': 'OK'})
    del actions[id]
    return (True, {'msg': 'OK'})

def nextaction_put(data):
    global actions
    id = data.get('id')
    if not id:
        return (False, 'INVALID ID')
    if id in actions:
        # delete it first
        del actions[id]
    newaction = data.get('action', '')
    if not newaction in ACTIONS_DEFAULT_PARAMS:
        return (False, 'INVALID ACTION NAME')
    # get params & co
    print("D DATA {}".format(data))
    params = data.get('params', {})
    print("D PARAMS {}".format(params))
    reconnect = data.get('reconnect', DEFAULT_ACTION['reconnect'])
    sleepafter = data.get('sleepafter', DEFAULT_ACTION['sleepafter'])
    params_base = ACTIONS_DEFAULT_PARAMS[newaction]
    # Overwrite default params with specific ones
    for key, value in params.items():
        print("D Par Overwrite {} with {}".format(key, value))
        params_base[key] = value
    actions[id] = {
        'action': newaction,
        'params': params_base,
        'reconnect': reconnect,
        'sleepafter': sleepafter
    }
    print("OK, I got a new nextaction for ID: {}".format(id))
    print(" -- {}".format(actions[id]))
    return (True, actions[id]) 


class FakeGWServerHandler(http.server.SimpleHTTPRequestHandler):
    def parse_data(self):
        self.data_string = "{}"
        if int(self.headers.get('Content-Length', 0)) > 0:
            self.data_string = self.rfile.read(int(self.headers['Content-Length']))
        self.data = simplejson.loads(self.data_string)
    def json_response(self, code=200, data={}):
        txt = json.dumps(data, sort_keys=True, indent=4)
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write("{}\n".format(txt).encode('utf-8'))
        return
    
    def hey(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write("hey.\n".encode('utf-8'))
    def do_GET(self):
        if self.path == '/status':
            status_struct = {
                'connections': connections,
                'nextactions': actions
            }
            self.json_response(200, status_struct)
        elif self.path == '/nextaction':
            self.parse_data()
            ret_action = actions['_default']
            ret_action['_source'] = '_default'
            id = self.data.get('id', 0)
            if id and id in actions:
                ret_action = actions[id]
                ret_action['_source'] = id
            self.json_response(200, ret_action)
            return
        else:
            self.hey()
            return
    def do_PUT(self):
        if self.path == '/connect':
            self.parse_data()
            ret = handle_new_connection(self.data)
            self.handle_return(ret)
        elif self.path == '/nextaction':
            self.parse_data()
            ret = nextaction_put(self.data)
            self.handle_return(ret)
        else:
            self.hey()
            return
    def do_POST(self):
        self.hey()
        return
    def do_DELETE(self):
        if self.path == '/connect':
            self.parse_data()
            ret = handle_del_connection(self.data)
            self.handle_return(ret)
        elif self.path == '/nextaction':
            self.parse_data()
            ret = nextaction_delete(self.data)
            self.handle_return(ret)
        else:
            self.hey()
            return
    def handle_return(self, ret):
        if ret[0]:
            self.json_response(200, ret[1])
        else:
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write("{}\n".format(ret[1]).encode('utf-8'))
        



def do_system_startup():
    vrf_name = 'n6'
    create_vrf(vrf_name, 6)
    config_interface_vrf('eth2', '10.211.100.1/24', vrf_name)
    static_route_vrf('10.211.211.0/24', '10.211.100.100', vrf_name)
    tunnel_up(TRANSPORT_IP, vrf_name, '100.64.255.255/32', '100.64.0.0/24')


def do_system_shutdown():
    tunnel_down()
    reset_interface('eth2')
    delete_vrf('n6')


do_system_startup()
socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), FakeGWServerHandler) as httpd:
    print("Serving at port {}".format(PORT))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        print("Closing... BYE!")
        do_system_shutdown()
