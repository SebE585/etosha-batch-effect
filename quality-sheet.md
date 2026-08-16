# Data from: Study "African elephants in Etosha National Park (data from Tsalyuk et al. 2018)"

Fiche de qualite ICHNOS. Movebank Data Repository, item `f30fb6d4-803f-4b45-8313-716c3b21e087`.

## Ce que le jeu contient

| | |
|---|---|
| Capteur dominant | gps |
| Fixes | 2 930 268 |
| Individus | 15 |
| Duree couverte | 1978 jours |
| Cadence mediane | 10 s |
| Cadence dominante | 10 s |
| Regularite | 52 % des intervalles au pas dominant |
| 95e centile des trous | 20 min |

## Trois mesures de qualite

| Mesure | Valeur | Lecture |
|---|---|---|
| Pics de position | 0.000 % | rien de notable |
| Positions repetees | 2.17 % | repetitions frequentes |
| Grain des coordonnees | 8 decimales | precision preservee |

## Ce que ce jeu ne permet pas

- Toute comparaison de distance entre individus sans re-echantillonnage : seuls **52 %** des intervalles sont au pas dominant.

## Methode

Detecteur d'aller-retour, sans echelle ni espece : sur trois positions consecutives A, B, C, l'excursion vaut `(AB + BC - AC) / 2`. Elle est comparee au 95e centile du pas de **l'individu lui-meme**, ce qui evite tout seuil dependant de l'espece. Un fix est signale au-dela de dix fois cet etalon.

Validation : applique a 237 jeux publics, ce detecteur retrouve seul l'ecart de precision documente entre Argos et GPS (p = 3,4e-07), sans qu'aucune information sur le systeme de positionnement ne lui soit fournie.

Ce banc ne juge ni la science ni la collecte. Il mesure ce que le fichier publie porte, et ce qu'il ne porte pas.

Une mesure contestee est une mesure utile : si ce resultat vous parait faux, l'auteur veut le savoir.

---

*ICHNOS Field Clause, non-binding. This bench is free to use. If it was useful to you, and you work somewhere where things move, you are invited, and never required, to invite its author to come and see it.*