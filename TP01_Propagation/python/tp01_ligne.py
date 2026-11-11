# -*- coding: utf-8 -*-
"""
TP 01 - Propagation dans les lignes électriques
Module : Réseaux Électriques (ENP Alger)
Version Python du script MATLAB TP01_ligne_longue.m (mêmes fonctions, mêmes noms).

Ligne monophasée sans pertes : modèle de Bergeron aux deux extrémités,
charge R-L traitée par la règle des trapèzes (modèle compagnon).
"""

import csv
import math
import os
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

DOSSIER_TP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOSSIER_FIG = os.path.join(DOSSIER_TP, "figures")
DOSSIER_RES = os.path.join(DOSSIER_TP, "resultats", "python")

f = 60.0
w = 2 * math.pi * f
Vm = 230000 * math.sqrt(2) / math.sqrt(3)  # amplitude de la tension simple


def parametres_base():
    """Données de l'énoncé : ligne de 100 mi, charge R-L, pas de 0,1 ms."""
    return {
        "Lp": 1.5e-3,          # H/mi
        "Cp": 0.02e-6,         # F/mi
        "d": 100.0,            # mi
        "R": 400.0,            # ohm
        "L": 0.25,             # H
        "dt": 1e-4,            # s
        "T": 5.0,              # s
        "t_ferm": 1e-4,        # fermeture de l'interrupteur
        "source": source_ac,
        "mode_retard": "interpolation",   # ou 'arrondi'
        "tau_impose": float("nan"),       # NaN : tau calculé à partir de L' et C'
        "couper_historique": True,        # False : interpolation à travers la fermeture (erreur)
    }


def source_ac(t):
    return Vm * np.cos(w * t)


def source_dc(t):
    return 230000.0 * np.ones_like(t)


def simuler_ligne(p):
    """Ligne sans pertes (Bergeron) + charge R-L (trapèzes), pas de temps fixe."""
    Zc = math.sqrt(p["Lp"] / p["Cp"])
    vp = 1 / math.sqrt(p["Lp"] * p["Cp"])
    tau = p["d"] / vp
    if not math.isnan(p["tau_impose"]):
        tau = p["tau_impose"]
    dt = p["dt"]
    R = p["R"]
    L = p["L"]

    # Option « arrondi » : le retard est ramené au multiple de dt le plus proche.
    k_tau = int(round(tau / dt))
    if p["mode_retard"] == "arrondi":
        tau_eff = k_tau * dt
    else:
        tau_eff = tau
    if tau_eff < dt:
        raise ValueError("Le temps de propagation doit dépasser le pas de calcul.")

    # Modèle compagnon de l'inductance : Req en parallèle avec la source Ih.
    if L > 0:
        Req = 2 * L / dt
    else:
        Req = 0.0

    N = int(round(p["T"] / dt))
    t = np.arange(N + 1) * dt
    vs = p["source"](t)
    v1 = np.zeros(N + 1)
    i1 = np.zeros(N + 1)
    v2 = np.zeros(N + 1)
    i2 = np.zeros(N + 1)
    vL = np.zeros(N + 1)
    eps_t = 1e-9 * dt
    t_lim = p["t_ferm"] if p["couper_historique"] else 0.0

    for n in range(1, N + 1):
        # Grandeurs vues à l'autre extrémité un temps de propagation plus tôt.
        ts = t[n] - tau_eff
        if ts < t_lim - eps_t:
            # Avant la fermeture la ligne est au repos : pas d'interpolation
            # à travers l'instant de manoeuvre.
            v1h = i1h = v2h = i2h = 0.0
        elif p["mode_retard"] == "arrondi":
            j = n - k_tau
            v1h, i1h, v2h, i2h = v1[j], i1[j], v2[j], i2[j]
        else:
            s = ts / dt
            j = int(math.floor(s))
            a = s - j
            if a > 1 - 1e-9:
                j, a = j + 1, 0.0
            v1h = v1[j] + a * (v1[j + 1] - v1[j])
            i1h = i1[j] + a * (i1[j + 1] - i1[j])
            v2h = v2[j] + a * (v2[j + 1] - v2[j])
            i2h = i2[j] + a * (i2[j + 1] - i2[j])

        # Sources d'historique du modèle de Bergeron.
        Ik = i2h - v2h / Zc     # onde réfléchie revenant vers k
        Im = v1h / Zc + i1h     # onde incidente arrivant en m

        # Extrémité k : tension imposée par la source une fois l'interrupteur fermé.
        if t[n] >= p["t_ferm"] - eps_t:
            v1[n] = vs[n]
            i1[n] = v1[n] / Zc + Ik
        else:
            i1[n] = 0.0
            v1[n] = -Zc * Ik

        # Extrémité m : Zc // Im en série avec R et le compagnon Req // Ih.
        if L > 0:
            Ih = i2[n - 1] + vL[n - 1] / Req
        else:
            Ih = 0.0
        i2[n] = (Im + Req * Ih / Zc) / (1 + (R + Req) / Zc)
        v2[n] = Zc * (Im - i2[n])
        vL[n] = v2[n] - R * i2[n]

    return {"t": t, "vs": vs, "v1": v1, "i1": i1, "v2": v2, "i2": i2, "vL": vL,
            "Zc": Zc, "vp": vp, "tau": tau, "tau_eff": tau_eff, "Req": Req}


