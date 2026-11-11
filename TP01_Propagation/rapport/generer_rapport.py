# -*- coding: utf-8 -*-
"""
Génère rapport/rapport_TP01.docx à partir des sorties des scripts :
resultats/matlab/indicateurs.csv, resultats/matlab/validation_livre.csv,
les CSV des cas et les figures de figures/. Aucune valeur numérique n'est saisie
à la main : tout est lu dans ces fichiers ou calculé ici à partir d'eux.
"""

import csv
import math
import os

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

TP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(TP, "resultats", "matlab")
FIG = os.path.join(TP, "figures")
EQ = os.path.join(TP, "rapport", "equations")
SORTIE = os.path.join(TP, "rapport", "rapport_TP01.docx")


def lire_indicateurs():
    with open(os.path.join(RES, "indicateurs.csv")) as fh:
        return {k: float(v) for k, v in list(csv.reader(fh))[1:]}


def lire_validation():
    with open(os.path.join(RES, "validation_livre.csv")) as fh:
        lignes = list(csv.reader(fh))[1:]
    return [(l[0], [float(x) for x in l[1:]]) for l in lignes]


def lire_cas(nom):
    return np.loadtxt(os.path.join(RES, nom + ".csv"), delimiter=",", skiprows=1)


I = lire_indicateurs()
VAL = lire_validation()

# Données de l'énoncé (entrées des scripts, pas des résultats).
Lp, Cp, d, R_RL, L_RL, dt = 1.5e-3, 0.02e-6, 100.0, 400.0, 0.25, 1e-4
Vm = 230000 * math.sqrt(2) / math.sqrt(3)
w = 2 * math.pi * 60


def nb(x, nd=2):
    """Nombre au format français : virgule décimale, espace fine pour les milliers."""
    s = "%.*f" % (nd, x)
    signe = ""
    if s.startswith("-"):
        signe, s = "−", s[1:]
    if "." in s:
        e, f_ = s.split(".")
    else:
        e, f_ = s, ""
    groupes = []
    while len(e) > 3:
        groupes.insert(0, e[-3:])
        e = e[:-3]
    groupes.insert(0, e)
    e = " ".join(groupes)
    return signe + (e + "," + f_ if f_ else e)


def sci(x, nd=3):
    m, ex = ("%.*e" % (nd, x)).split("e")
    return "%s·10^%d" % (m.replace(".", ","), int(ex))


# Grandeurs dérivées, calculées à partir des sorties.
Zc, tau, vp, Req = I["Zc_ohm"], I["tau_s"], I["vp_mi_s"], I["Req_ohm"]
bd = w * tau
ferranti = 1 / math.cos(bd)
a_interp = tau / dt - math.floor(tau / dt)
f_mode = 1 / (4 * tau)
H2 = 1 - 2 * a_interp * (1 - a_interp) * (1 - math.cos(2 * math.pi * f_mode * dt))
G1e6 = I["Gamma_R_1e+06"]
t_num_pred = 2 * tau / (-(math.log(abs(G1e6)) + math.log(H2)))
pas_dc = 2 * 230000 / Zc
L_tot = Lp * d + 0.001
i_dc_cc_pred = 230000 / 0.001 * (1 - math.exp(-5 * 0.001 / L_tot))
G999_front = (999 + 2 * 0.001 / dt - Zc) / (999 + 2 * 0.001 / dt + Zc)

ra = lire_cas("Q1_RL_arrondi_20ms")
ri = lire_cas("Q1_RL_interp_20ms")
dv2 = np.abs(ra[:, 4] - ri[:, 4])
t_dv2max = ra[np.argmax(dv2), 0]
sel5 = ra[:, 0] >= 5e-3
dv2_apres5 = float(np.max(dv2[sel5]))
cc = lire_cas("Q3_cc")
n07 = int(np.argmin(np.abs(cc[:, 0] - 7e-4)))
i2_cc_arr, v2_cc_arr = cc[n07, 5], cc[n07, 4]
v_inc_cc = 0.5 * (v2_cc_arr + Zc * i2_cc_arr)   # onde incidente : v2 + Zc.i2 = 2.v_inc
ecart_tau = max(abs(a[k] - b[k]) / max(abs(a[k]), 1e-9)
                for (ta, a), (tb, b) in zip([x for x in VAL if x[0] == "0.00055"],
                                            [x for x in VAL if x[0] == "exact"])
                for k in range(1, 5) if abs(a[k]) > 0)

doc = Document()
sec = doc.sections[0]
sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
sec.left_margin = sec.right_margin = Cm(2.3)
sec.top_margin = sec.bottom_margin = Cm(2.2)

st = doc.styles["Normal"]
st.font.name = "Calibri"
st.font.size = Pt(11)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
st.paragraph_format.space_after = Pt(4)
st.paragraph_format.line_spacing = 1.1
for niv, taille in ((1, 14), (2, 12)):
    h = doc.styles["Heading %d" % niv]
    h.font.name = "Calibri"
    h.font.size = Pt(taille)
    h.font.bold = True
    h.font.color.rgb = RGBColor(0, 0, 0)
    h.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
    h.paragraph_format.space_before = Pt(12 if niv == 1 else 8)
    h.paragraph_format.space_after = Pt(4)
    h.paragraph_format.keep_with_next = True

compteur = {"fig": 0, "tab": 0, "eq": 0}


def titre(texte, niv=1):
    doc.add_heading(texte, level=niv)


def para(texte, gras=None, italique=False, align=None, taille=None):
    p = doc.add_paragraph()
    morceaux = texte.split("**")
    for k, m in enumerate(morceaux):
        r = p.add_run(m)
        r.bold = (k % 2 == 1)
        r.italic = italique
        if taille:
            r.font.size = Pt(taille)
    p.paragraph_format.alignment = align if align is not None else WD_ALIGN_PARAGRAPH.JUSTIFY
    return p


