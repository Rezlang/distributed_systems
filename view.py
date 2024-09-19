import socket
import sys
import threading
import json
from helper import *

# data, address = self.udp.recvfrom(1024)
# self.udp.sendto(, address)


class View:
    def __init__(self, id):

        self.knownhosts = load_json("knownhosts.json")["hosts"]
        self.view_address = self.knownhosts["view"]["ip_address"]
        self.view_port = self.knownhosts["view"]["udp_start_port"]
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp.settimeout(0.15)
        self.cq = []
        server_address = (self.view_address, self.view_port)
        self.udp.bind(server_address)

        self.primaryID = None
        self.backupID = None
        self.no_role = []
        self.addresses = {}

        self.receive_loop()

    def receive_loop(self):
        # Start two threads: one for stdin and one for UDP
        stdin_thread = threading.Thread(target=self.stdin_loop)
        udp_thread = threading.Thread(target=self.udp_loop)
        worker_thread = threading.Thread(target=self.worker_loop)

        stdin_thread.start()
        udp_thread.start()
        worker_thread.start()

        # Optionally join threads if you need to wait for them to finish
        stdin_thread.join()
        udp_thread.join()
        worker_thread.join()

    def worker_loop(self):
        while True:
            if len(self.cq) == 0:
                continue
            address, data = self.cq.pop(0)
            if data[0] == "primary":
                primary_ID = self.get_primary()
                print("here {}".format(primary_ID))
                if primary_ID == "null":
                    self.udp.sendto(
                        primary_ID.encode(), address)
                else:
                    self.udp.sendto(
                        "{}".format(self.addresses[primary_ID]).encode(), address)
            elif data[0] == "backup":
                backup_ID = self.get_backup()
                if backup_ID == "null":
                    self.udp.sendto(
                        "null".encode(), address)
                self.udp.sendto(
                    "{}".format(self.addresses[backup_ID]).encode(), address)
            elif data[0] == "new_kv" and len(data) == 2:
                id = data[1]
                self.new_kv(id, address)
            else:
                print("invalid udp command", file=sys.stderr)

    def stdin_loop(self):
        while True:
            user_in = sys.stdin.readline().strip()
            if user_in == "view":
                self.view()
            else:
                print("invalid view command", file=sys.stderr)

    def udp_loop(self):
        while True:
            try:
                data, address = self.udp.recvfrom(1024)
                data = data.decode().split("|")
                print("Received command {}".format(data[0]))
                self.cq.append((address, data))

            except:
                data = ["None"]

    def get_primary(self, flag=True):

        if self.check_kv(self.primaryID):
            return self.primaryID
        elif flag == True:
            self.primaryID = None
            print("The primary is dead!")
            self.assign_primary()
            return self.get_primary(False)
        else:
            return "null"

    def check_kv(self, id):
        if not id:
            return None
        addr = self.addresses[id]
        success = subprotocol_send("ping", addr, self.udp)
        if not success:
            self.addresses.pop(id)
        print("pong")

        return success

    def get_backup(self, flag=True):
        if self.check_kv(self.backupID):
            return self.backupID
        elif flag == True:
            self.backupID = None
            self.assign_backup()
            return self.get_backup(False)
        else:
            return "null"

    def get_no_role(self):
        return self.no_role

    def new_kv(self, id, address):
        self.addresses[id] = address
        self.no_role.append(id)
        if self.primaryID == id:
            self.primaryID = None
        elif self.backupID == id:
            self.backupID = None
        self.assign_primary()
        self.assign_backup()
        print(self.addresses)

    def assign_primary(self):
        if not self.primaryID and not self.backupID and len(self.no_role) >= 1:
            self.primaryID = sorted(self.no_role)[0]
            print("Assigned primary:", self.primaryID)
            self.no_role.remove(self.primaryID)
        elif not self.primaryID and self.check_kv(self.backupID):
            self.primaryID = self.backupID
            self.backupID = None
            print("primary from promotion:", self.primaryID)
            self.assign_backup()
        else:
            self.backupID = None
            return None

        print(self.addresses)
        print("sending primaryTime to:", self.addresses[self.primaryID])
        sys.stdout.flush()

        success = subprotocol_send(
            "primaryTime", self.addresses[self.primaryID], self.udp)
        if not success:
            self.primaryID = None

        return success

    def assign_backup(self):
        if self.backupID == None and len(self.no_role) >= 1:
            self.backupID = sorted(self.no_role)[0]
            self.no_role.remove(self.backupID)

            success = subprotocol_send(
                "backupTime", self.addresses[self.backupID], self.udp)
            if not success:
                self.backupID = None
            return success
        return None

    def view(self):
        primary = self.primaryID if self.primaryID else "null"
        backup = self.backupID if self.backupID else "null"
        print("primary: {} backup: {}".format(primary, backup))


if __name__ == "__main__":
    ob = View(sys.argv[1])
