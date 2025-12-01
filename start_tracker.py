#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course,
# and is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#


"""
start_sampleapp
~~~~~~~~~~~~~~~~~

This module provides a sample RESTful web application using the WeApRous framework.

It defines basic route handlers and launches a TCP-based backend server to serve
HTTP requests. The application includes a login endpoint and a greeting endpoint,
and can be configured via command-line arguments.
"""

import json
import socket
import argparse

from daemon.weaprous import WeApRous

PORT = 9000  # Default port

peer_list = {}

app = WeApRous()
@app.route('/api/get-messages', methods=['GET'])
def get_messages(headers, body):
    with open("db/message.json", "r") as f:
        data = json.load(f)
    return 200, data

@app.route('/api/get-users', methods=['GET'])
def get_users(headers, body):
    with open("db/user.json", "r") as f:
        data = json.load(f)
    return 200, data
@app.route('/api/add-message', methods=['POST'])
def add_message(headers, body):
    with open("db/message.json", "r") as f:
        data = json.load(f)
    return 200, data
@app.route('/hello', methods=['PUT'])
def hello(headers, body):
    """
    Handle greeting via PUT request.

    This route prints a greeting message to the console using the provided headers
    and body.

    :param headers (str): The request headers or user identifier.
    :param body (str): The request body or message payload.
    """
    print("[SampleApp] ['PUT'] Hello in {} to {}".format(headers, body))
    return 200, "OK"

def print_input(headers, body):
    print("[Tracker] HEADERS:")
    print(headers)
    print("[Tracker] body:")
    print(body)

def handle_error(e):
    print("[Tracker] ERROR: {}".format(e))
    with open("apps/return.json", "w") as f:
        json.dump({'error': str(e)}, f, indent=4)
    return 500, "Internal Server Error"

@app.route("/", methods=["GET"])
def home(headers, body):
    return 200, "OK" #{"message": "Welcome to the RESTful TCP WebApp"}

@app.route("/user", methods=["GET"])
def get_user(headers, body):
    with open("apps/return.json", "w") as f:
        json.dump({"id": 1, "name": "Alice", "email": "alice@example.com"}, f, indent=4)
    return 200, "OK"

@app.route("/echo", methods=["POST"])
def echo(headers, body):
    try:
        data = json.loads(body)
        with open("apps/return.json", "w") as f:
            json.dump({"received": data}, f, indent=4)
        return 200, "OK"
    except json.JSONDecodeError:
        return {"error": "Invalid JSON"}
    
@app.route('/submit-info', methods=['POST'])
def submit_info(headers, body):
    print("[Tracker] POST /submit-info")
    print_input(headers, body)
    try:
        data = json.loads(body) if body else {}
        peer_ip = data.get('ip', '')
        peer_port = data.get('port', 0)
        
        if not (peer_ip and peer_port):
            print("[Tracker] ERROR: Missing ip or port")
            with open("apps/return.json", "w") as f:
                json.dump({'error': 'Missing ip or port'}, f, indent=4)
            return 400, "Bad Request"
        
        peer_id = "{}:{}".format(peer_ip, peer_port)
        peer_list[peer_id] = {
            'ip': peer_ip,
            'port': int(peer_port),
            'active': False
        }
        print("[Tracker] Registered: {}".format(peer_id))
        
        with open("apps/return.json", "w") as f:
            json.dump({'peer_id': peer_id}, f, indent=4)
        return 200, "OK"
        
    except Exception as e:
        return handle_error(e)
        
@app.route('/get-list', methods=['GET'])
def get_list(headers, body):
    print("[Tracker] GET /get-list")
    print_input(headers, body)

    try:
        active_peers = {
            peer_id: info for peer_id, info in peer_list.items() if info.get("active") is True
        }

        print("[Tracker] Active peers: {}".format(active_peers))

        with open("apps/return.json", "w") as f:
            json.dump({
                'peer_list': active_peers,
                'length': len(active_peers),
            }, f, indent=4)

        return 200, "OK"
        
    except Exception as e:
        return handle_error(e)

@app.route('/add-list', methods=['POST'])
def add_list(headers, body):
    print("[Tracker] POST /add-list")
    print_input(headers, body)
    try:
        data = json.loads(body) if body else {}
        peer_ip = data.get('ip', '')
        peer_port = data.get('port', 0)
        
        if not (peer_ip and peer_port):
            print("[Tracker] ERROR: Missing ip or port")
            with open("apps/return.json", "w") as f:
                json.dump({'error': 'Missing ip or port'}, f, indent=4)
            return 400, "Bad Request"
        
        peer_id = "{}:{}".format(peer_ip, peer_port)
        if peer_id not in peer_list:
            print("[Tracker] ERROR: ID {} haven't registerd yet".format(peer_id))
            with open("apps/return.json", "w") as f:
                json.dump({'error': "ID {} haven't registerd yet".format(peer_id)}, f, indent=4)
            return 400, "Bad Request"
            
        if peer_list[peer_id]['active']:
            print("[Tracker] ERROR: ID {} is already online".format(peer_id))
            with open("apps/return.json", "w") as f:
                json.dump({'error': "ID {} is already online".format(peer_id)}, f, indent=4)
            return 400, "Bad Request"
        
        peer_list[peer_id]['active'] = True
        print("[Tracker] Active: {}".format(peer_id))
        
        with open("apps/return.json", "w") as f:
            json.dump({'peer_id': peer_id}, f, indent=4)
        return 200, "OK"
        
    except Exception as e:
        return handle_error(e)
    
@app.route('/remove', methods=['POST'])
def add_list(headers, body):
    print("[Tracker] POST /remove")
    print_input(headers, body)
    try:
        data = json.loads(body) if body else {}
        peer_ip = data.get('ip', '')
        peer_port = data.get('port', 0)
        
        if not (peer_ip and peer_port):
            print("[Tracker] ERROR: Missing ip or port")
            with open("apps/return.json", "w") as f:
                json.dump({'error': 'Missing ip or port'}, f, indent=4)
            return 400, "Bad Request"
        
        peer_id = "{}:{}".format(peer_ip, peer_port)
        if peer_id not in peer_list:
            print("[Tracker] ERROR: ID {} haven't registerd yet".format(peer_id))
            with open("apps/return.json", "w") as f:
                json.dump({'error': "ID {} haven't registerd yet".format(peer_id)}, f, indent=4)
            return 400, "Bad Request"
            
        if not peer_list[peer_id]['active']:
            print("[Tracker] ERROR: ID {} is already offline".format(peer_id))
            with open("apps/return.json", "w") as f:
                json.dump({'error': "ID {} is already offline".format(peer_id)}, f, indent=4)
            return 400, "Bad Request"
        peer_list[peer_id]['active'] = False
        print("[Tracker] Offline: {}".format(peer_id))
        
        with open("apps/return.json", "w") as f:
            json.dump({'peer_id': peer_id}, f, indent=4)
        return 200, "OK"
        
    except Exception as e:
        return handle_error(e)

if __name__ == "__main__":
    # Parse command-line arguments to configure server IP and port
    parser = argparse.ArgumentParser(prog='Backend', description='', epilog='Beckend daemon')
    parser.add_argument('--server-ip', default='0.0.0.0')
    parser.add_argument('--server-port', type=int, default=PORT)
 
    args = parser.parse_args()
    ip = args.server_ip
    port = args.server_port

    # Clear the return.json
    with open("apps/return.json", "w") as f:
        f.write("")


    # Prepare and launch the RESTful application
    app.prepare_address(ip, port)
    app.run()
