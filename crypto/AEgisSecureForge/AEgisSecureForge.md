# AEgisSecureForge

### Description

La campagne de crowdfunding pour les robots AEgisSecureForge s'est terminée dans une grande déception. Les robots que nous avons finalement reçus, avec un an de retard, ne correspondent en rien à ce qui nous avait été promis. Il y a quelques jours, l'entreprise a réuni un groupe d'influenceurs pour dévoiler ses projets futurs, et il est devenu clair qu'ils prévoient de basculer vers un modèle B2B. Malheureusement, cela signifie la fin définitive du support pour nos robots.

Avant la réunion, j'avais déjà des doutes quant à leurs intentions. Les prétendus problèmes de stabilité des serveurs ne laissaient rien présager de bon. Même s'ils ont tenté de nous rassurer, j'ai eu l'impression d'entendre une conversation entre deux développeurs dans la salle de pause, évoquant une mise à jour visant à rendre inopérants les robots de génération précédente, probablement les nôtres. J'ai profité de l'occasion pour effectuer une capture réseau dans leurs locaux. Bien que je n'aie pas encore trouvé la dernière version du firmware qu'ils mentionnaient, je garde l'espoir de la récupérer.

Cependant, je ne peux pas y parvenir seul. C'est pourquoi je fais appel à vos compétences pour m'aider à récupérer le firmware, en utilisant la capture réseau que je mets à votre disposition ici. J'espère que nous pourrons trouver des preuves de cette manœuvre pour les diffuser publiquement, afin d'éviter à un maximum d'utilisateurs de voir leurs robots devenir inutilisables.

### Fichiers joints

* [aegis.pcapng](aegis.pcapng)

----

### 1. 1er Flag = déchiffrement du message issu de PrivateBin

Le fichier `aegis.pcapng` peut être ouvert avec Wireshark.

Parmi les objets HTTP (menu : File > Export Objects > HTTP), un des contenus `text/html` (de taille ~23Ko) en provenance du site `valence.mikeofp.free.fr` attire l'attention :
- cela correspond à la trame n° 1448
- dont on peut suivre le cheminement (sur la trame > clic droit > Follow > HTTP Stream)

Voici un extrait de l'appel :

```http
GET /?960f29ac832bfe36 HTTP/1.1
Host: valence.mikeofp.free.fr
Connection: keep-alive
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 6.1; rv:6.0) Gecko/20110814 Firefox/6.0 AEgisChatBot UriPreview/0.5
X-Original-Url: http://valence.mikeofp.free.fr/?960f29ac832bfe36#2VPy/R1GCQubXa36xPmxB5TR7HfTchPQF9Wz+P+9Xqs=
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Accept-Encoding: gzip, deflate


HTTP/1.1 200 OK
Content-Type: text/html; charset=UTF-8

<!DOCTYPE html>
<html lang="en">
...
```

L'analyse du HTML montre :
- qu'il semble s'agir d'un fork de [PrivateBin](https://privatebin.info/)
- avec des données chiffrées en bas de page :
```html
<div id="cipherdata" class="hidden">{"meta":{"expire_date":1700438697,"burnafterreading":true,"opendiscussion":false,"formatter":"plaintext","postdate":1699833897,"remaining_time":604788},"data":"{\"iv\":\"3IZ8loiaVy4MowXCP+WBIQ==\",\"v\":1,\"iter\":1000,\"ks\":256,\"ts\":128,\"mode\":\"gcm\",\"adata\":\"\",\"cipher\":\"aes\",\"salt\":\"0VndpPRdv3g=\",\"ct\":\"EClLmRtbbzGDP\/1JqY\/kfWKV1GdLAi7khBjdE+t9H24eiAGVQ6sVUWv...jei66FQ+cSAA=\"}","comments":[],"comment_count":0,"comment_offset":0,"@context":"js\/paste.jsonld"}</div>
```

