import os
import re
import sys
import socket


def unloadModule(sock):
    result = True
    data = send(command="module unload system", sock=sock)
    if "OK" in data:
        return True
    return False

def send(command, sock=None):
        # print(' [Client] > %s'%command)
        sock.settimeout(0.1)
        cmd = command 
        try:
            cmd = cmd.encode("utf-8")
        except:
            cmd = cmd
        sock.send(cmd + b'\r\n')
        recv_data = b''
        while True:
            try:
                data = sock.recv(1024)
            except:
                break
            recv_data = recv_data + data
        data = recv_data.decode("utf-8")
        # print(" [Server] > %s" % data.replace('\r\n', '\n [Server] > '))
        return data

def read():
    1

if __name__ == "__main__":
    target = []
    socks = []
    for t in target:
        tip = t.split(':')[0]
        tport = t.split(':')[1]
        temp = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        temp.connect((tip, int(tport)))
        socks.append(temp)
    for s in socks:
    	if unloadModule(s):
    		print(" [+][%s:%i] Unload redis module successfully." % (s.getpeername()[0], s.getpeername()[1]))