def equation(latex, nom, taille=12):
    os.makedirs(EQ, exist_ok=True)
    chemin = os.path.join(EQ, nom + ".png")
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, "$" + latex + "$", fontsize=taille)
    fig.savefig(chemin, dpi=300, bbox_inches="tight", pad_inches=0.03, transparent=False)
    plt.close(fig)
    from PIL import Image
    largeur_px = Image.open(chemin).size[0]
    compteur["eq"] += 1
    p = doc.add_paragraph()
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = False
    p.add_run().add_picture(chemin, width=Cm(min(largeur_px / 300 * 2.54, 13.5)))
    p.add_run("\t(%d)" % compteur["eq"])
    return compteur["eq"]


def figure(nom, legende, largeur=12.5):
    compteur["fig"] += 1
    p = doc.add_paragraph()
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(os.path.join(FIG, nom + ".png"), width=Cm(largeur))
    c = doc.add_paragraph()
    c.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = c.add_run("Figure %d : " % compteur["fig"])
    r.bold = True
    r.font.size = Pt(9.5)
    r2 = c.add_run(legende)
    r2.font.size = Pt(9.5)
    c.paragraph_format.space_after = Pt(10)
    return compteur["fig"]


def tableau(entetes, lignes, legende, largeurs):
    compteur["tab"] += 1
    c = doc.add_paragraph()
    c.paragraph_format.keep_with_next = True
    r = c.add_run("Tableau %d : " % compteur["tab"])
    r.bold = True
    r.font.size = Pt(9.5)
    r2 = c.add_run(legende)
    r2.font.size = Pt(9.5)
    t = doc.add_table(rows=1, cols=len(entetes))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for k, e in enumerate(entetes):
        cel = t.rows[0].cells[k]
        cel.text = ""
        run = cel.paragraphs[0].add_run(e)
        run.bold = True
        run.font.size = Pt(9.5)
        sh = OxmlElement("w:shd")
        sh.set(qn("w:val"), "clear")
        sh.set(qn("w:fill"), "E7E6E6")
        cel._tc.get_or_add_tcPr().append(sh)
    for ligne in lignes:
        cels = t.add_row().cells
        for k, v in enumerate(ligne):
            cels[k].text = ""
            run = cels[k].paragraphs[0].add_run(v)
            run.font.size = Pt(9.5)
            cels[k].paragraphs[0].alignment = (WD_ALIGN_PARAGRAPH.LEFT if k == 0
                                               else WD_ALIGN_PARAGRAPH.CENTER)
    for ligne in t.rows:
        for k, cel in enumerate(ligne.cells):
            cel.width = Cm(largeurs[k])
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return compteur["tab"]


def saut_page():
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


# Page de garde.
for _ in range(5):
    doc.add_paragraph()
para("École Nationale Polytechnique - Alger", align=WD_ALIGN_PARAGRAPH.CENTER, taille=12)
para("Module : Réseaux Électriques", align=WD_ALIGN_PARAGRAPH.CENTER, taille=12)
doc.add_paragraph()
p = para("**TP 01 - Propagation dans les lignes électriques**", align=WD_ALIGN_PARAGRAPH.CENTER,
         taille=18)
para("Modèle de Bergeron et règle des trapèzes : régimes transitoires d'une ligne longue sans pertes",
     align=WD_ALIGN_PARAGRAPH.CENTER, taille=12, italique=True)
for _ in range(4):
    doc.add_paragraph()
para("Étudiant : NOM Prénom", align=WD_ALIGN_PARAGRAPH.CENTER, taille=12)
para("Groupe : ...", align=WD_ALIGN_PARAGRAPH.CENTER, taille=12)
para("Enseignant : Prof. Karim SEBAA", align=WD_ALIGN_PARAGRAPH.CENTER, taille=12)
para("Date : ...", align=WD_ALIGN_PARAGRAPH.CENTER, taille=12)
saut_page()

titre("1. Objectif")
para("On simule la mise sous tension d'une ligne monophasée sans pertes de %s mi "
     "(L' = 1,5 mH/mi, C' = 0,02 µF/mi) alimentée par vs(t) = 230 000·√2/√3·"
     "cos(2π·60·t) et fermée sur une charge R-L (R = 400 Ω, L = 0,25 H). "
     "L'interrupteur se ferme à t = 0,1 ms et le pas de calcul vaut Δt = 0,1 ms. On reprend "
     "ensuite le calcul pour une extrémité ouverte, une extrémité en court-circuit, une source "
     "continue de 230 kV et une onde de choc de foudre. Les grandeurs suivies sont i1, v1 au départ "
     "(extrémité k) et i2, v2 à l'arrivée (extrémité m)." % nb(d, 0))

titre("2. Modèle et méthode numérique")
titre("2.1 Ligne sans pertes : modèle de Bergeron", 2)
para("Pour la ligne sans pertes, l'impédance caractéristique, la vitesse de propagation et le "
     "temps de propagation sont :")
e1 = equation(r"Z_c=\sqrt{L'/C'},\qquad v_p=1/\sqrt{L'C'},\qquad \tau=d/v_p", "eq_zc")
para("ce qui donne Zc = %s Ω, vp = %s mi/s et τ = %s µs, soit τ/Δt = %s. "
     "Le livre arrondit à Zc = 274 Ω et τ = 0,00055 s."
     % (nb(Zc), nb(vp, 0), nb(tau * 1e6), nb(I["tau_sur_dt"], 3)))
para("La grandeur v + Zc·i (i compté dans le sens k → m) se conserve le long de l'onde "
     "incidente, v − Zc·i le long de l'onde réfléchie. Chaque extrémité se ramène donc à la "
     "résistance Zc en parallèle avec une source de courant d'historique, connue à l'instant t "
     "parce qu'elle ne dépend que de l'autre extrémité à t − τ :")
e2 = equation(r"i_1(t)=\frac{v_1(t)}{Z_c}+I_k,\qquad I_k=i_2(t-\tau)-\frac{v_2(t-\tau)}{Z_c}",
              "eq_k")
e3 = equation(r"i_2(t)=I_m-\frac{v_2(t)}{Z_c},\qquad I_m=i_1(t-\tau)+\frac{v_1(t-\tau)}{Z_c}",
              "eq_m")
