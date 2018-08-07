import json
import time
import socket
import random
import logging
import traceback

from PodSixNet.Connection import connection, ConnectionListener

logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')


class MMXClient(ConnectionListener):
    def __init__(self, host, port, player_name, level):
        logging.info("Instantiating client")
        self.Connect((host, port))
        self.player_name = player_name
        self.level = level
        connection.Send({'action': 'newconnection', 'type': 'player', 'id': player_name})

    def Loop(self):
        connection.Pump()
        self.Pump()

    def send_player_data_update_to_server(self, player_dict):
        send_dict = {'action': 'updateserver', 'type': 'player', 'id': player_dict['id'], 'data': player_dict}
        connection.Send(send_dict)

    # Built-in ConnectionListener stuff

    def Network(self, data):
        # logging.debug("Getting information from server...")
        pass

    def Network_connected(self, data):
        logging.info("You are now connected to the server")

    def Network_error(self, data):
        logging.error('error:', data['error'][1])
        connection.Close()

    def Network_disconnected(self, data):
        logging.warning('Server disconnected')
        exit()

    # Custom interactions:
    # Network_updatefromserver
    # newconnection
    # findserver

    def Network_updatefromserver(self, data):
        try:
            # logging.debug('Got data from server')
            # logging.debug(f'{json.dumps(data, indent=4)}\n')
            if self.level:
                self.level.data_cache = data['data']
        except Exception as e:
            logging.warning(traceback.format_exc())
#

if __name__ == "__main__":

    # Trying PodSixNet
    c = MMXClient('localhost', 12000, input("Username? "), None)
    while True:
        c.send_player_data_update_to_server({'id': c.player_name, 'data': random.randint(1,101)})
        c.Loop()
        time.sleep(1.0/30)
