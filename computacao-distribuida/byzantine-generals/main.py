# -*- coding: utf-8 -*-

import sys
import socket
import re
from pickle import loads, dumps
from threading import Thread
from string import ascii_lowercase

running = True
faulty = False
general = False
configs = []
my_id = 0
vector = {}
neighbors = set()


def broadcast(msg):
    ng = []
    for i in range(1, len(configs)):
        sock = socket.socket()
        sock.settimeout(5)
        if faulty:
            msg = ascii_lowercase[i]
        try:
            sock.connect(configs[i])
            sock.send(dumps(msg))
        except (socket.timeout, ConnectionRefusedError):
            print('Impossível conectar com {}'.format(i + 1))
            continue
        except InterruptedError:
            print('Deu merda')
        sock.close()
        ng.append(i + 1)
    global neighbors
    neighbors |= set(ng)


def sender_general():
    while True:
        msg = input('-> ')
        if msg == 'sair':
            print('Saindo...')
            global running
            running = False
            break
        broadcast({my_id: msg})


def receiver(my_config):
    sock = socket.socket()
    sock.bind(my_config)
    sock.settimeout(5)
    sock.listen(10)
    vector[my_id] = {}
    ng = set()
    global neighbors
    while running:
        try:
            conn, _ = sock.accept()
        except socket.timeout:
            continue
        data = loads(conn.recv(1024))
        v = data.copy().popitem()
        print('data depois do bagulho', data)
        if v[0] == 1:
            # Recebendo do general
            vector[my_id] = data
            broadcast({my_id: data[1]})
        elif type(v[1]) is str:
            ng |= set(list(data.keys()))
            vector[my_id].update(data)
            if ng == neighbors:
                ng = set()
                print('Mandando ver')
                broadcast(vector)
        elif type(v[1]) is dict:
            print("ABACAXI")
            print('Recebi vetor de {} = {}'.format(v[0], v[1]))
            # Recebendo os vetores
            vector.update(data)
            ng |= set(list(data.keys()))
            if ng == neighbors:
                # ver qual é o faulty
                print('Acabou')
                print("-"*30)
                print(vector)
                break

        print(vector)
        print(ng)
        print(neighbors)

        conn.shutdown(socket.SHUT_RDWR)
        conn.close()
    sock.shutdown(socket.SHUT_RDWR)
    sock.close()


def read_configs():
    try:
        f = open('config.txt')
    except:
        print('Não foi possível abrir arquivo de configuração')
        sys.exit(0)
    global configs
    configs = [(i.split()[0], int(i.split()[1]))
               for i in f.readlines()]
    return configs[my_id - 1]


def start_threads():
    if my_id == 1:
        send = Thread(target=sender_general, name='sender')
        send.start()
        send.join()
    else:
        try:
            rec = Thread(target=receiver, name='receiver', args=(my_config, ))
            rec.start()
            rec.join()
        except KeyboardInterrupt:
            print('\r\rSaindo...')
            global running
            running = False


if __name__ == '__main__':
    try:
        my_id = int(sys.argv[1])
        neighbors |= set([my_id])
        print(neighbors)
        # Se o id do processo é 1 ele é o general
        general = True if my_id == 1 else False
        # Se o segundo argumento for 'faulty' o processo é o mentiroso
        faulty = True if sys.argv[2] == 'faulty' else False
    except IndexError:
        faulty = False
    except:
        print('Execute o programa com o padrão {} <id>'.
              format(sys.argv[0]))
        sys.exit(0)

    print('Digite "sair" para encerrar')

    my_config = read_configs()
    print(configs)
    print(my_config)
    start_threads()
