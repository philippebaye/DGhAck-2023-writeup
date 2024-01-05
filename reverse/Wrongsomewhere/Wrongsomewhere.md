# Wrongsomewhere

### Description

Un nouveau ransomware se propage sur internet.

Trop de vieilles dames se font arnaquer par celui-ci, il est temps d'agir !

Une des victimes nous a accordé l'accès à distance à sa machine, veuillez enquêter et trouver la clé pour déchiffrer les fichiers.

Attention à ne pas lancer le ransomware sur une machine autre que celle fournie.

### Fichiers joints

* [wrongsomewhere.exe](wrongsomewhere.exe.donotexe)

----

En prenant au sérieux l'avertissement, et pour éviter une erreur de manipulation, le fichier `wrongsomewhere.exe` est renommé en `wrongsomewhere.exe.donotexe`

On utilise ensuite un décompileur (ici Ghidra).

Voici un extrait du code de la fonction `main` ainsi obtenu :
```c
int __cdecl main(int _Argc,char **_Argv,char **_Env)
{
  int iVar1;
  undefined8 uVar2;
  char *pcVar3;
  char local_338 [256];
  char local_238 [268];
  DWORD local_12c;
  undefined8 local_128 [33];
  DWORD local_1c;
  HKEY local_18;
  uint local_c;

  __main();
  _Z2opPc(&stda);
  local_c = RegOpenKeyExA((HKEY)0xffffffff80000001,&stda,0,0x20019,&local_18);
  if (local_c == 0) {
    local_12c = 0x100;
    local_c = RegQueryValueExA(local_18,"error",(LPDWORD)0x0,&local_1c,(LPBYTE)local_128,&local_12c)
    ;
    if (local_c == 0) {
      RegCloseKey(local_18);
      if (_Argc < 2) {
        if (_Argc == 1) {
          pcVar3 = getcwd(local_238,0x104);
          if (pcVar3 == (char *)0x0) {
            perror("getcwd() error");
            iVar1 = 1;
          }
          else {
            printf("Current working dir: %s\n",local_238);
            printf("Enter key: ");
            scanf("%255s",local_338);
            iVar1 = strcmp((char *)local_128,local_338);
            if (iVar1 == 0) {
              printf("Encrypting/decrypting current folder %s\n",local_238);
              _Z22encrypt_decrypt_folderPcS_(local_238,local_128);
              iVar1 = 0;
            }
            else {
              puts("Wrong key");
              iVar1 = 1;
            }
          }
        }
        else {
          iVar1 = 0;
        }
      }
      else {...}
    }
    ...
  }
  ...
}
```

Plusieurs fonctions utilisées permettent de manipuler les clés de registre Windows, dont les 2 principales sont :

- [`RegOpenKeyExA`](https://learn.microsoft.com/en-us/windows/win32/api/winreg/nf-winreg-regopenkeyexa) : permet de se positionner sur une clé à partir d'une racine
    * la racine utilisée est ici `0x80000001`, ce qui correspond à `HKEY_CURRENT_USER`
    * la clé recherchée est `&stda` ; on note que `&stda` est déterminé via la fonction `_Z2opPc`
    * la clé est stockée dans `local_18`

- [`RegQueryValueExA`](https://learn.microsoft.com/en-us/windows/win32/api/winreg/nf-winreg-regqueryvalueexa) : permet de lire la valeur d'un attribut associé à une clé :
    * l'attibut recheché est `error`
    * associé à la clé `local_18`
    * la valeur est stockée dans `local_128`

Si l'exécutable est lancé sans paramètre (ie. condition `_Argc == 1`) alors :
- on est invité à saisir la clé de déchiffrement : `scanf("%255s",local_338)`
- la saisie est comparée avec celle stockée en clé de registre : `strcmp((char *)local_128,local_338)`
- si ça matche, le répertoire courant (précédemment récupéré via `getcwd`) est alors déchiffré en utilisant cette clé.

Pour rappel, la clé de registre est déterminée via l'appel à la fonction `_Z2opPc` :
```c
void _Z2opPc(byte *param_1)
{
  size_t sVar1;
  byte *local_18;
  int local_10;
  int local_c;

  sVar1 = strlen((char *)param_1);
  local_18 = param_1;
  for (local_c = 0; (ulonglong)(longlong)local_c < sVar1; local_c += local_10) {
    for (local_10 = 0; (*local_18 != 0 && (local_10 < 4)); local_10 += 1) {
      *local_18 = *local_18 ^ (&to)[local_10];
      local_18 = local_18 + 1;
    }
  }
  return;
}
```

Il suffit donc d'exécuter cette foncion avec `&stda` en paramètre.

En voici une traduction en python : [`decode-key.py`](./decode-key.py)

On en déduit donc que la clé de déchiffrement est stockée :
- dans l'attribut `error`
- au niveau de la clé de registre `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run\OneDrive`

On récupère ainsi la clé de déchiffrement : `ZndeAeUrTltyJVZvFVOJrKcFhkIhqljzryWPdUQpakaGPjiyBniXvenYwMvU`

Le dossier `Documents` présent sur le Bureau contient un fichier `flag.txt` chiffré.
On copie l'exécutable `wrongsomewhere.exe` dans ce répertoire, puis on l'exécute.
Le fichier est alors déchiffré et contient :
```
DGHACK{R4nS0mW4r3s_4r3_4_Cr1m3_D0_n0t_Us3_Th1s_0n3_F0r_3v1l}
```

Le flag est donc : `DGHACK{R4nS0mW4r3s_4r3_4_Cr1m3_D0_n0t_Us3_Th1s_0n3_F0r_3v1l}`
