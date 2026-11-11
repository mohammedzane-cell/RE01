# -*- coding: utf-8 -*-
"""
Compare les CSV produits par TP01_ligne_longue.m (resultats/matlab) et par
tp01_ligne.py (resultats/python) : écart absolu maximal par signal et par cas.
"""

import csv
import os

import numpy as np

DOSSIER_TP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DM = os.path.join(DOSSIER_TP, "resultats", "matlab")
DP = os.path.join(DOSSIER_TP, "resultats", "python")


def lire(chemin):
    with open(chemin) as fh:
        entete = fh.readline().strip().split(",")
    return entete, np.loadtxt(chemin, delimiter=",", skiprows=1, ndmin=2)


def lire_indicateurs(chemin):
    with open(chemin) as fh:
        lignes = list(csv.reader(fh))[1:]
    return {k: float(v) for k, v in lignes}


def main():
    communs = sorted(set(os.listdir(DM)) & set(os.listdir(DP)))
    communs = [c for c in communs if c.endswith(".csv") and c not in ("indicateurs.csv",
                                                                     "validation_livre.csv")]
    sortie = [("cas", "signal", "ecart_abs_max", "valeur_abs_max", "ecart_relatif")]
    pire = 0.0
    print("%-28s %-12s %14s %14s %12s" % ("cas", "signal", "écart max", "|x| max", "relatif"))
    for nom in communs:
        hm, Xm = lire(os.path.join(DM, nom))
        hp, Xp = lire(os.path.join(DP, nom))
        if hm != hp or Xm.shape != Xp.shape:
            print("%s : formats différents (%s / %s)" % (nom, Xm.shape, Xp.shape))
            continue
        for k, sig in enumerate(hm):
            e = float(np.max(np.abs(Xm[:, k] - Xp[:, k])))
            a = float(np.max(np.abs(Xp[:, k])))
            rel = e / a if a > 0 else 0.0
            pire = max(pire, rel)
            sortie.append((nom[:-4], sig, "%.6g" % e, "%.6g" % a, "%.3g" % rel))
            print("%-28s %-12s %14.4g %14.4g %12.3g" % (nom[:-4], sig, e, a, rel))
    print("Plus grand écart relatif sur l'ensemble des signaux : %.3g" % pire)

    Im = lire_indicateurs(os.path.join(DM, "indicateurs.csv"))
    Ip = lire_indicateurs(os.path.join(DP, "indicateurs.csv"))
    manquants = sorted(set(Im) ^ set(Ip))
    pire_ind = 0.0
    cle_pire = ""
    for k in sorted(set(Im) & set(Ip)):
        d = abs(Im[k] - Ip[k]) / max(abs(Ip[k]), 1e-12)
        if d > pire_ind:
            pire_ind, cle_pire = d, k
    print("Indicateurs communs : %d ; plus grand écart relatif %.3g (%s)"
          % (len(set(Im) & set(Ip)), pire_ind, cle_pire))
    if manquants:
        print("Indicateurs présents d'un seul côté :", ", ".join(manquants))

    with open(os.path.join(DOSSIER_TP, "resultats", "comparaison_matlab_python.csv"), "w",
              newline="") as fh:
        csv.writer(fh).writerows(sortie)


if __name__ == "__main__":
    main()
