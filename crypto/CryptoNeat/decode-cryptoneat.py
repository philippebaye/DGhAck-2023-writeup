import base64

# ============================================================
# Préparation des données
# ============================================================
# Applique un padding PKCS7 sur un message
def do_pkcs7_padding(bytes_message:bytes) -> bytes:
    message_length = len(bytes_message)
    pad_value = - message_length % 16
    bytes_message += chr(pad_value).encode() * pad_value
    return bytes_message

# -----------------
# P2
# -----------------
cryptoThanks = 'Build with love, kitties and flowers'
plaintext2 = cryptoThanks.encode()
plaintext2 = do_pkcs7_padding(plaintext2)
print(f'{plaintext2=}')
# -----------------

# -----------------
# C2
# -----------------
encryptedMsg2 = '34aff6de8f8c01b25c56c52261e49cbdC19FW3jqqqxd6G/z0fcpnOSIBsUSvD+jZ7E9/VkscwDMrdk9i9efIvJw1Fj6Fs0R'
ciphertext2 = encryptedMsg2[32:]
ciphertext2 = base64.b64decode(ciphertext2)
print(f'{ciphertext2=}')
# -----------------

# -----------------
# IV (juste pour info)
# -----------------
iv = encryptedMsg2[:32]
print(f'{iv=}')
# -----------------

# -----------------
# C1
# -----------------
encryptedMsg = '34aff6de8f8c01b25c56c52261e49cbddQsBGjy+uKhZ7z3+zPhswKWQHMYJpz7wffAe4Es/bwrJmMo99Kv7XJ8P63TbN/8X'
ciphertext = encryptedMsg[32:].encode()
ciphertext = base64.b64decode(ciphertext)
print(f'{ciphertext=}')
# -----------------


# ============================================================
# Décryptage du message
# ============================================================
plaintext = bytes([pt2_car ^ ct_car ^ ct2_car for pt2_car, ct_car, ct2_car in zip(plaintext2, ciphertext, ciphertext2)])
print(f'{plaintext=}')
