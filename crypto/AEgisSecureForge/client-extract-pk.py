import sys
from pwn import *
import struct
from collections import Counter

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


# ===================================
# Utilitaires de communication
# ===================================
# Lecture de la réponse su serveur, composée : 
# - de 4 octets indiquant la taille du message
# - suivi du message
def read_response():
    response_length = p.recvn(4)
    response_length = struct.unpack('I', response_length)[0]
    response_msg = p.recv(response_length)
    return response_msg


# ===================================
# Les différentes commandes possibles
# ===================================
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

# Enregistrement d'un certificat
def register(common_name=b'titi', return_response_only=True):
    assert len(common_name) <= 0xFFFF
    cn_length = struct.pack("<H", len(common_name))
    request_msg = b'\x4c\x04\x0a' + cn_length + b'\x0d\x0a' + common_name
    p.send(request_msg)

    serial_enc = read_response()
    serial_number = int.from_bytes(serial_enc, 'little')
    encrypted_response = read_response()
    
    if return_response_only:
        return encrypted_response
    else:
        return encrypted_response, serial_enc



# ===================================
# Préparation : détermination de toutes les fins de message possibles
# ===================================
# Le padding à appliquer au common_name pour se caler à l'offset 128
common_name_padding = b'A' * 8

# Entête et pied d'une clé privée au format PEM
pk_header = b'-----BEGIN PRIVATE KEY-----\n'
pk_footer = b'\n-----END PRIVATE KEY-----\n'

# Dictionnaire permettant de retrouver la valeur du padding PKCS7 du message en clair,
# à partir du dernier bloc chiffré contenu dans la réponse
padding_by_encrypted_pk_footers = {}
# Dictionnaire permettant de retrouver la valeur du dernier bloc chiffré en fonction du padding PKCS7 appliqué
encrypted_pk_footers_by_padding = {}

# Comptage des fins trouvées, afin de déterminer la plus probable 
last_encrypted_blocks = Counter()

# Détermine les correspondances entre padding PKCS7 et dernier bloc chiffré
def find_all_possible_encrypted_message_ending():
    last_16_bytes_of_pk_footer = pk_footer[-16:]
    
    for i in range(1,16+1):
        plaintext = last_16_bytes_of_pk_footer[i:]
        ending_padding = chr(i).encode() * i
        encrypted_response = register(common_name_padding + plaintext +  ending_padding)
        encryptext = encrypted_response[128:128+16]
        padding_by_encrypted_pk_footers[encryptext] = 16 - i
        encrypted_pk_footers_by_padding[16 - i] = encryptext
        print(f'{encryptext.hex()=}')
        last_encrypted_blocks.update([encrypted_response[-16:]])


find_all_possible_encrypted_message_ending()
print(f'{last_encrypted_blocks=}')
print(f'{padding_by_encrypted_pk_footers=}')


# ===================================
# Calage sur le début du footer 
# ===================================
# Détermine le padding PKCS7 le plus probable quand le common_name est bien qualibrée (ie A*8 + 16 octets)
# il servira de référence pour les calculs de début de récupération de la clé privée du serveur
init_encrypted_footer = last_encrypted_blocks.most_common(1)[0][0]
print(f'{init_encrypted_footer.hex()=}')
init_padding_footer = padding_by_encrypted_pk_footers[init_encrypted_footer]
print(f'{init_padding_footer=}')

# Calcul de la taille du common_name (en plus du padding initial) nécessaire 
# pour que le deuxième bloc contiennent le début du footer de la clé privée
pk_footer_length = len(pk_footer)
print(f'{pk_footer_length=}')
usable_cn_length = pk_footer_length - init_padding_footer
usable_cn_length %= 16
print(f'{usable_cn_length=}')


# ===================================
# Décryptage de la clé privée du serveur 
# ===================================
# Liste des caractères possibles dans une clé privée au format PEM (a priori plus de majuscules que de minuscules)
#valid_car = '-' + string.ascii_letters + string.digits + '/+=' + '\n'
valid_car = '-' + string.ascii_uppercase + string.ascii_lowercase + string.digits + '/+=' + '\n' + ' '

# La clé privée décryptée (initialisée avec le footer)
decrypted_pk = pk_footer

# Taille max espérée de la clé privée
max_key_length = 1000

# Décryptage caracère par caractère
for j in range(1, max_key_length):
    # -------------------------------------
    # 1. Identification du bloc à décrypter
    # -------------------------------------
    usable_cn_length += 1
    usable_cn_length %= 16
    expected_padding = (pk_footer_length + j ) % 16
    expected_last_encrypted_block = encrypted_pk_footers_by_padding[expected_padding]
    print(f'{j=} {expected_last_encrypted_block.hex()=}')
    
    # Boucle pour contourner le pb de taille de certificat variable
    # on fait plusieurs essais, jusqu'à ce que la fin de message corresponde à celle attendue
    while True:
        encrypted_response = register(common_name_padding + b'A' * usable_cn_length)
        last_encrypted_block = encrypted_response[-16:]
        if last_encrypted_block == expected_last_encrypted_block:
            break

    block_number = ((pk_footer_length + j) // 16)
    encrypted_block_to_decode = encrypted_response[-16  + (-16 * block_number) :-16 * block_number ]
    print(f'{encrypted_block_to_decode.hex()=}')

    # -------------------------------------
    # 2. Boucle sur tous les cas possibles du texte en clair
    # -------------------------------------
    for c in valid_car:
        encrypted_response = register(common_name_padding + c.encode() + decrypted_pk[:15])
        encryptext = encrypted_response[128:128+16]
        if encryptext.hex() == encrypted_block_to_decode.hex():
            print(f'{c=}')
            decrypted_pk = c.encode() + decrypted_pk
            #print(f'{len(encrypted_response)=}')
            break
    else:
        # Aucune correspondance trouvée : y a un bug dans l'algo => on s'arrête pour corriger
        print(f'damned !!!')
        print(f'{decrypted_pk=}')
        print(f'{len(encrypted_response)=}')
        print(f'{usable_cn_length=}')
        quit()
    
    # La clé a-t-elle été décryptée entièrement ?
    if decrypted_pk.startswith(pk_header):
        print('decryption finalized !!!')
        break

print(f'{decrypted_pk=}')

# ===================================
# Fermeture connexion
# ===================================
p.close()