def onde_foudre(t, Vmax, tau1, tau2, n, eta=1.0):
    """Onde de choc vs = eta.Vmax.(t/tau1)^n/(1+(t/tau1)^n).exp(-t/tau2), nulle pour t<0."""
    t = np.asarray(t, dtype=float)
    x = np.where(t > 0, t / tau1, 0.0) ** n
    return eta * Vmax * x / (1 + x) * np.exp(-np.maximum(t, 0) / tau2)


def mesurer_onde_choc(t, v):
    """Valeur de crête, durée de front (30-90 % x 1,67) et durée jusqu'à mi-valeur."""
    t = np.asarray(t)
    v = np.asarray(v)
    ic = int(np.argmax(v))
    Vc = v[ic]
    tc = t[ic]

    def franchissement_montant(niv):
        k = int(np.argmax(v[: ic + 1] >= niv * Vc))
        return t[k - 1] + (niv * Vc - v[k - 1]) * (t[k] - t[k - 1]) / (v[k] - v[k - 1])

    t30 = franchissement_montant(0.3)
    t90 = franchissement_montant(0.9)
    T1 = 1.67 * (t90 - t30)
    O1 = t30 - 0.3 * T1            # origine conventionnelle
    k = ic + int(np.argmax(v[ic:] <= 0.5 * Vc))
    t50 = t[k - 1] + (0.5 * Vc - v[k - 1]) * (t[k] - t[k - 1]) / (v[k] - v[k - 1])
    T2 = t50 - O1
    return {"Vc": Vc, "tc": tc, "t30": t30, "t90": t90, "T1": T1, "O1": O1,
            "t50": t50, "T2": T2}


def coefficient_reflexion(ZL, Zc):
    return (ZL - Zc) / (ZL + Zc)


def phaseurs_regime_permanent(p):
    """Ligne en quadripôle ABCD (sans pertes) fermée sur Z = R + jwL."""
    Zc = math.sqrt(p["Lp"] / p["Cp"])
    bd = w * p["d"] * math.sqrt(p["Lp"] * p["Cp"])
    A = math.cos(bd)
    B = 1j * Zc * math.sin(bd)
    C = 1j * math.sin(bd) / Zc
    D = A
    ZL = p["R"] + 1j * w * p["L"]
    V1 = Vm + 0j
    I2 = V1 / (A * ZL + B)
    V2 = ZL * I2
    I1 = C * V2 + D * I2
    return {"V1": V1, "I1": I1, "V2": V2, "I2": I2}


def ajuster_sinus(t, x):
    """Moindres carrés x = a.cos(wt) + b.sin(wt) + c ; renvoie le phaseur a - jb."""
    M = np.column_stack([np.cos(w * t), np.sin(w * t), np.ones_like(t)])
    coef = np.linalg.lstsq(M, x, rcond=None)[0]
    return coef[0] - 1j * coef[1]


def residu_regime_permanent(res, p, t_debut=4.0):
    """Plus grand écart entre la simulation et la solution par phaseurs pour t >= t_debut."""
    ph = phaseurs_regime_permanent(p)
    t = res["t"]
    s = t >= t_debut
    v2p = abs(ph["V2"]) * np.cos(w * t[s] + np.angle(ph["V2"]))
    i1p = abs(ph["I1"]) * np.cos(w * t[s] + np.angle(ph["I1"]))
    return float(np.max(np.abs(res["v2"][s] - v2p))), float(np.max(np.abs(res["i1"][s] - i1p)))