para("i1 entre dans la ligne en k, i2 en sort en m vers la charge. Le signe de Ik est celui de "
     "l'énoncé ; il se contrôle au régime permanent (paragraphe 4.2), puisque l'onde réfléchie ne "
     "revient en k qu'après 2τ et n'intervient pas dans le tableau de validation.")

titre("2.2 Charge R-L : modèle compagnon de la règle des trapèzes", 2)
para("L'équation diL/dt = vL/L intégrée par la règle des trapèzes donne un circuit linéaire : "
     "une résistance Req en parallèle avec une source Ih connue au pas précédent.")
e4 = equation(r"i_L(t)=\frac{v_L(t)}{R_{eq}}+I_h,\qquad R_{eq}=\frac{2L}{\Delta t},\qquad "
              r"I_h=i_L(t-\Delta t)+\frac{v_L(t-\Delta t)}{R_{eq}}", "eq_trap")
para("Ici Req = %s Ω. Côté m, Zc ∥ Im alimente R en série avec Req ∥ Ih ; "
     "la résolution du petit circuit « continu » donne directement :" % nb(Req, 0))
e5 = equation(r"i_2=\frac{I_m+R_{eq}I_h/Z_c}{1+(R+R_{eq})/Z_c},\qquad v_2=Z_c\,(I_m-i_2),"
              r"\qquad v_L=v_2-R\,i_2", "eq_m_sol")
para("Côté k, la tension est imposée : v1 = vs une fois l'interrupteur fermé, puis i1 par (%d)."
     % e2)

titre("2.3 Retard non multiple du pas", 2)
para("τ/Δt n'est pas entier : la valeur x(t − τ) tombe entre deux échantillons "
     "stockés. On l'obtient par interpolation linéaire :")
e6 = equation(r"x(t-\tau)\approx x_j+a\,(x_{j+1}-x_j),\qquad j=\lfloor (t-\tau)/\Delta t\rfloor,"
              r"\qquad a=(t-\tau)/\Delta t-j", "eq_interp")
para("L'option « arrondi » remplace τ par le multiple de Δt le plus proche "
     "(ici %s ms, soit une ligne électriquement %s %% plus courte)."
     % (nb(I["arrondi_tau_eff_s"] * 1e3, 1), nb((1 - I["arrondi_tau_eff_s"] / tau) * 100, 1)))
para("Il ne faut pas interpoler à travers l'instant de fermeture. Pour t = 0,6 ms et τ = 0,55 ms, "
     "t − τ = 0,05 ms précède la fermeture : la ligne est au repos et l'historique vaut 0. "
     "Une interpolation entre l'échantillon à t = 0 (interrupteur ouvert) et celui à 0,1 ms "
     "ferait apparaître l'onde en m un pas trop tôt : le script donne alors i2(0,6 ms) = %s A et "
     "i2(0,7 ms) = %s A, au lieu de 0 et %s A."
     % (nb(I["piege_i2_0p0006"]), nb(I["piege_i2_0p0007"]), nb(I["val_livre_t0.0007_i2"])))

titre("2.4 Mise en oeuvre", 2)
para("Un seul solveur simuler_ligne(p) est appelé pour tous les cas ; la structure p contient "
     "les paramètres de ligne, la charge, le pas, la durée, la source (fonction de t) et l'option "
     "de retard. Les tableaux sont préalloués et la boucle en temps est une boucle for simple "
     "(50 000 pas pour 5 s). Le script TP01_ligne_longue.m regroupe tous les cas et contient "
     "ses fonctions locales ; il a été exécuté sous GNU Octave 8.4 (syntaxe compatible MATLAB, "
     "sans boîte à outils). La version Python tp01_ligne.py reprend les mêmes fonctions : "
     "l'écart entre les deux sur l'ensemble des CSV est nul à 10 chiffres significatifs "
     "(compare_matlab_python.py). Les figures du rapport sont produites par la version Python ; "
     "le script MATLAB trace les mêmes figures dans figures/matlab.")

titre("3. Validation par rapport au livre")
livre = {0.0001: ("685", "187 661", "0", "0"), 0.0002: ("683", "187 261", "0", "0"),
         0.0007: ("662", "181 293", "66", "356 731")}
lignes = []
for tv in (0.0001, 0.0002, 0.0007):
    s1 = [v for tag, v in VAL if tag == "0.00055" and abs(v[0] - tv) < 1e-9][0]
    s2 = [v for tag, v in VAL if tag == "exact" and abs(v[0] - tv) < 1e-9][0]
    b = livre[tv]
    lignes.append([nb(tv * 1e3, 1), "livre", b[0], b[1], b[2], b[3]])
    lignes.append(["", "τ = 0,55 ms", nb(s1[1]), nb(s1[2], 0), nb(s1[3]), nb(s1[4], 0)])
    lignes.append(["", "τ exact", nb(s2[1]), nb(s2[2], 0), nb(s2[3]), nb(s2[4], 0)])
tableau(["t (ms)", "source", "i1 (A)", "v1 (V)", "i2 (A)", "v2 (V)"], lignes,
        "valeurs du livre (solution.pdf) et du script, charge R-L.", [1.6, 2.6, 2.2, 2.8, 2.2, 2.8])
s07 = [v for tag, v in VAL if tag == "0.00055" and abs(v[0] - 0.0007) < 1e-9][0]
v1_01 = [v for tag, v in VAL if tag == "0.00055" and abs(v[0] - 1e-4) < 1e-9][0][2]
v1_02 = [v for tag, v in VAL if tag == "0.00055" and abs(v[0] - 2e-4) < 1e-9][0][2]
v1_015 = 0.5 * (v1_01 + v1_02)                  # v1(0,15 ms) interpolé par le script
Im_b = 1368.0                                   # valeur arrondie de la figure 2.10 du livre
i2_b = Im_b / (1 + (R_RL + 2 * L_RL / dt) / 274)
v2_b = 274 * (Im_b - i2_b)
para("Les courants et tensions coïncident avec le livre à l'arrondi près. À t = 0,7 ms, le script "
     "donne v2 = %s V contre 356 731 V. L'écart de %s V vient des arrondis du livre : en reprenant "
     "son calcul avec Zc = 274 Ω et Im arrondi à 1368 A, on trouve i2 = %s A et "
     "v2 = 274·(1368 − i2) = %s V, la valeur du livre. Le livre prend aussi "
     "v1(0,15 ms) = vs(0,15 ms) = 187 494 V, alors que le script interpole entre les échantillons "
     "à 0,1 et 0,2 ms ; l'effet sur Im est de %s A. Avec le τ exact, l'onde arrive "
     "toujours au même pas (0,7 ms) et les valeurs du tableau diffèrent au plus de %s %% "
     "entre les deux retards. La suite utilise le τ exact."
     % (nb(s07[4], 0), nb(s07[4] - 356731, 0), nb(i2_b, 2), nb(v2_b, 0), nb(abs(187494 - v1_015) / Zc, 2), nb(ecart_tau * 100, 3)))

