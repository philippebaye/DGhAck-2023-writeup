Hi John,

I'm sick today, so I can't make it to the office. As I told you on telegram, last night, I fixed the issue with ticket 202 regarding the update server.
Here's the updated source code. I didn't leave any comments, but if you have any questions, feel free to give me a call.
I'll do my best to respond over the phone. I know you can handle it.

I should be back next week. Take care.

See you soon,
Zack

---

# server.py

```python
import asyncio
from enum import Enum
import logging
import os
import struct
from typing import Optional
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, padding, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from eth_keys import KeyAPI
from ecies import encrypt as ecies_encrypt

import datetime


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s,%(msecs)d %(levelname)s: %(message)s",
)

logger = logging.getLogger("AEgisSecureForge")

SHARED_KEY = os.environ.get("AESF_SHARED_KEY", "DEV-KEY.CHANGEIT").strip().encode()
SECRET_KEY = os.environ.get("AESF_SECRET_KEY", "DEV-KEY.CHANGEIT").strip().encode()
SECRET_IV = os.environ.get("AESF_SECRET_IV", "DEV-IV..CHANGEIT").strip().encode()

MAGIC_NUMBER = (1100).to_bytes(2, "little")


class AESFP_CMDS(Enum):
    PROTOCOL_CMD_REGISTER = (10).to_bytes(1, "little")
    PROTOCOL_CMD_GET_LATEST = (20).to_bytes(1, "little")
    PROTOCOL_CMD_HEALTHCHECK = (99).to_bytes(1, "little")


SIZE_HEADER = 5


class AEgisSecureForgeProtocol(asyncio.Protocol):
    def __init__(self):
        with open("config/aegis.root.pem", "rb") as server_key_file, open(
            "config/aegis.client.pem", "rb"
        ) as client_key_file, open("config/aegis.root.cert", "rb") as root_cert_file:
            self._server_pem = server_key_file.read()
            self._server_key = serialization.load_pem_private_key(
                self._server_pem, password=None, backend=default_backend()
            )

            self._client_pem = client_key_file.read()
            self._client_key = serialization.load_pem_private_key(
                self._client_pem, password=None, backend=default_backend()
            )

            self._root_certificate = x509.load_der_x509_certificate(
                root_cert_file.read()
            )

    def connection_made(self, transport):
        self.transport = transport

        ip, port = self.transport.get_extra_info("peername")
        self.peername = f"{ip}:{str(port)}"

        self._reset()

        logger.info(f"<|({self.peername}) Connected")

    def connection_lost(self, exc: Exception | None) -> None:
        if exc:
            logger.error(f"<|({self.peername}) Unhandled exception: {exc}")
        logger.info(f"<|({self.peername}) Disconnected")

    def encode_message_length(self, message: bytes) -> bytes:
        length_bytes = struct.pack("I", len(message))
        packed_length = struct.pack("4s", length_bytes)
        return packed_length

    def _reset(self):
        self._max_buffer_size = SIZE_HEADER
        self._current_cmd = None
        self._buffer: bytes = b""

    def data_received(self, data: bytes):
        datas = data.split(b"\r\n")
        if not datas:
            return

        logger.debug(f"<|({self.peername}) PACKET Received : {datas}")

        if not self._current_cmd:
            if len(self._buffer) < self._max_buffer_size:
                self._buffer += datas[0]

            if len(self._buffer) > SIZE_HEADER:
                logger.error(f"<|({self.peername}) INVALID COMMAND HEADER")
                self.transport.close()
                return

            if len(self._buffer) == self._max_buffer_size:
                pkt_magic_number = self._buffer[:2]
                if pkt_magic_number != MAGIC_NUMBER:
                    logger.error(
                        f"<|({self.peername}) INVALID MAGIC PACKET {pkt_magic_number}"
                    )
                    self.transport.close()
                    return

                pkt_cmd = self._buffer[2:3]
                if pkt_cmd not in (
                    member.value for member in AESFP_CMDS.__members__.values()
                ):
                    logger.error(f"<|({self.peername}) INVALID COMMAND {pkt_cmd}")
                    self.transport.close()
                    return

                cmd_name = AESFP_CMDS(pkt_cmd).name
                pkt_size = int.from_bytes(
                    self._buffer[3:SIZE_HEADER], byteorder="little"
                )

                self._buffer = b""
                self._current_cmd = pkt_cmd
                self._max_buffer_size = pkt_size
                datas = [datas[1]] if len(datas) > 1 else []

                logger.debug(
                    f"<|({self.peername}) [COMMAND] Name: {cmd_name} Argument length required: {pkt_size} bytes"
                )

        if len(datas) < 1:
            return

        if self._current_cmd:
            if len(self._buffer) < self._max_buffer_size:
                self._buffer += datas[0][
                    : max(self._max_buffer_size - len(self._buffer), 0)
                ]

            if len(self._buffer) == self._max_buffer_size:
                cmd_name = AESFP_CMDS(self._current_cmd).name
                logger.debug(
                    f"<|({self.peername}) [{cmd_name}] Received argument : {self._buffer}"
                )

                if cmd_name == AESFP_CMDS.PROTOCOL_CMD_REGISTER.name:
                    self._handle_registration(self._buffer)
                elif cmd_name == AESFP_CMDS.PROTOCOL_CMD_GET_LATEST.name:
                    self._handle_get_latest(self._buffer)
                elif cmd_name == AESFP_CMDS.PROTOCOL_CMD_HEALTHCHECK.name:
                    self._handle_healthcheck(self._buffer)

                self._reset()

    def _handle_registration(self, common_name: bytes):
        cert = generate_certificate(
            common_name.decode(),
            self._client_key,
            self._root_certificate,
            self._server_key,
        )
        cert_der = cert.public_bytes(encoding=serialization.Encoding.DER)

        response = cert_der + b"\r\n" + self._server_pem

        cipher = Cipher(algorithms.AES(SHARED_KEY), modes.ECB())
        encrypt = cipher.encryptor()
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_response = padder.update(response) + padder.finalize()
        encrypted_response = encrypt.update(padded_response) + encrypt.finalize()

        serial_enc = cert.serial_number.to_bytes(21, "little")
        self.transport.write(self.encode_message_length(serial_enc))
        self.transport.write(serial_enc)

        self.transport.write(self.encode_message_length(encrypted_response))
        self.transport.write(encrypted_response)

        logger.info(
            f"i| ({self.peername}) {common_name.decode()} succesfully enrolled (id: {cert.serial_number})"
        )

    def _handle_healthcheck(self, check: bytes):
        res = b"HEALTH_OK"
        if check == b"\x2a":
            res = open("FLAG", "rb").read()

        logger.debug(f"|>({self.peername}) HEALTHCHECK OK")
        self.transport.write(self.encode_message_length(res))
        self.transport.write(res)
        self.transport.close()

    def _handle_get_latest(self, certificate: bytes):
        cert = x509.load_der_x509_certificate(certificate)

        try:
            if not cert.verify_directly_issued_by(self._root_certificate):
                pass
        except Exception:
            logger.exception(
                f"[{AESFP_CMDS(self._current_cmd).name}] Invalid certificate"
            )
            self.transport.close()
            return

        ethk = KeyAPI("eth_keys.backends.CoinCurveECCBackend")
        sk = ethk.PrivateKey(
            self._server_key.private_numbers().private_value.to_bytes(
                (self._server_key.key_size + 7) // 8, "big"
            )
        )

        ecies_cipher = ecies_encrypt(sk.public_key.to_hex(), SECRET_KEY)
        ecies_iv = ecies_encrypt(sk.public_key.to_hex(), SECRET_IV)

        firmware = open("firmware", "rb").read()
        cipher = Cipher(algorithms.AES(SECRET_KEY), modes.CBC(SECRET_IV))
        encrypt = cipher.encryptor()
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_firmware = padder.update(firmware) + padder.finalize()
        encrypted_firmware = encrypt.update(padded_firmware) + encrypt.finalize()

        self.transport.write(self.encode_message_length(encrypted_firmware))
        self.transport.write(encrypted_firmware)

        self.transport.write(self.encode_message_length(ecies_cipher))
        self.transport.write(ecies_cipher)

        self.transport.write(self.encode_message_length(ecies_iv))
        self.transport.write(ecies_iv)

        logger.info(f"i| ({self.peername}) {cert.subject} Firmware sent")


def handle_exception(loop, context):
    name = context.get("future").get_coro().__name__
    msg = context.get("exception", context["message"])
    logger.critical(f"Caught exception from {name}: {msg}")


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


def verify_config_files():
    if not os.path.isfile("config/aegis.root.pem"):
        logger.warning("No server key found, generating a new one...")
        root_key = generate_ecc_key()
        with open("config/aegis.root.pem", "wb") as key_file:
            key_file.write(root_key)
        logger.warning("New server key generated.")

    if not os.path.isfile("config/aegis.client.pem"):
        logger.warning("No client key found, generating a new one...")
        client_key = generate_ecc_key()
        with open("config/aegis.client.pem", "wb") as key_file:
            key_file.write(client_key)
        logger.warning("New client key generated.")

    if not os.path.isfile("config/aegis.root.cert"):
        logger.warning("No root certificate found, generating a new one...")
        root_key = serialization.load_pem_private_key(
            open("config/aegis.root.pem", "rb").read(),
            password=None,
            backend=default_backend(),
        )
        root_cert = generate_certificate("AEgisSecureForge", root_key)
        with open("config/aegis.root.cert", "wb") as cert_file:
            cert_file.write(root_cert.public_bytes(encoding=serialization.Encoding.DER))
        logger.warning("New root certificate generated.")


async def main(port: int = 2429):
    verify_config_files()

    loop = asyncio.get_running_loop()
    server = await loop.create_server(
        lambda: AEgisSecureForgeProtocol(), "0.0.0.0", port
    )
    async with server:
        logger.info(
            f"""
*********** Release Manager ***********
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
          
|> Server listening on 0.0.0.0:{port}
"""
        )
        await server.serve_forever()


loop = asyncio.new_event_loop()
loop.set_exception_handler(handle_exception)
try:
    loop.run_until_complete(main())
except KeyboardInterrupt as exc:
    logger.info("Attempting graceful shutdown, press Ctrl+C again to exit…")
    tasks = asyncio.all_tasks(loop=loop)
    for task in tasks:
        task.cancel()
    loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
finally:
    loop.close()
    logger.info(
        f"""

~~~ Server shutdown ~~~

"""
    )

```

DGHACK{ThisCodeSmellGood,No?}