def indicateurs(res, amplitude_source, seuil=1e-6):
    """Arrivée de l'onde en m, crête de |v2| et rapport à l'amplitude de la source."""
    t, v2 = res["t"], res["v2"]
    # L'onde est détectée en m dès que v2 ou Zc.i2 sort du bruit numérique.
    k = np.flatnonzero((np.abs(v2) > seuil * amplitude_source)
                       | (res["Zc"] * np.abs(res["i2"]) > seuil * amplitude_source))
    t_arr = t[k[0]] if k.size else float("nan")
    crete = float(np.max(np.abs(v2)))
    return {"t_arrivee": t_arr, "crete_v2": crete,
            "rapport_v2": crete / amplitude_source,
            "crete_i1": float(np.max(np.abs(res["i1"]))),
            "crete_i2": float(np.max(np.abs(res["i2"])))}


def ecrire_csv(nom, res):
    os.makedirs(DOSSIER_RES, exist_ok=True)
    chemin = os.path.join(DOSSIER_RES, nom + ".csv")
    M = np.column_stack([res["t"], res["vs"], res["v1"], res["i1"], res["v2"], res["i2"]])
    np.savetxt(chemin, M, delimiter=",", fmt="%.10g",
               header="t_s,vs_V,v1_V,i1_A,v2_V,i2_A", comments="")


def ecrire_indicateurs(lignes):
    os.makedirs(DOSSIER_RES, exist_ok=True)
    with open(os.path.join(DOSSIER_RES, "indicateurs.csv"), "w", newline="") as fh:
        fh.write("grandeur,valeur\n")
        for cle, val in lignes:
            fh.write("%s,%.10g\n" % (cle, val))


def sauver_figure(fig, nom):
    os.makedirs(DOSSIER_FIG, exist_ok=True)
    fig.savefig(os.path.join(DOSSIER_FIG, nom + ".png"), dpi=300)
    fig.savefig(os.path.join(DOSSIER_FIG, nom + ".pdf"))
    plt.close(fig)


