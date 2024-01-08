# A_Maritime_Journey

### Description

Vous faîtes partie d'une compagnie de sauvetage en mer opérant dans la rade de Brest et alentours.

Pendant sa dernière escale, le capitaine de l'un de vos remorqueurs d'intervention, d'assistance et de sauvetage (RIAS) indique qu'il a obvservé des anomalies sur son GPS lors des dernières missions.

Vous avez été chargé d'investiguer en analysant les données recupérés sur l'ECDIS (Electronic Chart Display and Information System) du "Sam Brandy".

----

:warning: La solution proposée est partielle : elle permet uniquement de récupérer les cinq premiers des six flags.

----

### Flag 1 : Unknow frame

> Pour commencer votre investigation, vous devez retrouver le standard utilisé par les systèmes de navigation  
> dont voici l'une des trames :  
> $GPRMC,.00,A,4821.984,N,00429.118,W,17.0,170.4,2023,,,A,S*09  
> Format du Flag: DGHACK{nom_du_standard_numéro} (tout attaché, sans underscore)

Une rapide recherche permet de trouver que les trames GPRMC font référence à la norme [NMEA 0183](https://fr.wikipedia.org/wiki/NMEA_0183)

Le 1er flag est donc : `DGHACK{NMEA0183}`

----

### Flag 2 : Geographical benchmark

> Lors de vos analyses, vous avez besoin de retrouver l'une des routes maritime empruntée par le Sam Brandy.  
> Retrouver les coordonnées GPS à partir de la trame suivante :  
> $GPGGA,123519,4815.970,N,0447.340,W,1,08,0.9,545.4,M,46.9,M, ,*41  
> Donnez le résultat au format "degré" "minute" "seconde" (arrondi au centième de seconde).  
> Format du Flag : DGHACK{DDMMSS.SS[N|S],DDMMSS.SS[W|E]}

La spécification des trames [GPGGA](https://gpsd.gitlab.io/gpsd/NMEA.html#_gga_global_positioning_system_fix_data) permet d'en comprendre la structure.

La position GPS est donc : 4815.970 N - 0447.340 W

Il reste alors à convertir la partie décimale des minutes en secondes (en appliquant le facteur 60/10.000) :
- 9700 => 58.20''
- 3400 => 20.40''

Le 2ème flag est donc : `DGHACK{481558.20N,044720.40W}`

----

### Flag 3 : Fast Sentence

> Pour comprendre la cinématique du remorqueur et la cohérence des données de navigation envoyées à l'ECDIS, vous avez besoin de régénérer vous-même certaines données :  
> Trouver le moyen de générer la bonne trame VTG émise par le Système GPS sachant que notre navire va à 3.24 nœuds, que son cap réel est de 34.8° et que son cap vrai magnétique est de 24.2°. Sachant que le mode autonome est utilisé.  
> Attention, ne mettez pas de 0 devant les métriques (écrivez 34.8 et non pas 034.8). La vitesse en Km/h sera arrondie au chiffre supérieur sans indiquer de virgule.  
> Format du Flag : DGHACK{trame_VTG}

La spécification des trames [GPVTG](https://gpsd.gitlab.io/gpsd/NMEA.html#_vtg_track_made_good_and_ground_speed) indique comment celles-ci sont construites.

Parmi les informations nécessaires, il manque :
- la vitesse en Km/h, qui peut être calculée à partir de celle fournie en Noeuds.
    + 3,24 noeuds <=> 6,00048 km/h => on retient `6`` km/h
- le checksum de la trame. Celui-ci peut être calculé en suivant par exemple l'implémentation proposée [ici](https://rietman.wordpress.com/2008/09/25/how-to-calculate-the-nmea-checksum/). En l'appliquant le calcul sur la chaine comprise entre `$` et `*`, on obtient `05`.

Le 3ème flag est donc : `DGHACK{$GPVTG,34.8,T,24.2,M,3.24,N,6,K,A*05}`

----

### Flag 4 : What a time to be on sea!

> Il semble que le Sam Brandy ait été identifié le 14/09/2023 loin de sa zone d'opération. Bien que cela vous semble troublant, vous décidez de reconstituer les évènements grâces aux trames que vous avez récupérés :  
> $GPGSV,3,1,9,27,65,309,24,31,63,061,10,16,57,203,34,26,55,143,171E  
> $GPGSV,3,2,9,05,36,257,29,28,32,048,29,08,27,312,34,18,27,109,1940  
> $GPGSV,3,3,9,09,17,232,2876  
> Les coordonnées indiquées sont les suivantes :  
> 30°41'24.0''S 133°42'0.0''W  
> Vous devez retrouver à qu'elle heure il a été aperçu (GMT+00) ?  
> Format du Flag : DGHACK{OCEAN_HH_MM}  
> Fichier join : https://www.dghack.fr/uploads/event-dghack-2023/a-maritime-journey/diagram.png

La position donnée `30°41'24.0''S 133°42'0.0''W ` (ie au format décimal : `-30.69N / -133.7E`) est située au milieu de l'océan Pacifique : https://www.coordonnees-gps.fr/satellite/@-30.690000,-133.700000,2

La spécification des trames [GPGSV](https://gpsd.gitlab.io/gpsd/NMEA.html#_gsv_satellites_in_view) associée à l'[identification des satellites](https://gpsd.gitlab.io/gpsd/NMEA.html#_satellite_ids), permet de comprendre comment 9 satellites sont vus depuis la position donnée :

| ID Satellite | Elévation | Azimut |
| -  | -  | -   |
| 27 | 65 | 309 |
| 31 | 63 | 061 |
| 16 | 57 | 203 |
| 26 | 55 | 143 |
| 05 | 36 | 257 |
| 28 | 32 | 048 |
| 08 | 27 | 312 |
| 18 | 27 | 109 |
| 09 | 17 | 232 |

On peut se limiter à utiliser les informations des 4 premiers satellites pour déterminer l'horaire. Les 5 autres permettront de valider.

Le site suivant permet de suivre la position des satellites : https://in-the-sky.org/satmap_worldmap.php?gps=1

On peut ensuite se positionner à l'endroit indiqué, en spécifiant un Timezone à GMT+00, : https://in-the-sky.org/satmap_worldmap.php?latitude=-30.69&longitude=-133.7&timezone=%2B00%3A00, et en affichant uniquement les satellites GPS

Il suffit ensuite, pour la date du 14/9/2023, de faire défiler le temps jusqu'à ce que les satellites soient correctement positionnés. Ceci est le cas à 19h52.

Le 4ème flag est donc : `DGHACK{PACIFIQUE_19_52}`

----

### Flag 5 : Ephemeris Shift

> En discutant avec le Capitaine, vous en savez un peu plus sur le comportement étrange observé sur les systèmes de navigation. En effet, après avoir perdu le signal à plusieurs reprises pendant des périodes très courtes, son bateau a fini par ne plus du tout apparaître sur son système de cartographie. D'après ces dires, vous comprenez que le bateau a probablement été victime d'une cyberattaque de type GPS Jamming. Vous devez retrouver précisement quand l'attaque a eu lieu. On considère qu'un brouillage GPS dure plus d'une dizaine de seondes, sinon c'est une simple perte de signal.  
> Format du flag : DGHACK{JJMMAAAAhhmmss}  
> Fichier join : https://www.dghack.fr/uploads/event-dghack-2023/a-maritime-journey/GPS_NMEA_dump.txt

La [spécification](https://gpsd.gitlab.io/gpsd/NMEA.html#_error_status_indications) indique que 4 trames peuvent être utilisées pour identifier des erreurs : GPRMC, GPGLL, GPGGA et GPGSA.

Parmi celles-ci, seules les trames GPRMC, GPGLL et GPGGA son présentes dans le fichier joint [GPS_NMEA_dump.txt](./GPS_NMEA_dump.txt).

2 plages présentes des erreurs dans ces trames, dont la 1ère démarre vers 17:03:34.

Les trames GPRMC indiquent que les trames ont été produites le 12/09/2023.

Le 5ème flag est donc : `DGHACK{12092023170334}`
