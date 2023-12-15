import sys
from pwn import *
import struct
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from eth_keys import KeyAPI
from ecies import decrypt as ecies_decrypt

# ===================================
# Quel serveur cible ?
# ===================================
# Par défaut on appelle l'instance "locale", sauf si on utilise -REMOTE dans les arguments de lancement
if '-REMOTE' in sys.argv:
    root_pk_filename = 'aegissecureforgeserver.chall.malicecyber.com_aegis.root.pem'
    host, port = 'aegissecureforgeserver.chall.malicecyber.com', '2429'
    #host, port = "46.30.202.223", "2429"
else:
    root_pk_filename = 'local_aegis.root.pem'
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


# Envoi d'un certificat pour récupérer le firmware
def recup_firmware(cert:bytes):
    cert_length = struct.pack('<H', len(cert))
    request_msg = b'\x4c\x04' + b'\x14' + cert_length + b'\x0d\x0a' + cert
    p.send(request_msg)

    encrypted_firmware = read_response()
    print(f'{encrypted_firmware=}')
    ecies_cipher = read_response()
    print(f'{ecies_cipher=}')
    ecies_iv = read_response()
    print(f'{ecies_iv=}')

    return encrypted_firmware, ecies_cipher, ecies_iv


# Chargement d'une clé privée au format PEM
def load_key_from_pem(pem_filename):
    pem_file = open(pem_filename, 'rb')
    pem = pem_file.read()
    key = serialization.load_pem_private_key(pem, password=None, backend=default_backend())
    return key


# Déchiffrement de la clé et de l'IV utilisés pour chiffrer le firmware
def decipher_key_and_iv(ciphered_key, ciphered_iv):
    root_pk = load_key_from_pem(root_pk_filename)

    ethk = KeyAPI("eth_keys.backends.CoinCurveECCBackend")
    sk = ethk.PrivateKey(
        root_pk.private_numbers().private_value.to_bytes(
            (root_pk.key_size + 7) // 8, "big"
        )
    )

    SECRET_KEY = ecies_decrypt(sk._raw_key.hex(), ciphered_key)
    SECRET_IV = ecies_decrypt(sk._raw_key.hex(), ciphered_iv)

    return SECRET_KEY, SECRET_IV

# Déchiffrement du firmware, à partir de la clé et de l'IV
def decipher_firmware(encrypted_firmware, secret_key, secret_iv):
    cipher = Cipher(algorithms.AES(secret_key), modes.CBC(secret_iv))
    decryptor = cipher.decryptor()
    plaintext_firmware = decryptor.update(encrypted_firmware) + decryptor.finalize()
    print(f'{plaintext_firmware=}')

    return plaintext_firmware

def unpad(datas):
    final_padding = datas[-1]
    return datas[:-final_padding]

# ===================================
# Appel PROTOCOL_CMD_GET_LATEST avec le certificat généré
# ===================================
with open('forged-cert.der', 'rb') as cert_file:
    cert = cert_file.read()
    encrypted_firmware, ecies_key, ecies_iv = recup_firmware(cert)
    SECRET_KEY, SECRET_IV = decipher_key_and_iv(ecies_key, ecies_iv)
    firmware = decipher_firmware(encrypted_firmware, SECRET_KEY, SECRET_IV)
    firmware = unpad(firmware)
    
with open('firmware', 'wb') as output_file:
    output_file.write(firmware)


# ===================================
# Fermeture connexion
# ===================================
p.close()
