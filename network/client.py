import json
import time
import socket


def update_player_data(player_dict, server_addr):
    msg_dict = {
                'username': player_dict['un'],
                'player_dict': player_dict,
                'sending_update': True,
               }

    b_msg = json.dumps(msg_dict).encode('utf-8')
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(1.0/30)
    client_socket.sendto(b_msg, server_addr)

def get_remote_player_data(username, server_addr):
    msg_dict = {
                'username': username,
                'get_update': True,
               }
    b_msg = json.dumps(msg_dict).encode('utf-8')
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(1.0)
    client_socket.sendto(b_msg, server_addr)
    try:
        # Ensure buffer is large enough for data.
        data, server = client_socket.recvfrom(1024*8)
        remote_player_dict = json.loads(data)
        return remote_player_dict
    except socket.timeout:
        print('REQUEST TIMED OUT')
        # raise TimeoutException(f"{username}: timed out")



def inform_disconnect(username, server_addr):
    msg_dict = {
                'username': username,
                'disconnect': True,
               }

    b_msg = json.dumps(msg_dict).encode('utf-8')
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(1.0/30)
    client_socket.sendto(b_msg, server_addr)

def test():
    username = input("What is your username? ")
    msg = ''
    while msg != "exit":
        msg = input("Message to send to server: ")
        msg_dict = {
                    'username': username,
                    'message': msg
                   }
        if msg == 'check server':
            msg_dict['check_server'] = True
            addr = ("<broadcast>", 12000)
        else:
            addr = ("127.0.0.1", 12000)
        b_msg = json.dumps(msg_dict).encode('utf-8')
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.settimeout(1.0)
        addr = ("127.0.0.1", 12000)
        print(f'Sending ""{b_msg.lower()}""...')
        start = time.time()

        client_socket.sendto(b_msg, addr)
        try:
            data, server = client_socket.recvfrom(1024)
            end = time.time()
            elapsed = end - start
            print(f'Received "{data}"" in {elapsed} seconds')
        except socket.timeout:
            print('REQUEST TIMED OUT')

class TimeoutException(Exception):
    pass

if __name__ == "__main__":
    test()