def tracer_cas(liste_res, legendes, titre, nom, t_max=None, unite_t="ms"):
    """Figure 2x2 : i1, i2 (A) et v1, v2 (kV) en fonction du temps."""
    ech = 1e3 if unite_t == "ms" else 1e6
    lab_t = "t (ms)" if unite_t == "ms" else "t (µs)"
    fig, ax = plt.subplots(2, 2, figsize=(10, 7))
    signaux = [("i1", "i_1(t) (A)", 1, "Courant au départ i_1"),
               ("i2", "i_2(t) (A)", 1, "Courant à l'arrivée i_2"),
               ("v1", "v_1(t) (kV)", 1e-3, "Tension au départ v_1"),
               ("v2", "v_2(t) (kV)", 1e-3, "Tension à l'arrivée v_2")]
    for k, (cle, ylab, g, tit) in enumerate(signaux):
        a = ax[k // 2][k % 2]
        for res, lg in zip(liste_res, legendes):
            t = res["t"]
            sel = slice(None) if t_max is None else (t <= t_max + 1e-12)
            a.plot(t[sel] * ech, res[cle][sel] * g, label=lg, linewidth=0.8)
        t_fin = res["t"][-1] if t_max is None else min(t_max, res["t"][-1])
        a.set_xlim(0, t_fin * ech)
        a.set_xlabel(lab_t)
        a.set_ylabel(ylab)
        a.set_title(tit)
        a.grid(True)
        if len(liste_res) > 1:
            a.legend(fontsize=8)
    fig.suptitle(titre)
    fig.tight_layout()
    sauver_figure(fig, nom)


def enveloppe_ecart(res, p, fenetre=0.02):
    """Maximum de |v2 - v2 phaseur| sur des fenêtres successives de durée fenetre."""
    ph = phaseurs_regime_permanent(p)
    e = np.abs(res["v2"] - abs(ph["V2"]) * np.cos(w * res["t"] + np.angle(ph["V2"])))
    m = int(round(fenetre / p["dt"]))
    nb = (len(e) - 1) // m
    env = np.array([np.max(e[1 + k * m: 1 + (k + 1) * m]) for k in range(nb)])
    tc = (np.arange(nb) + 0.5) * m * p["dt"]
    return tc, env


def tracer_amortissement(cas, legendes, nom):
    """Enveloppe de l'écart au régime permanent (échelle log) pour chaque cas."""
    fig, ax = plt.subplots(1, len(cas), figsize=(11, 4.2))
    for a, (titre, liste) in zip(ax, cas):
        for (res, p), lg in zip(liste, legendes):
            tc, env = enveloppe_ecart(res, p)
            a.semilogy(tc, env / 1e3, label=lg)
        a.set_xlim(0, liste[0][0]["t"][-1])
        a.set_xlabel("t (s)")
        a.set_ylabel("max |v_2 - v_2,phaseur| sur 20 ms (kV)")
        a.set_title(titre)
        a.grid(True, which="both")
        a.legend(fontsize=8)
    fig.tight_layout()
    sauver_figure(fig, nom)


def tableau_validation(res, instants):
    lignes = []
    for tv in instants:
        n = int(round(tv / res["t"][1]))
        lignes.append((res["t"][n], res["i1"][n], res["v1"][n], res["i2"][n], res["v2"][n]))
    return lignes


def afficher_tableau(titre, lignes):
    print(titre)
    print("   t (s)      i1 (A)        v1 (V)      i2 (A)        v2 (V)")
    for l in lignes:
        print("%8.4f %11.2f %13.0f %11.2f %13.0f" % l)


def main():
    os.makedirs(DOSSIER_RES, exist_ok=True)
    ind = []
    p0 = parametres_base()

    # Contrôle par rapport au livre (tau = 0,00055 s comme dans la solution).
    pv = dict(p0, T=1e-3, tau_impose=0.00055)
    rv = simuler_ligne(pv)
    instants = [k * 1e-4 for k in range(1, 11)]
    tab_livre = tableau_validation(rv, instants)
    afficher_tableau("Validation, tau = 0.00055 s (livre)", tab_livre)
    pe = dict(p0, T=1e-3)
    re_ = simuler_ligne(pe)
    tab_exact = tableau_validation(re_, instants)
    afficher_tableau("Validation, tau exact = %.4e s" % re_["tau"], tab_exact)
    with open(os.path.join(DOSSIER_RES, "validation_livre.csv"), "w") as fh:
        fh.write("tau,t_s,i1_A,v1_V,i2_A,v2_V\n")
        for tag, tab in (("0.00055", tab_livre), ("exact", tab_exact)):
            for l in tab:
                fh.write("%s,%.4f,%.6g,%.8g,%.6g,%.8g\n" % ((tag,) + l))

    rp = simuler_ligne(dict(pv, couper_historique=False))
    tab_piege = tableau_validation(rp, [6e-4, 7e-4])
    afficher_tableau("Sans coupure de l'historique à la fermeture (tau = 0.00055 s)", tab_piege)
    ind += [("piege_i2_0p0006", tab_piege[0][3]), ("piege_i2_0p0007", tab_piege[1][3]),
            ("piege_v2_0p0007", tab_piege[1][4])]
    for l in tab_livre:
        ind += [("val_livre_t%.4f_i1" % l[0], l[1]), ("val_livre_t%.4f_v1" % l[0], l[2]),
                ("val_livre_t%.4f_i2" % l[0], l[3]), ("val_livre_t%.4f_v2" % l[0], l[4])]

    Zc, tau, vp = re_["Zc"], re_["tau"], re_["vp"]
    ind += [("Zc_ohm", Zc), ("vp_mi_s", vp), ("tau_s", tau), ("tau_sur_dt", tau / p0["dt"]),
            ("Req_ohm", re_["Req"])]
    print("Zc = %.4f ohm, vp = %.1f mi/s, tau = %.4e s, tau/dt = %.4f, Req = %.1f ohm"
          % (Zc, vp, tau, tau / p0["dt"], re_["Req"]))

    # Coefficients de réflexion pour les charges résistives étudiées.
    for R in (400.0, 999.0, 1e6, 0.001):
        G = coefficient_reflexion(R, Zc)
        ind.append(("Gamma_R_%g" % R, G))
        print("Gamma(R = %g ohm) = %.6f" % (R, G))
    G_front = coefficient_reflexion(400.0 + re_["Req"], Zc)
    ind.append(("Gamma_front_RL_discret", G_front))
    print("Gamma vu par le front d'onde (R + Req = %.0f ohm) = %.4f" % (400 + re_["Req"], G_front))

    charges = {
        "RL": (400.0, 0.25),
        "ouvert999": (999.0, 0.001),
        "ouvert1e6": (1e6, 0.001),
        "cc": (0.001, 0.001),
        "ccR": (0.001, 0.0),
    }

    resultats = {}
    for src_nom, src, amp in (("AC", source_ac, Vm), ("DC", source_dc, 230000.0)):
        for ch in ("RL", "ouvert999", "ouvert1e6", "cc"):
            R, L = charges[ch]
            p = dict(p0, R=R, L=L, source=src)
            r = simuler_ligne(p)
            resultats[(src_nom, ch)] = r
            q = indicateurs(r, amp)
            for cle, val in q.items():
                ind.append(("%s_%s_%s" % (src_nom, ch, cle), val))
            print("%s %-9s : arrivée en m à t = %.4f ms (t - t_ferm = %.4f ms), "
                  "|v2|max = %.1f kV, rapport = %.3f, |i1|max = %.0f A, |i2|max = %.0f A"
                  % (src_nom, ch, q["t_arrivee"] * 1e3, (q["t_arrivee"] - p0["t_ferm"]) * 1e3,
                     q["crete_v2"] / 1e3, q["rapport_v2"], q["crete_i1"], q["crete_i2"]))

    nomcsv = {"RL": "RL", "ouvert999": "ouvert_999", "ouvert1e6": "ouvert_1e6", "cc": "cc",
              "ccR": "cc_R"}
    prefixe = {("AC", "RL"): "Q1", ("AC", "ouvert999"): "Q2", ("AC", "ouvert1e6"): "Q2",
               ("AC", "cc"): "Q3"}
    for (s, ch), r in resultats.items():
        nom = (prefixe[(s, ch)] if s == "AC" else "Q5_DC") + "_" + nomcsv[ch]
        ecrire_csv(nom, r)

    # Régime permanent Q1 : comparaison avec le calcul par phaseurs.
    r = resultats[("AC", "RL")]
    ph = phaseurs_regime_permanent(p0)
    sel = r["t"] >= 4.0
    I1s = ajuster_sinus(r["t"][sel], r["i1"][sel])
    I2s = ajuster_sinus(r["t"][sel], r["i2"][sel])
    V2s = ajuster_sinus(r["t"][sel], r["v2"][sel])
    for nomg, Xs, Xp in (("I1", I1s, ph["I1"]), ("I2", I2s, ph["I2"]), ("V2", V2s, ph["V2"])):
        ecart = abs(abs(Xs) - abs(Xp)) / abs(Xp) * 100
        dphi = (np.angle(Xs, deg=True) - np.angle(Xp, deg=True))
        ind += [("Q1_%s_sim_amp" % nomg, abs(Xs)), ("Q1_%s_phaseur_amp" % nomg, abs(Xp)),
                ("Q1_%s_sim_phase_deg" % nomg, np.angle(Xs, deg=True)),
                ("Q1_%s_phaseur_phase_deg" % nomg, np.angle(Xp, deg=True)),
                ("Q1_%s_ecart_pct" % nomg, ecart)]
        print("Q1 régime permanent %s : simulation %.2f /%.3f deg, phaseur %.2f /%.3f deg, "
              "écart %.3f %%, déphasage %.4f deg"
              % (nomg, abs(Xs), np.angle(Xs, deg=True), abs(Xp), np.angle(Xp, deg=True),
                 ecart, dphi))
    i2_ref = abs(ph["I2"]) * np.cos(w * r["t"] + np.angle(ph["I2"]))
    err = np.abs(r["i2"] - i2_ref)
    k = np.flatnonzero(err > 0.01 * abs(ph["I2"]))
    t_trans = r["t"][k[-1]] if k.size else 0.0
    ind.append(("Q1_duree_transitoire_1pct_s", t_trans))
    print("Q1 : |i2 - i2_phaseur| < 1 %% de |I2| après t = %.4f s" % t_trans)

    # Interpolation contre arrondi du retard (20 premières ms).
    pa = dict(p0, T=0.02, mode_retard="arrondi")
    pi = dict(p0, T=0.02)
    ra = simuler_ligne(pa)
    ri = simuler_ligne(pi)
    dv2 = float(np.max(np.abs(ra["v2"] - ri["v2"])))
    di2 = float(np.max(np.abs(ra["i2"] - ri["i2"])))
    ind += [("arrondi_tau_eff_s", ra["tau_eff"]), ("arrondi_max_dv2_V", dv2),
            ("arrondi_max_di2_A", di2)]
    print("Arrondi : tau_eff = %.4e s ; max|dv2| = %.1f V (%.2f %% de Vm), max|di2| = %.2f A"
          % (ra["tau_eff"], dv2, dv2 / Vm * 100, di2))
    ecrire_csv("Q1_RL_arrondi_20ms", ra)
    ecrire_csv("Q1_RL_interp_20ms", ri)

    # Amortissement des cas extrêmes : enveloppe de v2 sur la dernière seconde.
    for ch in ("ouvert999", "ouvert1e6", "cc"):
        rr = resultats[("AC", ch)]
        dern = rr["t"] >= 4.0
        prem = (rr["t"] >= 0.0) & (rr["t"] <= 0.05)
        ind += [("AC_%s_v2max_0_50ms" % ch, float(np.max(np.abs(rr["v2"][prem])))),
                ("AC_%s_v2max_4_5s" % ch, float(np.max(np.abs(rr["v2"][dern])))),
                ("AC_%s_i2max_4_5s" % ch, float(np.max(np.abs(rr["i2"][dern])))),
                ("AC_%s_i1max_4_5s" % ch, float(np.max(np.abs(rr["i1"][dern]))))]
        print("AC %-9s : |v2|max sur 0-50 ms = %.1f kV, sur 4-5 s = %.1f kV ; "
              "|i1|max 4-5 s = %.0f A, |i2|max 4-5 s = %.0f A"
              % (ch, ind[-4][1] / 1e3, ind[-3][1] / 1e3, ind[-1][1], ind[-2][1]))
    # Part physique et part numérique de l'amortissement : écart au régime permanent
    # sur 4-5 s, avec dt = 1e-4 s (retard interpolé) et avec dt = tau/5 (retard exact).
    dt_N = tau / 5
    res_N = {}
    for ch in ("ouvert999", "ouvert1e6", "cc"):
        R, L = charges[ch]
        G = coefficient_reflexion(R, Zc)
        t_amort = 2 * tau / (-math.log(abs(G)))
        ind.append(("AC_%s_constante_amortissement_Gamma_s" % ch, t_amort))
        for lab, pp in (("dt1e-4", dict(p0, R=R, L=L)), ("dtTauSur5", dict(p0, R=R, L=L, dt=dt_N))):
            rr = resultats[("AC", ch)] if lab == "dt1e-4" else simuler_ligne(pp)
            if lab == "dtTauSur5":
                res_N[ch] = rr
            rv2, ri1 = residu_regime_permanent(rr, pp)
            ind += [("AC_%s_%s_residu_v2_4_5s" % (ch, lab), rv2),
                    ("AC_%s_%s_residu_i1_4_5s" % (ch, lab), ri1)]
            print("AC %-9s %-9s : écart au régime permanent sur 4-5 s, v2 : %.0f V, i1 : %.1f A "
                  "(constante d'amortissement 2tau/(-ln|Gamma|) = %.4g s)"
                  % (ch, lab, rv2, ri1, t_amort))
    ind.append(("dt_tau_sur_5_s", dt_N))
    # Constante de temps mesurée sur l'enveloppe (pente en échelle log).
    for lab, rr, pp, t_a, t_b in (
            ("dt1e-4", resultats[("AC", "ouvert1e6")], dict(p0, R=1e6, L=0.001), 0.02, 0.4),
            ("dtTauSur5", res_N["ouvert1e6"], dict(p0, R=1e6, L=0.001, dt=dt_N), 0.5, 4.5)):
        tc, env = enveloppe_ecart(rr, pp)
        sel = (tc > t_a) & (tc < t_b)
        pente = np.polyfit(tc[sel], np.log(env[sel]), 1)[0]
        ind.append(("AC_ouvert1e6_%s_constante_mesuree_s" % lab, -1 / pente))
        print("AC ouvert1e6 %-9s : constante de temps de l'enveloppe mesurée = %.4g s"
              % (lab, -1 / pente))
    rr = resultats[("AC", "cc")]
    ind.append(("AC_cc_moyenne_i1_4_5s", float(np.mean(rr["i1"][rr["t"] >= 4.0]))))
    n_arr = int(np.flatnonzero(np.abs(rr["v2"]) > 1e-6 * Vm)[0])
    ind += [("AC_cc_v2_n_arr", rr["v2"][n_arr]), ("AC_cc_v2_n_arr_plus1", rr["v2"][n_arr + 1]),
            ("AC_cc_v2_n_arr_plus2", rr["v2"][n_arr + 2]),
            ("Gamma_front_cc_discret", coefficient_reflexion(0.001 + 2 * 0.001 / p0["dt"], Zc))]
    print("AC cc : v2 aux trois premiers pas après l'arrivée : %.0f, %.0f, %.0f V ; "
          "moyenne de i1 sur 4-5 s = %.1f A" % (ind[-4][1], ind[-3][1], ind[-2][1], ind[-5][1]))

    for ch in ("RL", "ouvert999", "cc"):
        rr = resultats[("DC", ch)]
        ind += [("DC_%s_v2_final" % ch, rr["v2"][-1]), ("DC_%s_i2_final" % ch, rr["i2"][-1]),
                ("DC_%s_i1_final" % ch, rr["i1"][-1])]
        print("DC %-9s : à t = 5 s, v2 = %.1f kV, i2 = %.1f A, i1 = %.1f A"
              % (ch, rr["v2"][-1] / 1e3, rr["i2"][-1], rr["i1"][-1]))

    # Onde de choc de foudre.
    Vmax, tau1, tau2, nf = 230000.0, 1.2e-6, 50e-6, 3
    tf = np.arange(0, 250e-6 + 1e-12, 1e-9)
    v_brut = onde_foudre(tf, Vmax, tau1, tau2, nf)
    mb = mesurer_onde_choc(tf, v_brut)
    eta = Vmax / mb["Vc"]
    v_corr = onde_foudre(tf, Vmax, tau1, tau2, nf, eta)
    mc = mesurer_onde_choc(tf, v_corr)
    ind += [("foudre_crete_brute_V", mb["Vc"]), ("foudre_t_crete_s", mb["tc"]),
            ("foudre_eta", eta), ("foudre_T1_s", mb["T1"]), ("foudre_T2_s", mb["T2"]),
            ("foudre_t30_s", mb["t30"]), ("foudre_t90_s", mb["t90"]), ("foudre_O1_s", mb["O1"]),
            ("foudre_t50_s", mb["t50"]), ("foudre_crete_corrigee_V", mc["Vc"])]
    print("Foudre : crête brute %.1f kV à t = %.3f us, eta = %.5f ; T1 = %.3f us, "
          "T2 = %.2f us (origine O1 = %.3f us, t50 = %.2f us)"
          % (mb["Vc"] / 1e3, mb["tc"] * 1e6, eta, mb["T1"] * 1e6, mb["T2"] * 1e6,
             mb["O1"] * 1e6, mb["t50"] * 1e6))

    fig, a = plt.subplots(figsize=(8, 4.5))
    a.plot(tf * 1e6, v_brut / 1e3, label="formule brute (η = 1)")
    a.plot(tf * 1e6, v_corr / 1e3, label="corrigée (η = %.4f)" % eta)
    a.axhline(Vmax / 1e3, color="k", linestyle=":", linewidth=0.8)
    a.set_xlabel("t (µs)")
    a.set_ylabel("v_s(t) (kV)")
    a.set_title("Onde de choc de foudre 1,2/50 µs, n = 3")
    a.grid(True)
    a.legend()
    fig.tight_layout()
    sauver_figure(fig, "Q6a_onde_foudre")
    np.savetxt(os.path.join(DOSSIER_RES, "Q6a_onde_foudre.csv"),
               np.column_stack([tf[::10], v_brut[::10], v_corr[::10]]), delimiter=",",
               fmt="%.10g", header="t_s,v_brut_V,v_corrige_V", comments="")

    src_f = lambda t: onde_foudre(t, Vmax, tau1, tau2, nf, eta)
    pf = dict(p0, dt=60e-9, T=250e-6, t_ferm=0.0, source=src_f)
    res_f = {}
    for ch in ("RL", "ouvert999", "cc"):
        R, L = charges[ch]
        res_f[ch] = simuler_ligne(dict(pf, R=R, L=L))
    r = res_f["RL"]
    ecart_i1 = float(np.max(np.abs(r["i1"] - r["vs"] / r["Zc"])))
    dmax_ch = max(float(np.max(np.abs(res_f[c]["i1"] - r["i1"]))) for c in res_f)
    ind += [("Q6_100mi_max_abs_v2", float(np.max(np.abs(r["v2"])))),
            ("Q6_100mi_max_abs_i2", float(np.max(np.abs(r["i2"])))),
            ("Q6_100mi_max_ecart_i1_vs_sur_Zc", ecart_i1),
            ("Q6_100mi_max_i1", float(np.max(r["i1"]))),
            ("Q6_100mi_ecart_entre_charges_i1", dmax_ch),
            ("Q6_100mi_nb_pas", len(r["t"]) - 1)]
    print("Foudre, 100 mi : max|v2| = %g V, max|i2| = %g A, max|i1 - vs/Zc| = %.3g A, "
          "i1 max = %.1f A, écart entre charges %.3g A, %d pas"
          % (ind[-6][1], ind[-5][1], ecart_i1, ind[-3][1], dmax_ch, len(r["t"]) - 1))
    ecrire_csv("Q6_foudre_100mi_RL", r)
    tracer_cas([r], ["charge R-L"], "Choc de foudre, ligne de 100 mi (τ = %.1f µs > 250 µs)"
               % (r["tau"] * 1e6), "Q6b_foudre_100mi", unite_t="us")

    # Extension : ligne de 10 mi, les réflexions apparaissent dans la fenêtre de 250 us.
    pf10 = dict(pf, d=10.0)
    res_10 = {}
    for ch in ("RL", "ouvert999", "cc", "ccR"):
        R, L = charges[ch]
        res_10[ch] = simuler_ligne(dict(pf10, R=R, L=L))
        q = indicateurs(res_10[ch], Vmax)
        ind += [("Q6_10mi_%s_t_arrivee" % ch, q["t_arrivee"]),
                ("Q6_10mi_%s_crete_v2" % ch, q["crete_v2"]),
                ("Q6_10mi_%s_rapport_v2" % ch, q["rapport_v2"]),
                ("Q6_10mi_%s_crete_i2" % ch, q["crete_i2"]),
                ("Q6_10mi_%s_crete_i1" % ch, q["crete_i1"])]
        print("Foudre, 10 mi, %-9s : arrivée %.3f us (tau = %.3f us), |v2|max = %.1f kV "
              "(rapport %.3f), |i2|max = %.0f A, |i1|max = %.0f A"
              % (ch, q["t_arrivee"] * 1e6, res_10[ch]["tau"] * 1e6, q["crete_v2"] / 1e3,
                 q["rapport_v2"], q["crete_i2"], q["crete_i1"]))
        ecrire_csv("Q6_foudre_10mi_" + nomcsv[ch], res_10[ch])
    ind.append(("Q6_10mi_tau_s", res_10["RL"]["tau"]))
    tracer_cas([res_10["RL"], res_10["ouvert999"], res_10["cc"], res_10["ccR"]],
               ["R-L", "R = 999 Ω", "R = L = 0,001", "R = 0,001, L = 0"],
               "Choc de foudre, ligne de 10 mi (τ = %.2f µs)" % (res_10["RL"]["tau"] * 1e6),
               "Q6c_foudre_10mi", unite_t="us")

    # Figures des cas sinusoïdaux et continus.
    R_ = resultats
    tracer_cas([R_[("AC", "RL")]], ["R-L"], "Q1 : charge R-L, source alternative, 0-5 s",
               "Q1_RL_5s")
    tracer_cas([R_[("AC", "RL")]], ["R-L"], "Q1 : charge R-L, 10 premières ms", "Q1_RL_zoom",
               t_max=0.01)
    tracer_cas([ra, ri], ["τ arrondi à 5Δt", "τ interpolé"],
               "Q1 : arrondi et interpolation du retard, 10 premières ms", "Q1_RL_arrondi_interp",
               t_max=0.01)
    tracer_cas([R_[("AC", "ouvert999")], R_[("AC", "ouvert1e6")]], ["R = 999 Ω", "R = 10⁶ Ω"],
               "Q2 : extrémité ouverte, 0-5 s", "Q2_ouvert_5s")
    tracer_cas([R_[("AC", "ouvert999")], R_[("AC", "ouvert1e6")]], ["R = 999 Ω", "R = 10⁶ Ω"],
               "Q2 : extrémité ouverte, 20 premières ms", "Q2_ouvert_zoom", t_max=0.02)
    tracer_cas([R_[("AC", "cc")]], ["R = L = 0,001"], "Q3 : extrémité en court-circuit, 0-5 s",
               "Q3_cc_5s")
    tracer_cas([R_[("AC", "cc")]], ["R = L = 0,001"], "Q3 : court-circuit, 20 premières ms",
               "Q3_cc_zoom", t_max=0.02)
    tracer_cas([R_[("DC", "RL")], R_[("DC", "ouvert999")]], ["R-L", "R = 999 Ω"],
               "Q5 : source continue 230 kV, 0-5 s", "Q5_DC_RL_ouvert_5s")
    tracer_cas([R_[("DC", "RL")], R_[("DC", "ouvert999")], R_[("DC", "cc")]],
               ["R-L", "R = 999 Ω", "court-circuit"],
               "Q5 : source continue 230 kV, 10 premières ms", "Q5_DC_zoom", t_max=0.01)
    tracer_cas([R_[("DC", "cc")]], ["R = L = 0,001"], "Q5 : source continue, court-circuit, 0-5 s",
               "Q5_DC_cc_5s")

    tracer_amortissement(
        [("Extrémité ouverte, R = 10⁶ Ω", [(R_[("AC", "ouvert1e6")], dict(p0, R=1e6, L=0.001)),
                                           (res_N["ouvert1e6"], dict(p0, R=1e6, L=0.001, dt=dt_N))]),
         ("Court-circuit, R = L = 0,001", [(R_[("AC", "cc")], dict(p0, R=0.001, L=0.001)),
                                          (res_N["cc"], dict(p0, R=0.001, L=0.001, dt=dt_N))])],
        ["Δt = 0,1 ms (retard interpolé)", "Δt = τ/5 (retard exact)"], "Q4_amortissement")

    ecrire_indicateurs(ind)
    return ind


if __name__ == "__main__":
    main()