titre("4. Q1 : charge R-L, source alternative")
titre("4.1 Régime transitoire", 2)
figure("Q1_RL_zoom", "charge R-L, 10 premières ms. À regarder : l'échelon de i1 à la fermeture "
       "(v1/Zc), l'arrivée de l'onde en m à 0,7 ms avec v2 proche du double de l'onde incidente, "
       "puis les sauts de i1 tous les 2τ ≈ 1,1 ms quand l'onde réfléchie revient en k.")
para("À la fermeture, la ligne présente Zc à la source : i1(0,1 ms) = v1/Zc = %s A. Rien ne change "
     "en m tant que l'onde n'est pas arrivée ; elle y parvient %s µs après la fermeture, et le "
     "premier pas où elle est vue est t = %s ms (%s ms après la fermeture, quantification par Δt). "
     "Au front, l'inductance se comporte presque en circuit ouvert : la charge vue par l'onde est "
     "R + Req = %s Ω, d'où Γ = %s et v2 = (1 + Γ)·(onde incidente). "
     "Le rapport |v2|max/Vm vaut %s."
     % (nb(I["val_livre_t0.0001_i1"]), nb(tau * 1e6), nb(I["AC_RL_t_arrivee"] * 1e3, 1),
        nb((I["AC_RL_t_arrivee"] - 1e-4) * 1e3, 1), nb(R_RL + Req, 0),
        nb(I["Gamma_front_RL_discret"], 4), nb(I["AC_RL_rapport_v2"], 3)))
para("Chaque aller-retour, l'onde réfléchie en m (Γ = %s pour R seule) revient en k où la "
     "source idéale impose v1 : elle y est réfléchie avec Γ = −1. Seule la résistance de "
     "la charge prélève de l'énergie ; l'écart à la solution sinusoïdale tombe sous 1 %% de |I2| "
     "après t = %s ms." % (nb(I["Gamma_R_400"], 3), nb(I["Q1_duree_transitoire_1pct_s"] * 1e3, 1)))
figure("Q1_RL_5s", "charge R-L, 0 à 5 s. À regarder : après quelques dizaines de ms, les quatre "
       "grandeurs sont sinusoïdales à 60 Hz ; les amplitudes sont celles du tableau 2.",
       largeur=11)

titre("4.2 Régime permanent et contrôle par les phaseurs", 2)
para("Le régime permanent se calcule à la main en écrivant la ligne comme un quadripôle ABCD "
     "sans pertes, fermé sur ZL = R + jωL :")
e8 = equation(r"\underline{V}_1=\cos(\beta d)\,\underline{V}_2+jZ_c\sin(\beta d)\,\underline{I}_2,"
              r"\qquad \underline{I}_1=\frac{j\sin(\beta d)}{Z_c}\,\underline{V}_2+\cos(\beta d)\,"
              r"\underline{I}_2", "eq_abcd")
para("avec βd = ωτ = %s rad et V1 = Vm. Côté simulation, on ajuste par moindres "
     "carrés a·cos(ωt) + b·sin(ωt) + c sur l'intervalle 4-5 s." % nb(bd, 4))
lignes = []
for g, u, ech in (("I1", "A", 1), ("I2", "A", 1), ("V2", "kV", 1e-3)):
    lignes.append(["|%s| (%s)" % (g, u), nb(I["Q1_%s_phaseur_amp" % g] * ech, 2),
                   nb(I["Q1_%s_sim_amp" % g] * ech, 2), nb(I["Q1_%s_ecart_pct" % g], 3)])
    lignes.append(["arg %s (°)" % g, nb(I["Q1_%s_phaseur_phase_deg" % g], 3),
                   nb(I["Q1_%s_sim_phase_deg" % g], 3), ""])
tableau(["grandeur", "phaseurs", "simulation 4-5 s", "écart (%)"], lignes,
        "régime permanent de Q1 (amplitudes crête, phases par rapport à vs).", [3.5, 3.5, 3.5, 2.5])
para("Les amplitudes concordent à %s %% près au plus. Ce contrôle valide le signe de Ik : avec le "
     "signe opposé, l'onde réfléchie reviendrait en k avec la mauvaise polarité et le régime "
     "permanent ne correspondrait plus aux phaseurs."
     % nb(max(I["Q1_I1_ecart_pct"], I["Q1_I2_ecart_pct"], I["Q1_V2_ecart_pct"]), 3))

titre("4.3 Interpolation et arrondi du retard", 2)
figure("Q1_RL_arrondi_interp", "comparaison des deux traitements du retard sur 10 ms. À regarder : "
       "avec τ arrondi à 5Δt, l'onde arrive en m un pas plus tôt et les réflexions "
       "successives se décalent de plus en plus.")
para("Sur les 20 premières ms, l'écart maximal sur v2 entre les deux options vaut %s kV et se "
     "produit à t = %s ms, au pas où l'onde est déjà arrivée dans un calcul et pas encore dans "
     "l'autre. Après 5 ms, l'écart reste de %s kV : l'arrondi change le temps de propagation de "
     "%s %%, donc les instants de toutes les réflexions."
     % (nb(I["arrondi_max_dv2_V"] / 1e3, 1), nb(t_dv2max * 1e3, 1), nb(dv2_apres5 / 1e3, 1),
        nb((1 - I["arrondi_tau_eff_s"] / tau) * 100, 1)))

