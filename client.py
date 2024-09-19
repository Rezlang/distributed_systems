import sys
import socket
from helper import *


class Client:
    def __init__(self, id):

        self.knownhosts = load_json("knownhosts.json")["hosts"]

        self.view = (self.knownhosts["view"]["ip_address"],
                     self.knownhosts["view"]["udp_start_port"])
        server_address = (
            self.knownhosts[id]["ip_address"], self.knownhosts[id]["udp_start_port"])
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp.settimeout(0.15)
        self.udp.bind(server_address)

        self.receive_loop()

    def receive_loop(self):
        while True:
            user_in = sys.stdin.readline().strip().split()
            if len(user_in) == 0:
                continue
            if user_in[0] == "get" and len(user_in) == 2:
                response = self.send_to_KV(
                    self.construct_message(user_in))
                self.get_response(response)
            elif user_in[0] == "put" and len(user_in) == 3:
                response = self.send_to_KV(
                    self.construct_message(user_in))
                self.put_response(response)
            elif user_in[0] == "append" and len(user_in) == 3:
                response = self.send_to_KV(
                    self.construct_message(user_in))
                self.append_response(response)
            elif user_in[0] == "remove" and len(user_in) == 2:
                response = self.send_to_KV(
                    self.construct_message(user_in))
                self.remove_response(response)
            else:
                print("Invalid client command", file=sys.stderr)

    def get_response(self, response):
        if response == "None":
            print("unable to execute get")
        else:
            succ, key, val = response.split('|')
            if val == 'None':
                val = "null"
            print("get {} returned {}".format(key, val))

    def put_response(self, response):
        if response == "None":
            print("unable to execute put")
        else:
            print("put completed")

    def append_response(self, response):
        if response == "None":
            print("unable to execute append")
        else:
            print("append completed")

    def remove_response(self, response):
        if response == "None":
            print("unable to execute remove")
        else:
            print("remove completed")

    def send_to_KV(self, command):

        kv_address = get_kv(self.udp, "primary", self.view)
        print("Kv_address:", kv_address)
        if kv_address == None:
            return "None"
        # TODO: REMOVE THIS PRINT
        print("sending command {} to {}".format(command, kv_address))
        response = subprotocol_send(command, kv_address, self.udp)

        return response

    def construct_message(self, user_in):
        return '|'.join(user_in)


if __name__ == "__main__":
    ob = Client(sys.argv[1])
