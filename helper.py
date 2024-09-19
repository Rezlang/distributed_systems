import socket
import json
import sys


def subprotocol_send(message, address, udp_socket, attempt=1, max_attempts=3):

    udp_socket.sendto(message.encode(), address)

    try:
        # Wait for the acknowledgment
        data, return_address = udp_socket.recvfrom(1024)

        return data.decode()

    except:
        if attempt < max_attempts:
            return subprotocol_send(message, address, udp_socket, attempt + 1, max_attempts)
        else:
            return None


def load_json(filename):
    with open(filename) as file:
        return json.loads(file.read())


def get_kv(udp, key, view):
    # TODO: REMOVE THIS PRINT
    print("getting kv {}".format(key))
    kv_address = subprotocol_send(key, view, udp)
    print("kv_address:", kv_address)

    if not kv_address:
        return None
    elif kv_address == "null":
        print("kv_address is null, key:", key)
        return None
    kv_address = kv_address.replace(
        "(", "").replace(")", "").replace(" ", "").replace("'", "").split(",")

    kv_address = (kv_address[0], int(kv_address[1]))
    print(type(kv_address[0]))
    return kv_address