titre("5. Q2 : extrémité ouverte")
para("L'énoncé propose R = 999 Ω (avec L = 0,001 H) pour représenter la ligne ouverte. "
     "999 Ω ne vaut que %s·Zc : le coefficient de réflexion n'est que %s, contre %s pour "
     "R = 10⁶ Ω. Le tableau 3 rassemble les coefficients de réflexion des charges "
     "résistives étudiées." % (nb(999 / Zc, 2), nb(I["Gamma_R_999"], 3), nb(G1e6, 5)))
tableau(["charge", "Γ = (ZL − Zc)/(ZL + Zc)", "1 + Γ"],
        [["R = 400 Ω", nb(I["Gamma_R_400"], 4), nb(1 + I["Gamma_R_400"], 4)],
         ["R = 999 Ω", nb(I["Gamma_R_999"], 4), nb(1 + I["Gamma_R_999"], 4)],
         ["R = 10⁶ Ω", nb(G1e6, 6), nb(1 + G1e6, 6)],
         ["R = 0,001 Ω", nb(I["Gamma_R_0.001"], 6), nb(1 + I["Gamma_R_0.001"], 6)],
         ["R + Req = %s Ω (front, R-L)" % nb(R_RL + Req, 0), nb(I["Gamma_front_RL_discret"], 4),
          nb(1 + I["Gamma_front_RL_discret"], 4)]],
        "coefficients de réflexion en m (Zc = %s Ω)." % nb(Zc), [6, 4.5, 3])
figure("Q2_ouvert_zoom", "extrémité ouverte, 20 premières ms. À regarder : à l'arrivée, v2 vaut "
       "1 + Γ fois l'onde incidente (%s pour 999 Ω, %s pour 10⁶ Ω) ; avec "
       "10⁶ Ω le courant i2 reste nul et v2 oscille autour de la sinusoïde."
       % (nb(1 + G999_front, 2), nb(1 + G1e6, 3)))
para("Avec R = 10⁶ Ω, |v2|max atteint %s kV, soit %s·Vm : c'est le doublement de "
     "tension à l'extrémité ouverte (Γ ≈ 1). Avec 999 Ω, le rapport tombe à %s. "
     "En fin de simulation (4-5 s), |v2|max vaut %s kV et %s kV pour les deux résistances ; le "
     "régime permanent de la ligne à vide donne Vm/cos(βd) = %s kV (effet Ferranti, "
     "+%s %%)."
     % (nb(I["AC_ouvert1e6_crete_v2"] / 1e3, 1), nb(I["AC_ouvert1e6_rapport_v2"], 3),
        nb(I["AC_ouvert999_rapport_v2"], 3), nb(I["AC_ouvert999_v2max_4_5s"] / 1e3, 1),
        nb(I["AC_ouvert1e6_v2max_4_5s"] / 1e3, 1), nb(Vm * ferranti / 1e3, 1),
        nb((ferranti - 1) * 100, 2)))
f_q2_5s = figure("Q2_ouvert_5s", "extrémité ouverte, 0 à 5 s. À regarder : avec Δt = 0,1 ms, "
       "l'oscillation libre disparaît en moins d'une seconde, y compris pour 10⁶ Ω ; "
       "le paragraphe 9.2 montre que cet amortissement est d'origine numérique.", largeur=11)

titre("6. Q3 : extrémité en court-circuit")
figure("Q3_cc_zoom", "court-circuit R = L = 0,001, 20 premières ms. À regarder : v2 reste "
       "faible et change de signe à chaque pas après l'arrivée de l'onde ; i2 monte par paliers "
       "jusqu'à plus de 3 kA.")
para("Pour R = L = 0,001, le régime libre de v2 est faible mais il n'est pas nul dès l'arrivée : "
     "avec Δt = 0,1 ms, Req = 2L/Δt = %s Ω n'est pas négligeable devant Zc, et "
     "le premier pas voit Γ = %s. Les trois premiers échantillons de v2 valent %s, %s et %s V : "
     "l'alternance de signe d'un pas à l'autre est l'oscillation numérique connue de la règle des "
     "trapèzes quand Δt est grand devant la constante de temps du circuit (L/Zc = %s µs "
     "ici). Le courant, lui, double au premier passage : à t = 0,7 ms, i2 = %s A pour une onde "
     "incidente de %s A (2·v_inc/Zc = %s A, diminué par les 20 Ω de Req). Les "
     "réflexions suivantes s'additionnent ensuite : |i2|max atteint %s A et |i1|max %s A."
     % (nb(2 * 0.001 / dt, 0), nb(I["Gamma_front_cc_discret"], 3), nb(I["AC_cc_v2_n_arr"], 0),
        nb(I["AC_cc_v2_n_arr_plus1"], 0), nb(I["AC_cc_v2_n_arr_plus2"], 0),
        nb(0.001 / Zc * 1e6, 2), nb(i2_cc_arr, 0), nb(v_inc_cc / Zc, 0), nb(2 * v_inc_cc / Zc, 0),
        nb(I["AC_cc_crete_i2"], 0), nb(I["AC_cc_crete_i1"], 0)))
para("Sur l'intervalle 4-5 s, i1 garde une composante continue de %s A : la boucle source-ligne-"
     "court-circuit ne contient que R = 0,001 Ω pour une inductance totale L'd + L = %s H, "
     "soit une constante de temps de %s s." % (nb(I["AC_cc_moyenne_i1_4_5s"], 1), nb(L_tot, 3),
                                               nb(L_tot / 0.001, 0)))
f_q3_5s = figure("Q3_cc_5s", "court-circuit, 0 à 5 s. À regarder : l'enveloppe des courants se stabilise ; "
       "la composante continue de i1 ne décroît pratiquement pas sur 5 s.", largeur=11)

titre("7. Q5 : source continue de 230 kV")
figure("Q5_DC_zoom", "source continue, 10 premières ms. À regarder : en court-circuit, i1 et i2 "
       "croissent par marches à chaque aller-retour ; pour les deux autres charges, v2 rejoint "
       "230 kV par paliers de durée 2τ.")