Si on essaie d'aller sur l'URL de départ (http://valence.mikeofp.free.fr/?960f29ac832bfe36#2VPy/R1GCQubXa36xPmxB5TR7HfTchPQF9Wz+P+9Xqs=) définie dans le header `X-Original-Url`, on s'aperçoit que le message a été supprimé : PrivateBin permet de supprimer celui-ci dès que la page a été visité (c'est l'autodestruction de celui-ci une fois qu'il a été lu :boom:)

L'analyse du code source de la page montre :
- la présence d'une fonction `decipher` dans le fichier `privatebin.js`
- que la clé de chiffrement/déchiffrement est positionée dans l'URL après le `#`
- que le password est vide

Donc un appel de cette fonction avec les paramètres suivants devrait permettre de déchiffrer le message :
- key =  `2VPy/R1GCQubXa36xPmxB5TR7HfTchPQF9Wz+P+9Xqs=`
- password = chaine vide
- data = partie `data` du json. ie : "{\"iv\":\"3IZ8loiaVy4MowXCP+WBIQ==\",\"v\":1,\"iter\":1000,\"ks\":256,\"ts\":128,\"mode\":\"gcm\",\"adata\":\"\",\"cipher\":\"aes\",\"salt\":\"0VndpPRdv3g=\",\"ct\":\"EClLmRtbbzGDP\/1JqY\/kfWKV1GdLAi7khBjdE+t9H24eiAGVQ6sVUWv...jei66FQ+cSAA=\"}

Après avoir positionné un point d'arrêt sur la méthode (et rafraichit la page pour s'arrêter à l'endroit souhaité), il suffit alors de remplacer les 3 paramètres et de continuer.

On obtient ainsi le texte en clair disponible ici : [privatebin-data-decrypted.md](privatebin-data-decrypted.md)

En bas du texte déchiffré, on trouve le 1er flag : `DGHACK{ThisCodeSmellGood,No?}`

----

### 2. Exploitation du health-check du serveur Aegis en local

Le fichier [privatebin-data-decrypted.md](privatebin-data-decrypted.md) contient également le code source d'un script python que l'on peut extraire : [server.py](server.py)

En parcourant rapidement le code, on identifie la présence d'une fonction intéressante `_handle_healthcheck` permettant de récupérer le contenu d'un fichier `FLAG` :

```python
    def _handle_healthcheck(self, check: bytes):
        res = b"HEALTH_OK"
        if check == b"\x2a":
            res = open("FLAG", "rb").read()

        logger.debug(f"|>({self.peername}) HEALTHCHECK OK")
        self.transport.write(self.encode_message_length(res))
        self.transport.write(res)
        self.transport.close()
```

Reste à comprendre comment faire pour déclencher l'appel de cette fonction.

Pour cela, pour nous aider à comprendre le comportement du serveur (en plus de l'analyse du code), on peut lancer le script en local. Cela permet aussi de valider un exploit avant de l'appliquer au serveur Aegis cible.

En analysant la fonction `data_received`, on comprend comment communiquer avec le serveur : 
- la donnée doit être composée de 2 parties séparées par `\r\n` (soit en hexa : `\x0d\x0a`)
- concernant la 1ere partie, elle doit :
    - avoir une longueur de `5` (i.e. `SIZE_HEADER`)
    - commencer par `\x4c\x04` (i.e. `MAGIC_NUMBER`)
    - le 3ème octet porte la commande à réaliser. Celle-ci doit correspondre à l'une des 3 commandes possibles. Pour appeler `_handle_healthcheck`, il faut que cela soit `\x63` (i.e. `PROTOCOL_CMD_HEALTHCHECK`)
    - les octets 4 et 5 représentent la taille de la charge utile (i.e. la 2ème partie des données positionée après le `\x0d\x0a`) en little-endian
- la 2ème partie porte la charge utile spécifique à chaque commande.

Or pour que le fichier `FLAG` soit lu, il est nécessaire que la condition `check == b"\x2a"` soit valide.
La charge utile doit donc être : `\x2a`. La taille de celle-ci est 1, soit  `\x01\x00` en little-endian.

Par conséquent, le message à envoyer est : `\x4c\x04\x63\x01\x00\x0d\x0a\x2a`

On utilise le script [client-flag2.py](client-flag2.py) qui permet de tester et valider notre exploit en local.

Mais où se trouve le serveur Aegis cible ?

----

### 3. Identification localisation du server Aegis

L'analyse du code python, corroboré par le comportement du serveur lancé en local, montre que le serveur écoute sur le port `2429`.

Dans Wireshark, il est possible de rechercher les trames pour lesquelles le port `2429` est utilisé, via le filtre `tcp.port == 2429`.

La seule destination qui écoute sur ce port est l'adresse IP `46.30.202.223`.

La recherche de réponse DNS utilisant cette adresse, via le filtre `dns.a == 46.30.202.223`, indique `aegissecureforgeserver.chall.malicecyber.com` comme alias.

Un simple `ping` sur cet alias permet de confirmer la correspondance avec l'adresse IP.

Un simple `nc aegissecureforgeserver.chall.malicecyber.com 2429` permet de confirmer qu'il y a bien quelque chose qui écoute.

----

### 4. Récupération du 2ème flag

Maintenant que l'on a localisé le serveur Aegis, il suffit de renouveler l'exploit sur celui-ci pour obtenir le 2ème flag : `DGHACK{SeemsLike.YoureOnTheRightTrack!}`

----

### 5. C'était quoi déjà l'objectif ?

Petit retour sur l'énoncé : il faut récupérer un firmware.

En interrogeant le serveur, il semble possible de récupérer le firmware, si on arrive à déclencher l'appel de la fonction `_handle_get_latest`. Pour cela, il faut envoyer la commande `\x14` (i.e. `PROTOCOL_CMD_GET_LATEST`), avec un certificat valide en payload.

En y regardant de plus près, on voit que la réponse du serveur est alors composée de plusieurs parties :
- `encrypted_firmware` : le firmware chiffré avec AES-128 en mode CBC, en utilisant un [padding PKCS7](https://en.wikipedia.org/wiki/Padding_(cryptography)#PKCS#5_and_PKCS#7)
- `ecies_cipher` : une version chiffrée de la clé de chiffrement `SECRET_KEY`
- `ecies_iv` : une version chiffrée de l'iv (ie le vecteur d'initialisation) `SECRET_IV`

Voici un schéma, issu d'un article [Wikipedia](https://fr.wikipedia.org/wiki/Mode_d%27op%C3%A9ration_(cryptographie)#%C2%AB_Cipher_Block_Chaining_%C2%BB_(CBC):_encha%C3%AEnement_de_blocs), qui montre le principe du chiffrement AES en mode CBC :

![principe de chiffrement AES en mode CBC](schema_AES_CBC.png)

L'algorithme de chiffrement `CoinCurveECCBackend` de la clé et de l'iv se base sur une coube elliptique générée à partir de la clé privée du serveur Aegis `_server_key`.

Nous voilà bien avancé :
- sans certificat, impossible de déclencher cette commande `PROTOCOL_CMD_GET_LATEST`
- même si on arrive à obtenir un certificat et déclencher la commande, sans la clé privée du serveur, impossible de déchiffrer le firmware.

----

### 6. On fait quoi maintenant ?

La dernière commande `\x0a` (ie `PROTOCOL_CMD_REGISTER`) permet de déclencher la fonction `_handle_registration`.

Cette fonction génère un certificat `cert_der` au format DER pour le `common_name` fourni en payload de la commande.

La réponse du serveur est composée des éléments suivants :
- `serial_enc` : le numéro de série du certificat généré
- `encrypted_response` : un message chiffré composé par le certificat généré et la clé privée du serveur au format PEM (`cert_der + b"\r\n" + self._server_pem`). On note que le séparateur utilisé (`\r\n`) est le même que celui utilisé pour séparer les données envoyées (entre la commande et le payload).

Le chiffrement utilise l'algorithme AES-128, en mode ECB, avec ici aussi un padding PKCS7.

Voici un schéma, issu d'un article [Wikipedia](https://fr.wikipedia.org/wiki/Mode_d%27op%C3%A9ration_(cryptographie)#%C2%AB_Electronic_Codebook_Block_%C2%BB_(ECB):_dictionnaire_de_codes), qui montre le principe du chiffrement AES en mode ECB :

![principe de chiffrement AES en mode ECB](schema_AES_ECB.png)

Si on arrive à déchiffer le message, on pourra alors :
- utiliser le certificat en payload de la commande `PROTOCOL_CMD_GET_LATEST`
- puis, en déchiffrer la réponse grace à la clé privée du serveur

----

### 7. Retour dans Wireshark

Dans Wireshark, le filtre `(tcp.port == 2429) && (tcp.flags == 0x018)` permet de se limiter aux données échangées avec le serveur Aegis.

Maintenant qu'on comprend comment les communications fonctionnent avec le serveur, on voit :
- la commande envoyée :
    - trame 2712 : l'appel de la commande `PROTOCOL_CMD_GET_LATEST`
    - trame 2713 : le payload associé qui contient un certificat qui a été généré avec le common_name `gitlab-ci.pipeline-928`
- la réponse reçue :
    - trame 2716 : la taille du message qui suit
    - trame 2718 : le message qui contient probablement le firmware chiffré
    - trame 2720 : la taille du message qui suit
    - trame 2722 : le message qui contient probablement la clé chiffrée
    - trame 2724 : la taille du message qui suit
    - trame 2726 : le message qui contient probablement l'iv chiffré

De la trame 2713, on peut en extraire le certificat [gitlab-ci.pipeline-928.der](gitlab-ci.pipeline-928.der).

Celui-ci semble valide du 13/11/2023 au 12/11/2024 : il devrait donc encore être utilisable.

Le script [client-send-wireshark-cert.py](client-send-wireshark-cert.py) permet de réaliser cette opération :
- en local, le serveur indique que le certificat n'est pas valide : normal puisqu'on ne dispose pas des certificats qui ont été utilisés pour le générer
- en distant, la communication est coupée : vraisemblablement il en est de même. Les secrets ont dû être changés entre temps.

Ce certificat ne va donc pas pouvoir être exploité, ni même la réponse (puisque la clé privée du serveur a surement aussi été modifiée)

Retour à la case départ.

----

### 8. Exploitation du common_name

Rappel : la commande `PROTOCOL_CMD_REGISTER` génère un certificat à partir d'un common_name fourni, et nous renvoie un message chiffré (via AES-128 en mode ECB avec padding PKCS7) contenant ce certificat, ainsi que la clé privée du serveur.

La fragilité de cette opération réside dans le fait que l'on a accès à volonté à cette opération, permettant ainsi de faire la correspondance entre n'importe quel message en clair connu et son chiffré, par l'intermédiaire du common_name.

En effet, comme l'algorithme chiffre le message en clair, bloc par bloc, il suffit de s'arranger pour que le contenu du common_name, dont on souhaite connaître le chiffré, soit calé sur un bloc.

En AES, les blocs font 16 octets (ou 16 bytes).

Si on a de la chance, le common_name se retrouve positionné pile-poil sur un début de bloc. Sinon, il va falloir trouver le padding qui va bien à appliquer au début du common_name pour se caler correctement ensuite sur un début de bloc.

Pour trouver le padding et la localisation du common_name dans le chiffré, plusieurs possibilités.

1ère possibilité : Expérimenter.  
On peut partir sur une base 2 blocs (soit 32 octets) composée que de `A`.  
Si le common_name est en début de bloc, alors on devrait trouver dans le message chiffré 2 blocs identiques qui se suivent.  
Si ce n'est pas le cas, on rajoute au début des 32 `A` un octet supplémentaire (par exemple `B`).  
On poursuit la démarche jusqu'à obtenir 2 blocs consécutifs identiques.  
Le nombre de `B` rajoutés correspond au padding que l'on va appliquer.

2ème possibilité : Comprendre.  
Il s'agit ici de comprendre comment un certificat est construit.  
J'ai trouvé l'article suivant très intéressant pour démystifier x509 et faciliter ensuite si besoin la compréhension de la RFC : https://www.cryptologie.net/article/262/what-are-x509-certificates-rfc-asn1-der/  
On y trouve également la référence à un outil en ligne qui permet de décoder un certificat : https://lapo.it/asn1js/  
On peut l'expérimenter sur le certificat récupéré de wireshark.  
On voit alors que `gitlab-ci.pipeline-928` est positionné à l'offset 120.  
On est au milieu d'un bloc. Le prochain bloc commençant à l'offset 128, un padding de 8 octets est donc nécessaire.  
On comprend aussi au passage que si le common_name dépasse les 255 octets, la structure du certificat va un peu changer. On va donc se limiter à cette taille.

Quelle que soit la méthode, on détermine :
- qu'il est nécessaire de préfixer le common_name par 8 octets de padding
- que l'on pourra alors retrouver la version chiffrée de la partie "utilisable" du common_name à partir de l'offset 128.
- qu'il est judicieux que cette partie utilisable soit un multiple de 16 octets, si on veut avoir la correspondance entre un message en clair et son chiffré.

NB : il existe une taille limite sur le common_name transmis au serveur. Celle-ci ne peut pas dépasser `65.535` octets (ie. `0xFFFF`). Ceci est lié au fait que la taille du payload doit être exprimée en hexa sur 2 octets.

----

### 9. Récupération de la clé privée du serveur

Pour rappel, la réponse de la commande `PROTOCOL_CMD_REGISTER` se termine par le contenu de la clé privée au format PEM.

Voici un exemple de clé privée au format PEM :
```pem
-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgI1B54rxMw5laxHG3
kPsG6nhRpOzzYNX0dma1dnCk8kWhRANCAAQdB5cceNl2fAoaKCf/SK9qaNdu3oMW
nSw7n9a3iOHWSfGQSdHqR8wvZ//gtmS5Agh7QXUlkRE/yHS32hINNQGj
-----END PRIVATE KEY-----

```

Donc, dans sa version en clair, la partie du message correspondant à la clé privée est de la forme : `-----BEGIN PRIVATE KEY-----\nXXXXXXXXX\n-----END PRIVATE KEY-----\n`

On en connait donc le début : `-----BEGIN PRIVATE KEY-----\n` et la fin : `\n-----END PRIVATE KEY-----\n`

Un padding PKCS7 étant appliqué au message, le contenu du dernier bloc, avant chiffrement, est l'une des 16 possibilités suivantes :
```
IVATE KEY-----\n\x01
VATE KEY-----\n\x02\x02
ATE KEY-----\n\x03\x03\x03
TE KEY-----\n\x04\x04\x04\x04
E KEY-----\n\x05\x05\x05\x05\x05
 KEY-----\n\x06\x06\x06\x06\x06\x06
KEY-----\n\x07\x07\x07\x07\x07\x07\x07
EY-----\n\x08\x08\x08\x08\x08\x08\x08\x08
Y-----\n\x09\x09\x09\x09\x09\x09\x09\x09\x09
-----\n\x0a\x0a\x0a\x0a\x0a\x0a\x0a\x0a\x0a\x0a
----\n\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b
---\n\x0c\x0c\x0c\x0c\x0c\x0c\x0c\x0c\x0c\x0c\x0c\x0c
--\n\x0d\x0d\x0d\x0d\x0d\x0d\x0d\x0d\x0d\x0d\x0d\x0d\x0d
-\n\x0e\x0e\x0e\x0e\x0e\x0e\x0e\x0e\x0e\x0e\x0e\x0e\x0e\x0e
\n\x0f\x0f\x0f\x0f\x0f\x0f\x0f\x0f\x0f\x0f\x0f\x0f\x0f\x0f\x0f
\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10
```

En utilisant ces 16 valeurs (préfixée par 8 octets, par exemple `AAAAAAAA`), en tant que common_name, on peut récupérer leurs correspandances chiffrées (au niveau du bloc chiffré débutant à l'offset 128), en retour.

Une de ces 16 valeurs correspond forcément aussi à la fin du message de retour.

Sauf que la fin du message chiffré n'est pas toujours la même.  
Après quelques tests, et en analysant le comportement au niveau du serveur, on se rend compte que le certiticat généré `cert_der` n'a pas toujours la même longueur. La variation opère au niveau de la signature qui est positionnée en toute fin.  
On va donc utiliser les 16 derniers octets renvoyés le plus grand nombre de fois, comme référence de fin de message.

Maintenant que la fin de message est déterminée, on va pouvoir "remonter" caractère par caractère vers le début.

Pour gagner un peu de temps, on commence par se caler, en déterminant la longueur de common_name nécesaire, afin que les 2 derniers blocs contiennent : 
```
bloc n-1: \n-----END PRIVAT
bloc n  : E KEY-----\n\x05\x05\x05\x05\x05
```

Puis, on rajoute un caractère supplémentaire au common_name.

Les 2 derniers blocs contiennent alors :
```
bloc n-1 : X\n-----END PRIVA
bloc n   : TE KEY-----\n\x04\x04\x04\x04
```

En faisant varier la valeur de `Y` dans le common_name suivant `AAAAAAAA` + `Y` + `\n-----END PRIVA`, a un moment donné, la valeur chiffrée va être identique à celle du bloc n-1. On obtient ainsi la valeur de `X`.

Etant donné que la clé est au format PEM, les valeurs possibles de `Y` sont dans : `[a-z][A-Z][0-9]/+=`, auxquelles on peut rajouter `\n`, `-` et *`espace`*.

On poursuit ainsi caractère par caractère, jusqu'au début de la clé privée : [aegissecureforgeserver.chall.malicecyber.com_aegis.root.pem](aegissecureforgeserver.chall.malicecyber.com_aegis.root.pem)

Voici le script utilisé pour récupérer la clé privée : [client-extract-pk.py](client-extract-pk.py)

On ne peut pas aller plus loin, car `\r\n` étant utilisé comme séparateur de données par le serveur, un common_name contenant cette valeur serait mal interprété. Il faut donc trouver un autre moyen pour obtenir un certificat valide.

----

### 10. Génération d'un certificat

En regardant de plus près la commande `PROTOCOL_CMD_GET_LATEST`, on s'aperçoit que les vérifications sur le certificat se limitent à :

```python
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
```

Il suffit donc d'avoir :
- un certificat au format DER
- signé par `AEgisSecureForge`
- signé ave la clé privée du serveur

On dispose donc de tous les éléments pour forger un certificat valide.

Le script [forge-cert.py](forge-cert.py) permet de générer un tel certificat.

----

### 11. Récupération du firmware.

Maintenant qu'on dispose d'un certificat, on peut à nouveau solliciter la commande `PROTOCOL_CMD_GET_LATEST`.

On récupère alors les 3 éléments : `encrypted_firmware`, `ecies_cipher` et `ecies_iv`.

On commence par déchiffrer `ecies_cipher` et `ecies_iv` avec la clé privée du serveur.

Puis, ces 2 éléments obtenus, le déchiffrement du `encrypted_firmware` devient possible.

Une fois le déchiffrement réalisé, un padding PKCS7 ayant été appliqué sur le contenu en clair du firmware, il est nécessaire d'effectuer l'opération inverse : le nombre d'octets à supprimer à la fin correspond à la valeur du dernier octet.

Le script [client-recup-firmware.py](client-recup-firmware.py) permet de récupérer le [firmware](firmware)

----

### 12. Analyse du firmware

Le fichier `firmware` récupéré est compressé. Après décompression, il s'avère qu'il s'agit d'un binaire Unix 64 bits :

```bash
# Type du fichier firmware
$ file firmware
firmware: gzip compressed data, was "firmware", last modified: Sun Oct 22 12:46:58 2023, max compression, from Unix, original size modulo 2^32 14368

# Décompression du fichier
$ gunzip -c firmware > decompressed_firmware

# Type du fichier décompressé
$ file decompressed_firmware
decompressed_firmware: ELF 64-bit LSB executable, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, for GNU/Linux 3.2.0, stripped
```

Suivant le degré de confiance qu'on a dans ce binaire, et de l'environnement plus ou moins étanche dans lequel on se situe, on peut :
- décompiler le binaire
- lancer le binaire

Une décompilation du binaire, avec Ghidra par exemple, fait apparaître les 2 fonctions suivantes :
```c
undefined8 FUN_004011c2(void)
{
    FUN_00401170("Critical error occurred!","WellDone.YouFoundTh3Secr3tF1rmware!");
}


void FUN_00401170(undefined8 param_1,undefined8 param_2)
{
  printf("[ERROR] %s (Error Code: DGHACK{%s})\n",param_1,param_2);
  return;
}
```

Alors que le lancement du binaire produit la sortie suivante :
```
$ ./decompressed_firmware
[INFO] Firmware started.
[INFO] Performing initialization...
[DEBUG] Memory allocated.
[WARNING] Low battery level detected.
[INFO] Configuring settings...
[DEBUG] Settings loaded.
[DEBUG] Settings validated.
[INFO] Connecting to network...
[WARNING] Unstable network connection detected.
[DEBUG] Retrying connection...
[INFO] Synchronizing data...
[DEBUG] Data synchronization in progress...
[INFO] Executing firmware...
[DEBUG] Executing Step 1: Preparing resources...
[DEBUG] Executing Step 2: Performing calculations...
[DEBUG] Executing Step 3: Updating firmware...
[ERROR] Critical error occurred! (Error Code: DGHACK{WellDone.YouFoundTh3Secr3tF1rmware!})
[INFO] Rolling back changes...
[DEBUG] Changes rolled back.
[INFO] Finalizing firmware...
[DEBUG] Cleaning up resources...
[INFO] Firmware execution completed.
```

Dans les 2 cas, on obtient facilement le 3ème et dernier flag : `DGHACK{WellDone.YouFoundTh3Secr3tF1rmware!}`
