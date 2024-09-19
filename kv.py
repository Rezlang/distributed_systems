# data, address = self.udp.recvfrom(1024)
# self.udp.sendto(, address)
import sys
import socket
import threading
from helper import *
import json


class KV:
    def __init__(self, id):

        self.knownhosts = load_json("knownhosts.json")["hosts"]

        self.view = (self.knownhosts["view"]["ip_address"],
                     self.knownhosts["view"]["udp_start_port"])
        self.dict = {}
        self.id = id
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.cq = []
        self.udp.settimeout(0.15)
        server_address = (
            self.knownhosts[id]["ip_address"], self.knownhosts[id]["udp_start_port"])
        self.udp.bind(server_address)
        self.primary = False
        self.backup = False
        self.udp.sendto("new_kv|{}".format(id).encode(), self.view)
        self.receive_loop()

    def receive_loop(self):
        # Start the stdin thread
        stdin_thread = threading.Thread(
            target=self.stdin_loop, daemon=True)
        # Start the UDP thread
        udp_thread = threading.Thread(
            target=self.udp_loop, daemon=True)

        worker_thread = threading.Thread(
            target=self.process_commands, daemon=True
        )

        stdin_thread.start()
        udp_thread.start()
        worker_thread.start()

        stdin_thread.join()
        udp_thread.join()
        worker_thread.join()

    def process_commands(self):
        while True:
            if len(self.cq) == 0:
                continue
            return_address, data = self.cq.pop(0)
            if data[0] == "ping":
                self.udp.sendto("pong".encode(), return_address)
            elif data[0] == "backup" and self.backup:
                data = data[1:]
                self.command_picker(data, return_address)
            elif data[0] == "primaryTime":
                self.backup = False
                self.primary = True
                self.udp.sendto("yesPrimaryTime".encode(), return_address)
            elif data[0] == "backup_data":
                print("Sending backup data")
                resp = subprotocol_send("data|"+json.dumps(self.dict),
                                        return_address, self.udp)
                print("response:", resp)
            elif data[0] != "backup" and self.primary:
                self.command_picker(data, return_address)
            elif data[0] == "backupTime":
                print("Requesting backup data")
                self.backup = True
                self.request_data()
                self.udp.sendto("yesBackupTime".encode(), return_address)
            else:
                print("Invalid udp command", file=sys.stderr)
                print("Invalid command:", data)

    def stdin_loop(self):
        while True:
            user_in = sys.stdin.readline().strip()
            if user_in == "kv":
                self.kv()
            else:
                print("Invalid user input", file=sys.stderr)

    def udp_loop(self):
        while True:
            try:
                data, return_address = self.udp.recvfrom(1024)
                data = data.decode().split("|")
                print("Received UDP:", data)
                self.cq.append((return_address, data))

            except:
                data = ["None"]

    def request_data(self):
        primary_address = get_kv(self.udp, "primary", self.view)
        print("primary address: {}".format(primary_address))

        resp = subprotocol_send(
            "backup_data", primary_address, self.udp)
        if resp != None:
            self.udp.sendto("ack".encode(), primary_address)
            if resp == "data|{}":
                self.dict = {}
            else:
                resp = resp.replace("data|", "")
                data = json.loads(resp)
                self.dict = data
        else:
            print("Failed to get backup data from primary")

    def command_picker(self, data, return_address):
        if self.primary:
            backup_address = get_kv(self.udp, "backup", self.view)
            print("backup address: {}".format(backup_address))
            if backup_address != None:
                resp = subprotocol_send("backup|" + "|".join(data),
                                        backup_address, self.udp)
                print("backup response: {}".format(resp))
        if data[0] == "put" and len(data) == 3:
            self.put(data[1], data[2])
            self.udp.sendto("success".encode(), return_address)
        elif data[0] == "get" and len(data) == 2:
            print("GETTING")
            val = self.get(data[1])
            print("val: {}".format(val))
            self.udp.sendto("success|{}|{}".format(
                data[1], val).encode(), return_address)
        elif data[0] == "append" and len(data) == 3:
            self.append(data[1], data[2])
            self.udp.sendto("success".encode(), return_address)
        elif data[0] == "remove" and len(data) == 2:
            self.remove(data[1])
            self.udp.sendto("success".encode(), return_address)
        else:
            print("invalid view command", file=sys.stderr)

    def put(self, key, val):
        self.dict[key] = [val]
        print(self.dict, val)

    def get(self, key):
        try:
            return self.dict[key]
        except:
            return None

    def append(self, key, val):
        if key not in self.dict:
            self.put(key, val)
        else:
            self.dict[key].append(val)

    def remove(self, key):
        self.dict.pop(key)

    def kv(self):
        if len(self.dict.keys()) == 0:
            print("no entries")
        else:
            for item in sorted(self.dict.items()):
                print(item[0], item[1])


if __name__ == "__main__":
    ob = KV(sys.argv[1])