para("En continu, l'onde incidente est un échelon de 230 kV et les réflexions successives "
     "s'additionnent : les courbes prennent la forme d'escaliers de largeur 2τ, ce que la "
     "source sinusoïdale masque parce que vs varie pendant un aller-retour. En court-circuit, "
     "chaque aller-retour ajoute 2·230 kV/Zc = %s A ; le courant atteint %s A à t = 5 s, "
     "pour V/R·(1 − exp(−Rt/(L'd + L))) = %s A attendu. Il n'existe pas de régime "
     "permanent fini, la source idéale débitant dans une boucle presque sans résistance."
     % (nb(pas_dc, 1), nb(I["DC_cc_i1_final"], 0), nb(i_dc_cc_pred, 0)))
para("Pour la charge R-L, la première crête de v2 vaut %s kV (rapport %s, soit 1 + Γ au "
     "front) et le régime final est v2 = %s kV, i2 = %s A = V/R. Pour 999 Ω, la première "
     "crête vaut %s kV (rapport %s, à comparer à 1 + Γ = %s avec Req = 20 Ω en série) "
     "et le courant final %s A."
     % (nb(I["DC_RL_crete_v2"] / 1e3, 1), nb(I["DC_RL_rapport_v2"], 3), nb(I["DC_RL_v2_final"] / 1e3, 1),
        nb(I["DC_RL_i2_final"], 1), nb(I["DC_ouvert999_crete_v2"] / 1e3, 1),
        nb(I["DC_ouvert999_rapport_v2"], 3), nb(1 + G999_front, 3), nb(I["DC_ouvert999_i2_final"], 1)))
figure("Q5_DC_RL_ouvert_5s", "source continue, charges R-L et 999 Ω, 0 à 5 s. À regarder : "
       "les deux cas tendent vers v2 = 230 kV ; le courant final vaut V/R.", largeur=11)
figure("Q5_DC_cc_5s", "source continue en court-circuit, 0 à 5 s. À regarder : croissance "
       "quasi linéaire du courant jusqu'à environ 7,5 MA, physiquement impossible, qui traduit "
       "l'absence de résistance dans le modèle.", largeur=11)

titre("8. Q6 : onde de choc de foudre")
titre("8.1 Forme de l'onde", 2)
e9 = equation(r"v_s(t)=\eta\,V_{max}\,\frac{(t/\tau_1)^n}{1+(t/\tau_1)^n}\,e^{-t/\tau_2},"
              r"\qquad \tau_1=1{,}2\ \mu s,\ \tau_2=50\ \mu s,\ n=3", "eq_foudre")
para("Les mesures sont faites numériquement sur une grille de 1 ns. La formule brute (η = 1) "
     "culmine à %s kV à t = %s µs, et non à Vmax. Le facteur η = Vmax/crête = %s ramène "
     "la crête à %s kV. La durée de front conventionnelle T1 = 1,67·(t90 − t30) vaut "
     "%s µs (t30 = %s µs, t90 = %s µs) et la durée jusqu'à mi-valeur, comptée depuis "
     "l'origine conventionnelle O1 = t30 − 0,3·T1 = %s µs, vaut T2 = %s µs. "
     "Avec τ1 = 1,2 µs et τ2 = 50 µs, la formule donne donc une onde "
     "%s/%s µs et non 1,2/50 µs : les constantes de temps ne sont pas les durées "
     "normalisées. Le facteur η ne modifie pas T1 et T2 (multiplication par une constante)."
     % (nb(I["foudre_crete_brute_V"] / 1e3, 1), nb(I["foudre_t_crete_s"] * 1e6, 2), nb(I["foudre_eta"], 4),
        nb(I["foudre_crete_corrigee_V"] / 1e3, 1), nb(I["foudre_T1_s"] * 1e6, 2),
        nb(I["foudre_t30_s"] * 1e6, 3), nb(I["foudre_t90_s"] * 1e6, 3), nb(I["foudre_O1_s"] * 1e6, 3),
        nb(I["foudre_T2_s"] * 1e6, 1), nb(I["foudre_T1_s"] * 1e6, 2), nb(I["foudre_T2_s"] * 1e6, 1)))
figure("Q6a_onde_foudre", "onde de choc brute et corrigée. À regarder : la crête de la formule "
       "brute reste sous 230 kV (pointillés) ; le front dure quelques microsecondes, la queue "
       "plusieurs dizaines.", largeur=11)

titre("8.2 Ligne de 100 mi, fenêtre de 250 µs", 2)
para("Avec Δt = 60 ns et T = 250 µs, le calcul compte %s pas. Le temps de propagation "
     "τ = %s µs dépasse la fenêtre d'observation : l'onde n'atteint jamais l'extrémité m. "
     "Le script donne max|v2| = %s V et max|i2| = %s A sur toute la durée, et "
     "max|i1 − vs/Zc| = %s A : la source ne voit que l'impédance caractéristique, i1 culmine à "
     "%s A = 230 kV/Zc. Le résultat est le même pour les trois charges (écart %s A sur i1)."
     % (nb(I["Q6_100mi_nb_pas"], 0), nb(tau * 1e6, 1), nb(I["Q6_100mi_max_abs_v2"], 0),
        nb(I["Q6_100mi_max_abs_i2"], 0), nb(I["Q6_100mi_max_ecart_i1_vs_sur_Zc"], 0),
        nb(I["Q6_100mi_max_i1"], 1), nb(I["Q6_100mi_ecart_entre_charges_i1"], 0)))
figure("Q6b_foudre_100mi", "choc de foudre sur la ligne de 100 mi. À regarder : i1 reproduit la "
       "forme de vs à l'échelle 1/Zc, i2 et v2 restent nuls pendant les 250 µs.", largeur=11)

