# TP 01 – Propagation dans les lignes électriques

Module Réseaux Électriques, ENP Alger (Prof. Karim SEBAA).

Simulation des régimes transitoires d'une ligne monophasée sans pertes de 100 mi
(L' = 1,5 mH/mi, C' = 0,02 µF/mi) fermée sur une charge R-L (400 Ω, 0,25 H), par le
modèle de Bergeron aux deux extrémités et le modèle compagnon de la règle des trapèzes
pour l'inductance. Cas traités : charge R-L (Q1), extrémité ouverte (Q2), court-circuit
(Q3), source continue (Q5), onde de choc de foudre (Q6).

## Contenu

```
TP01/                     version rendue
├── rapport/
│   ├── TP01_ligne_longue.m  script MATLAB (fichier remis)
│   ├── main.tex             préambule et \input des sections
│   ├── page_de_garde.tex
│   ├── sections/            1_objectif … 6_conclusion, valeurs.tex
│   ├── annexe_code.tex      listing du script
│   └── figures/             PNG écrits par le script, plus circuit.png
├── rapport_TP01.pdf         rapport compilé
└── rapport_overleaf.zip     dossier rapport/ prêt pour Overleaf

TP01_Propagation/            première version, plus complète (archive)
├── matlab/                  solveur, script principal, constructeur du modèle Simulink
├── python/                  version Python et comparaison MATLAB/Python
├── figures/, resultats/     figures et CSV de chaque cas
└── rapport/                 rapport Word et son générateur
```

## Utilisation

Lancer le script depuis le dossier `TP01_v2/rapport/` :

```matlab
cd TP01_v2/rapport
TP01_ligne_longue
```

Le script affiche les valeurs reprises dans le rapport et enregistre les figures dans
`figures/` (le dossier est créé s'il n'existe pas). Aucune boîte à outils n'est nécessaire.

Compiler le rapport :

```bash
cd TP01/rapport
pdflatex main.tex
pdflatex main.tex
```

Sur Overleaf, importer `rapport_overleaf.zip` et compiler `main.tex` avec pdfLaTeX.

## Modifier le rapport

- Toutes les valeurs numériques sont dans `sections/valeurs.tex`. Après une nouvelle
  exécution du script, mettre à jour ce seul fichier. Les valeurs calculées à la main
  et celles du livre y sont regroupées et commentées.
- Figures : `\fig{fichier}{légende}{largeur}` pour une figure, `\figdeux{f1}{légende 1}{f2}{légende 2}`
  pour deux figures côte à côte. Un exemple pour ajouter une photo est en commentaire
  dans `main.tex`.
- Les figures fournies ont été tracées sous GNU Octave ; les relancer sous MATLAB
  remplace les fichiers en gardant les mêmes noms.

BY ZANE MOHAMMED

