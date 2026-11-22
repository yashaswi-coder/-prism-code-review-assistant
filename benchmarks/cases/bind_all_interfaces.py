import socket


def open_listener() -> socket.socket:
    listener = socket.socket()
    listener.bind(("0.0.0.0", 8080))
    return listener