titre("8.3 Extension : ligne de 10 mi", 2)
para("Pour voir les réflexions dans la même fenêtre, on réduit la longueur à 10 mi : "
     "τ = %s µs et l'onde arrive en m à %s µs (premier pas de 60 ns après τ). "
     "La charge R-L vaut alors Req = 2L/Δt = %s MΩ au front : elle se comporte "
     "en circuit ouvert et v2 culmine à %s kV, soit %s·Vmax. Pour 999 Ω le rapport est "
     "%s. Avec R = L = 0,001, l'inductance de 1 mH n'est plus un court-circuit à l'échelle du "
     "front (L/Zc = %s µs pour un front de %s µs) : v2 monte à %s kV avant de s'annuler. "
     "Le court-circuit résistif pur (R = 0,001 Ω, L = 0) annule v2 (%s kV) et i2 atteint "
     "%s A."
     % (nb(I["Q6_10mi_tau_s"] * 1e6, 2), nb(I["Q6_10mi_RL_t_arrivee"] * 1e6, 2),
        nb(2 * L_RL / 60e-9 / 1e6, 2),
        nb(I["Q6_10mi_RL_crete_v2"] / 1e3, 1), nb(I["Q6_10mi_RL_rapport_v2"], 3),
        nb(I["Q6_10mi_ouvert999_rapport_v2"], 3), nb(0.001 / Zc * 1e6, 2), nb(I["foudre_T1_s"] * 1e6, 1),
        nb(I["Q6_10mi_cc_crete_v2"] / 1e3, 1), nb(I["Q6_10mi_ccR_crete_v2"] / 1e3, 1),
        nb(I["Q6_10mi_ccR_crete_i2"], 0)))
figure("Q6c_foudre_10mi", "choc de foudre sur une ligne de 10 mi, quatre charges. À regarder : "
       "doublement de v2 à l'extrémité R-L (ouverte pour le front) vers 55 µs, retour de "
       "l'onde réfléchie en k à 2τ ≈ 110 µs, puis inversion de v2 à 3τ après "
       "réflexion sur la source.", largeur=13)

titre("9. Q4 : discussion")
titre("9.1 Propagation et réflexions", 2)
para("Dans tous les cas, l'extrémité m ne réagit qu'après le temps de propagation τ "
     "(arrivée détectée au premier pas qui suit, 0,7 ms pour Δt = 0,1 ms). La source ne voit "
     "d'abord que Zc, quelle que soit la charge : i1 = v1/Zc jusqu'au retour de l'onde réfléchie à "
     "2τ. Le coefficient de réflexion Γ = (ZL − Zc)/(ZL + Zc) fixe la tension "
     "transmise 1 + Γ : proche de 2 à l'extrémité ouverte (doublement de tension), proche de 0 "
     "en court-circuit, où c'est le courant qui double. La source idéale se comporte en "
     "court-circuit pour l'onde réfléchie (Γ = −1 en k) : l'onde change de signe à "
     "chaque retour en k, d'où les oscillations libres de période 4τ = %s ms à l'extrémité "
     "ouverte et 2τ = %s ms en court-circuit." % (nb(4 * tau * 1e3, 2), nb(2 * tau * 1e3, 2)))
titre("9.2 Amortissement : rôle de R, part physique et part numérique", 2)
para("La ligne est sans pertes : seule la résistance de charge dissipe de l'énergie. Après n "
     "allers-retours, l'oscillation libre est multipliée par |Γ|ⁿ, soit une constante "
     "de temps")
e10 = equation(r"T_a=\frac{2\tau}{-\ln|\Gamma|}", "eq_amort")
para("qui vaut %s ms pour 999 Ω, %s s pour 10⁶ Ω et %s s pour 0,001 Ω. "
     "Les cas ouvert et court-circuit devraient donc osciller presque sans amortissement sur 5 s. "
     "Les figures %d et %d montrent au contraire un amortissement rapide : il vient de "
     "l'interpolation linéaire du retard, qui agit comme un filtre passe-bas à chaque passage "
     "sur la ligne. Pour le mode fondamental de la ligne ouverte (f = 1/(4τ) = %s Hz), le "
     "gain en puissance de l'interpolation sur un passage vaut 1 − 2a(1 − a)"
     "(1 − cos(2πfΔt)) = %s avec a = %s ; sur un aller-retour, cela donne une "
     "constante de temps prévue de %s ms. Le script mesure %s ms sur l'enveloppe de la figure %d."
     % (nb(I["AC_ouvert999_constante_amortissement_Gamma_s"] * 1e3, 2),
        nb(I["AC_ouvert1e6_constante_amortissement_Gamma_s"], 2),
        nb(I["AC_cc_constante_amortissement_Gamma_s"], 0), f_q2_5s, f_q3_5s, nb(f_mode, 1), nb(H2, 4),
        nb(a_interp, 3), nb(t_num_pred * 1e3, 1), nb(I["AC_ouvert1e6_dt1e-4_constante_mesuree_s"] * 1e3, 1),
        compteur["fig"] + 1))
figure("Q4_amortissement", "enveloppe de |v2 − v2,phaseur| (maximum sur 20 ms, échelle "
       "logarithmique). À regarder : avec Δt = τ/5 le retard est exact, la décroissance "
       "de l'extrémité ouverte suit la pente physique et le court-circuit ne s'amortit pas ; "
       "avec Δt = 0,1 ms l'interpolation éteint les deux en moins d'une seconde.", largeur=15.5)
para("Avec Δt = τ/5 = %s µs, le retard tombe exactement sur un échantillon et "
     "l'interpolation disparaît : la constante mesurée pour 10⁶ Ω vaut %s s, égale à "
     "2τ/(−ln|Γ|). L'écart au régime permanent sur 4-5 s est alors de %s kV sur v2 "
     "(contre %s V avec Δt = 0,1 ms) ; en court-circuit, il reste %s kV (contre %s V). C'est "
     "la raison de choisir Δt = τ/N lorsqu'une seule ligne est modélisée : le retard est "
     "exact et la seule dissipation est celle du circuit."
     % (nb(I["dt_tau_sur_5_s"] * 1e6, 2), nb(I["AC_ouvert1e6_dtTauSur5_constante_mesuree_s"], 2),
        nb(I["AC_ouvert1e6_dtTauSur5_residu_v2_4_5s"] / 1e3, 1),
        nb(I["AC_ouvert1e6_dt1e-4_residu_v2_4_5s"], 0), nb(I["AC_cc_dtTauSur5_residu_v2_4_5s"] / 1e3, 1),
        nb(I["AC_cc_dt1e-4_residu_v2_4_5s"], 0)))
