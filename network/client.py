import json
import time
import socket
import random
import traceback

from PodSixNet.Connection import connection, ConnectionListener


class MMXClient(ConnectionListener):
    def __init__(self, host, port, player_name, level):
        print("Intantiating client")
        self.Connect((host, port))
        self.player_name = player_name
        self.level = level
        connection.Send({'action': 'newconnection', 'un': player_name})

    def Loop(self):
        connection.Pump()
        self.Pump()

    def send_update_to_server(self, player_dict):
        send_dict = {'action': 'updateserver', 'un': player_dict['un'], 'data': player_dict}
        connection.Send(send_dict)

    # Built-in ConnectionListener stuff

    def Network(self, data):
        # print("Getting information from server...")
        pass

    def Network_connected(self, data):
        print("You are now connected to the server")

    def Network_error(self, data):
        print('error:', data['error'][1])
        connection.Close()

    def Network_disconnected(self, data):
        print('Server disconnected')
        exit()

    # Custom interactions:
    # Network_updatefromserver
    # newconnection
    # findserver

    def Network_updatefromserver(self, data):
        try:
            # print('Got data from server')
            # print(f'{json.dumps(data, indent=4)}\n')
            if self.level:
                self.level.player_data = data['data']
        except Exception as e:
            print(traceback.format_exc())


if __name__ == "__main__":

    # Trying PodSixNet
    c = MMXClient('localhost', 12000, input("Username? "), None)
    while True:
        c.send_update_to_server({'un': c.player_name, 'data': random.randint(1,101)})
        c.Loop()
        time.sleep(1.0/30)