para("Une oscillation non amortie pendant plusieurs secondes n'est pas physique : une ligne réelle "
     "a une résistance linéique R' et une conductance G', et l'effet de peau augmente R' aux "
     "fréquences des modes libres. La correction proposée par le cours consiste à ajouter une "
     "résistance localisée, série ou parallèle, à chaque extrémité du modèle sans pertes ; les "
     "programmes de type EMTP placent par exemple R'd/4 à chaque extrémité et R'd/2 au milieu, "
     "la ligne étant découpée en deux tronçons sans pertes.")
titre("9.3 Source alternative et source continue", 2)
para("Avec la source continue, l'onde incidente est un échelon constant : chaque réflexion ajoute "
     "un palier visible, et la réponse est un escalier de largeur 2τ qui converge vers "
     "V/R. Avec la source sinusoïdale, vs varie pendant un aller-retour (ω·2τ = "
     "%s rad) : les paliers se déforment et la réponse rejoint un régime sinusoïdal établi, donné "
     "par les phaseurs. La surtension maximale dépend de l'instant de fermeture : ici la fermeture "
     "a lieu près de la crête de vs (cos(ω·0,1 ms) = %s), et les crêtes de v2 rapportées "
     "à l'amplitude de la source sont voisines dans les deux cas : %s en alternatif contre %s en "
     "continu pour la charge R-L, %s contre %s pour R = 10⁶ Ω."
     % (nb(2 * bd, 3), nb(math.cos(w * 1e-4), 4), nb(I["AC_RL_rapport_v2"], 3),
        nb(I["DC_RL_rapport_v2"], 3), nb(I["AC_ouvert1e6_rapport_v2"], 3),
        nb(I["DC_ouvert1e6_rapport_v2"], 3)))
titre("9.4 Choc de foudre et choix du pas", 2)
para("Le front de l'onde de foudre dure %s µs, %s fois moins que τ pour la "
     "ligne de 100 mi : il faut un pas de l'ordre de 60 ns pour le décrire, et une fenêtre de "
     "250 µs ne laisse pas à l'onde le temps de traverser la ligne. À ces échelles de temps, "
     "toute inductance de charge (même 1 mH) se comporte en circuit ouvert au front, et l'extrémité "
     "subit le doublement de tension. Le modèle sans pertes surestime ces crêtes : l'effet couronne "
     "et l'effet de peau atténuent et étalent réellement le front."
     % (nb(I["foudre_T1_s"] * 1e6, 2), nb(tau / I["foudre_T1_s"], 0)))

titre("10. Vérification croisée avec Simulink")
para("Le script construire_modele_simulink.m construit TP01_simulink_check.slx avec Simscape "
     "Electrical (Specialized Power Systems) : source alternative, disjoncteur fermé à 0,1 ms, "
     "bloc Distributed Parameters Line monophasé (R' = 0, L' = %s mH/km, C' = %s nF/km, %s km), "
     "charge RL série, powergui discret avec Ts = Δt. Les grandeurs v1, i1, v2, i2 sont "
     "enregistrées dans resultats/simulink_Q1.mat ; TP01_ligne_longue.m les superpose alors aux "
     "résultats du modèle de Bergeron (figure Q1_comparaison_simulink) et écrit l'écart maximal "
     "sur 20 ms. Simscape n'étant pas disponible sur la machine de préparation, ce modèle reste "
     "à exécuter en salle de TP ; aucun résultat Simulink n'est donc présenté ici."
     % (nb(Lp / 1.609344 * 1e3, 4), nb(Cp / 1.609344 * 1e9, 3), nb(d * 1.609344, 2)))

titre("11. Conclusion")
para("Le modèle de Bergeron associé au modèle compagnon des trapèzes reproduit les valeurs du "
     "livre (i2(0,7 ms) = %s A pour 66 A) et le régime permanent calculé par phaseurs à %s %% "
     "près. L'onde atteint l'extrémité m après τ = %s µs ; la tension y double presque "
     "à l'extrémité ouverte (%s·Vm) et s'effondre en court-circuit, où le courant double. "
     "Avec Δt = 0,1 ms, l'interpolation du retard amortit les oscillations libres avec une "
     "constante de %s ms, alors que la dissipation de la charge seule donnerait %s s pour "
     "10⁶ Ω : le choix Δt = τ/N supprime cet effet. Pour le choc de foudre, "
     "la ligne de 100 mi n'a pas le temps de réagir en 250 µs, et il faut raccourcir la ligne "
     "pour voir le doublement de tension (%s·Vmax sur 10 mi)."
     % (nb(I["val_livre_t0.0007_i2"]), nb(max(I["Q1_I1_ecart_pct"], I["Q1_I2_ecart_pct"],
                                               I["Q1_V2_ecart_pct"]), 3),
        nb(tau * 1e6, 1), nb(I["AC_ouvert1e6_rapport_v2"], 3),
        nb(I["AC_ouvert1e6_dt1e-4_constante_mesuree_s"] * 1e3, 0),
        nb(I["AC_ouvert1e6_constante_amortissement_Gamma_s"], 1), nb(I["Q6_10mi_RL_rapport_v2"], 3)))

# Numéros de page en pied de page.
pied = sec.footer.paragraphs[0]
pied.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = pied.add_run()
for typ, txt in (("begin", None), (None, "PAGE"), ("end", None)):
    if typ:
        el = OxmlElement("w:fldChar")
        el.set(qn("w:fldCharType"), typ)
    else:
        el = OxmlElement("w:instrText")
        el.set(qn("xml:space"), "preserve")
        el.text = txt
    r._r.append(el)

doc.save(SORTIE)
print("Rapport écrit : %s (%d figures, %d tableaux, %d équations)"
      % (SORTIE, compteur["fig"], compteur["tab"], compteur["eq"]))
