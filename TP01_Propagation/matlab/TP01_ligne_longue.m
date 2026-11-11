% TP 01 - Propagation dans les lignes électriques
% Module : Réseaux Électriques - ENP Alger
% Étudiant : NOM Prénom
% Groupe   : ...
% Date     : ...

clear; close all; clc;

dossier_tp  = fileparts(fileparts(mfilename('fullpath')));
dossier_fig = fullfile(dossier_tp, 'figures', 'matlab');
dossier_res = fullfile(dossier_tp, 'resultats', 'matlab');
if ~exist(dossier_fig, 'dir'), mkdir(dossier_fig); end
if ~exist(dossier_res, 'dir'), mkdir(dossier_res); end
visible_fig = 'on';

f  = 60;
w  = 2*pi*f;
Vm = 230000*sqrt(2)/sqrt(3);            % amplitude de la tension simple
source_ac = @(t) Vm*cos(w*t);
source_dc = @(t) 230000*ones(size(t));

% Données de l'énoncé : ligne de 100 mi, charge R-L, pas de 0,1 ms.
p0.Lp = 1.5e-3;                         % H/mi
p0.Cp = 0.02e-6;                        % F/mi
p0.d  = 100;                            % mi
p0.R  = 400;                            % ohm
p0.L  = 0.25;                           % H
p0.dt = 1e-4;                           % s
p0.T  = 5;                              % s
p0.t_ferm = 1e-4;                       % fermeture de l'interrupteur
p0.source = source_ac;
p0.mode_retard = 'interpolation';       % ou 'arrondi'
p0.tau_impose = NaN;                    % NaN : tau calculé à partir de L' et C'
p0.couper_historique = true;            % false : interpolation à travers la fermeture

ind = cell(0, 2);                       % grandeurs exportées vers indicateurs.csv

% Contrôle par rapport au livre (tau = 0,00055 s comme dans la solution).
instants = (1:10)*1e-4;
pv = p0; pv.T = 1e-3; pv.tau_impose = 0.00055;
rv = simuler_ligne(pv);
tab_livre = tableau_validation(rv, instants);
afficher_tableau('Validation, tau = 0.00055 s (livre)', tab_livre);
pe = p0; pe.T = 1e-3;
re = simuler_ligne(pe);
tab_exact = tableau_validation(re, instants);
afficher_tableau(sprintf('Validation, tau exact = %.4e s', re.tau), tab_exact);
fid = fopen(fullfile(dossier_res, 'validation_livre.csv'), 'w');
fprintf(fid, 'tau,t_s,i1_A,v1_V,i2_A,v2_V\n');
for k = 1:size(tab_livre, 1)
    fprintf(fid, '0.00055,%.4f,%.6g,%.8g,%.6g,%.8g\n', tab_livre(k, :));
end
for k = 1:size(tab_exact, 1)
    fprintf(fid, 'exact,%.4f,%.6g,%.8g,%.6g,%.8g\n', tab_exact(k, :));
end
fclose(fid);

pp = pv; pp.couper_historique = false;
rp = simuler_ligne(pp);
tab_piege = tableau_validation(rp, [6e-4 7e-4]);
afficher_tableau('Sans coupure de l''historique à la fermeture (tau = 0.00055 s)', tab_piege);
ind(end+1, :) = {'piege_i2_0p0006', tab_piege(1, 4)};
ind(end+1, :) = {'piege_i2_0p0007', tab_piege(2, 4)};
ind(end+1, :) = {'piege_v2_0p0007', tab_piege(2, 5)};
for k = 1:size(tab_livre, 1)
    nom = sprintf('val_livre_t%.4f', tab_livre(k, 1));
    ind(end+1, :) = {[nom '_i1'], tab_livre(k, 2)};
    ind(end+1, :) = {[nom '_v1'], tab_livre(k, 3)};
    ind(end+1, :) = {[nom '_i2'], tab_livre(k, 4)};
    ind(end+1, :) = {[nom '_v2'], tab_livre(k, 5)};
end

Zc = re.Zc; tau = re.tau; vp = re.vp; Req = re.Req;
ind(end+1, :) = {'Zc_ohm', Zc};
ind(end+1, :) = {'vp_mi_s', vp};
ind(end+1, :) = {'tau_s', tau};
ind(end+1, :) = {'tau_sur_dt', tau/p0.dt};
ind(end+1, :) = {'Req_ohm', Req};
fprintf('Zc = %.4f ohm, vp = %.1f mi/s, tau = %.4e s, tau/dt = %.4f, Req = %.1f ohm\n', ...
        Zc, vp, tau, tau/p0.dt, Req);

% Coefficients de réflexion des charges résistives étudiées.
for R = [400 999 1e6 0.001]
    G = coefficient_reflexion(R, Zc);
    ind(end+1, :) = {sprintf('Gamma_R_%g', R), G};
    fprintf('Gamma(R = %g ohm) = %.6f\n', R, G);
end
G_front = coefficient_reflexion(400 + Req, Zc);
ind(end+1, :) = {'Gamma_front_RL_discret', G_front};
fprintf('Gamma vu par le front d''onde (R + Req = %.0f ohm) = %.4f\n', 400 + Req, G_front);

% Charges : nom, R, L, nom de fichier.
charges = {'RL', 400, 0.25, 'RL'; 'ouvert999', 999, 0.001, 'ouvert_999'; ...
           'ouvert1e6', 1e6, 0.001, 'ouvert_1e6'; 'cc', 0.001, 0.001, 'cc'; ...
           'ccR', 0.001, 0, 'cc_R'};
prefixe_ac = {'Q1', 'Q2', 'Q2', 'Q3'};

sources = {'AC', source_ac, Vm; 'DC', source_dc, 230000};
resultats = struct();
for is = 1:2
    for ic = 1:4
        p = p0; p.R = charges{ic, 2}; p.L = charges{ic, 3}; p.source = sources{is, 2};
        r = simuler_ligne(p);
        cle = [sources{is, 1} '_' charges{ic, 1}];
        resultats.(cle) = r;
        q = indicateurs(r, sources{is, 3});
        ind(end+1, :) = {[cle '_t_arrivee'], q.t_arrivee};
        ind(end+1, :) = {[cle '_crete_v2'], q.crete_v2};
        ind(end+1, :) = {[cle '_rapport_v2'], q.rapport_v2};
        ind(end+1, :) = {[cle '_crete_i1'], q.crete_i1};
        ind(end+1, :) = {[cle '_crete_i2'], q.crete_i2};
        fprintf(['%s %-9s : arrivée en m à t = %.4f ms (t - t_ferm = %.4f ms), ' ...
                 '|v2|max = %.1f kV, rapport = %.3f, |i1|max = %.0f A, |i2|max = %.0f A\n'], ...
                sources{is, 1}, charges{ic, 1}, q.t_arrivee*1e3, (q.t_arrivee - p0.t_ferm)*1e3, ...
                q.crete_v2/1e3, q.rapport_v2, q.crete_i1, q.crete_i2);
        if is == 1
            ecrire_csv(fullfile(dossier_res, [prefixe_ac{ic} '_' charges{ic, 4} '.csv']), r);
        else
            ecrire_csv(fullfile(dossier_res, ['Q5_DC_' charges{ic, 4} '.csv']), r);
        end
    end
end

% Régime permanent Q1 : comparaison avec le calcul par phaseurs (quadripôle ABCD).
r = resultats.AC_RL;
ph = phaseurs_regime_permanent(p0, Vm, w);
sel = r.t >= 4;
noms = {'I1', 'I2', 'V2'};
Xs = [ajuster_sinus(r.t(sel), r.i1(sel), w), ajuster_sinus(r.t(sel), r.i2(sel), w), ...
      ajuster_sinus(r.t(sel), r.v2(sel), w)];
Xp = [ph.I1, ph.I2, ph.V2];
for k = 1:3
    ecart = abs(abs(Xs(k)) - abs(Xp(k)))/abs(Xp(k))*100;
    ind(end+1, :) = {['Q1_' noms{k} '_sim_amp'], abs(Xs(k))};
    ind(end+1, :) = {['Q1_' noms{k} '_phaseur_amp'], abs(Xp(k))};
    ind(end+1, :) = {['Q1_' noms{k} '_sim_phase_deg'], angle(Xs(k))*180/pi};
    ind(end+1, :) = {['Q1_' noms{k} '_phaseur_phase_deg'], angle(Xp(k))*180/pi};
    ind(end+1, :) = {['Q1_' noms{k} '_ecart_pct'], ecart};
    fprintf(['Q1 régime permanent %s : simulation %.2f /%.3f deg, phaseur %.2f /%.3f deg, ' ...
             'écart %.3f %%\n'], noms{k}, abs(Xs(k)), angle(Xs(k))*180/pi, abs(Xp(k)), ...
            angle(Xp(k))*180/pi, ecart);
end
i2_ref = abs(ph.I2)*cos(w*r.t + angle(ph.I2));
k = find(abs(r.i2 - i2_ref) > 0.01*abs(ph.I2), 1, 'last');
t_trans = r.t(k);
ind(end+1, :) = {'Q1_duree_transitoire_1pct_s', t_trans};
fprintf('Q1 : |i2 - i2_phaseur| < 1 %% de |I2| après t = %.4f s\n', t_trans);

% Interpolation contre arrondi du retard (20 premières ms).
pa = p0; pa.T = 0.02; pa.mode_retard = 'arrondi';
pi_ = p0; pi_.T = 0.02;
ra = simuler_ligne(pa);
ri = simuler_ligne(pi_);
dv2 = max(abs(ra.v2 - ri.v2));
di2 = max(abs(ra.i2 - ri.i2));
ind(end+1, :) = {'arrondi_tau_eff_s', ra.tau_eff};
ind(end+1, :) = {'arrondi_max_dv2_V', dv2};
ind(end+1, :) = {'arrondi_max_di2_A', di2};
fprintf('Arrondi : tau_eff = %.4e s ; max|dv2| = %.1f V (%.2f %% de Vm), max|di2| = %.2f A\n', ...
        ra.tau_eff, dv2, dv2/Vm*100, di2);
ecrire_csv(fullfile(dossier_res, 'Q1_RL_arrondi_20ms.csv'), ra);
ecrire_csv(fullfile(dossier_res, 'Q1_RL_interp_20ms.csv'), ri);

% Cas extrêmes : crête au début et à la fin de la simulation.
for ch = {'ouvert999', 'ouvert1e6', 'cc'}
    rr = resultats.(['AC_' ch{1}]);
    dern = rr.t >= 4;
    prem = rr.t <= 0.05;
    a1 = max(abs(rr.v2(prem))); a2 = max(abs(rr.v2(dern)));
    a3 = max(abs(rr.i2(dern))); a4 = max(abs(rr.i1(dern)));
    ind(end+1, :) = {['AC_' ch{1} '_v2max_0_50ms'], a1};
    ind(end+1, :) = {['AC_' ch{1} '_v2max_4_5s'], a2};
    ind(end+1, :) = {['AC_' ch{1} '_i2max_4_5s'], a3};
    ind(end+1, :) = {['AC_' ch{1} '_i1max_4_5s'], a4};
    fprintf(['AC %-9s : |v2|max sur 0-50 ms = %.1f kV, sur 4-5 s = %.1f kV ; ' ...
             '|i1|max 4-5 s = %.0f A, |i2|max 4-5 s = %.0f A\n'], ch{1}, a1/1e3, a2/1e3, a4, a3);
end

% Part physique et part numérique de l'amortissement : écart au régime permanent
% sur 4-5 s, avec dt = 1e-4 s (retard interpolé) et avec dt = tau/5 (retard exact).
dt_N = tau/5;
res_N = struct();
for ic = 2:4
    ch = charges{ic, 1};
    p = p0; p.R = charges{ic, 2}; p.L = charges{ic, 3};
    G = coefficient_reflexion(p.R, Zc);
    t_amort = 2*tau/(-log(abs(G)));
    ind(end+1, :) = {['AC_' ch '_constante_amortissement_Gamma_s'], t_amort};
    for variante = 1:2
        if variante == 1
            lab = 'dt1e-4';
            rr = resultats.(['AC_' ch]);
        else
            lab = 'dtTauSur5';
            p.dt = dt_N;
            rr = simuler_ligne(p);
            res_N.(ch) = rr;
        end
        [rv2, ri1] = residu_regime_permanent(rr, p, Vm, w);
        ind(end+1, :) = {['AC_' ch '_' lab '_residu_v2_4_5s'], rv2};
        ind(end+1, :) = {['AC_' ch '_' lab '_residu_i1_4_5s'], ri1};
        fprintf(['AC %-9s %-9s : écart au régime permanent sur 4-5 s, v2 : %.0f V, ' ...
                 'i1 : %.1f A (constante d''amortissement 2tau/(-ln|Gamma|) = %.4g s)\n'], ...
                ch, lab, rv2, ri1, t_amort);
    end
end
ind(end+1, :) = {'dt_tau_sur_5_s', dt_N};
% Constante de temps mesurée sur l'enveloppe (pente en échelle log).
pq = p0; pq.R = 1e6; pq.L = 0.001;
variantes = {'dt1e-4', resultats.AC_ouvert1e6, 1e-4, 0.02, 0.4; ...
             'dtTauSur5', res_N.ouvert1e6, dt_N, 0.5, 4.5};
for k = 1:2
    pq.dt = variantes{k, 3};
    [tc, env] = enveloppe_ecart(variantes{k, 2}, pq, Vm, w, 0.02);
    sel = tc > variantes{k, 4} & tc < variantes{k, 5};
    c = polyfit(tc(sel), log(env(sel)), 1);
    ind(end+1, :) = {['AC_ouvert1e6_' variantes{k, 1} '_constante_mesuree_s'], -1/c(1)};
    fprintf('AC ouvert1e6 %-9s : constante de temps de l''enveloppe mesurée = %.4g s\n', ...
            variantes{k, 1}, -1/c(1));
end
rr = resultats.AC_cc;
ind(end+1, :) = {'AC_cc_moyenne_i1_4_5s', mean(rr.i1(rr.t >= 4))};
n_arr = find(abs(rr.v2) > 1e-6*Vm, 1);
ind(end+1, :) = {'AC_cc_v2_n_arr', rr.v2(n_arr)};
ind(end+1, :) = {'AC_cc_v2_n_arr_plus1', rr.v2(n_arr+1)};
ind(end+1, :) = {'AC_cc_v2_n_arr_plus2', rr.v2(n_arr+2)};
ind(end+1, :) = {'Gamma_front_cc_discret', coefficient_reflexion(0.001 + 2*0.001/p0.dt, Zc)};
fprintf(['AC cc : v2 aux trois premiers pas après l''arrivée : %.0f, %.0f, %.0f V ; ' ...
         'moyenne de i1 sur 4-5 s = %.1f A\n'], rr.v2(n_arr), rr.v2(n_arr+1), rr.v2(n_arr+2), ...
        mean(rr.i1(rr.t >= 4)));

for ch = {'RL', 'ouvert999', 'cc'}
    rr = resultats.(['DC_' ch{1}]);
    ind(end+1, :) = {['DC_' ch{1} '_v2_final'], rr.v2(end)};
    ind(end+1, :) = {['DC_' ch{1} '_i2_final'], rr.i2(end)};
    ind(end+1, :) = {['DC_' ch{1} '_i1_final'], rr.i1(end)};
    fprintf('DC %-9s : à t = 5 s, v2 = %.1f kV, i2 = %.1f A, i1 = %.1f A\n', ch{1}, ...
            rr.v2(end)/1e3, rr.i2(end), rr.i1(end));
end

% Onde de choc de foudre 1,2/50 us : forme brute, correction de crête, mesures.
Vmax = 230000; tau1 = 1.2e-6; tau2 = 50e-6; nf = 3;
tf = 0:1e-9:250e-6;
[v_brut, mb] = onde_foudre(tf, Vmax, tau1, tau2, nf, 1);
eta = Vmax/mb.Vc;
[v_corr, mc] = onde_foudre(tf, Vmax, tau1, tau2, nf, eta);
ind(end+1, :) = {'foudre_crete_brute_V', mb.Vc};
ind(end+1, :) = {'foudre_t_crete_s', mb.tc};
ind(end+1, :) = {'foudre_eta', eta};
ind(end+1, :) = {'foudre_T1_s', mb.T1};
ind(end+1, :) = {'foudre_T2_s', mb.T2};
ind(end+1, :) = {'foudre_t30_s', mb.t30};
ind(end+1, :) = {'foudre_t90_s', mb.t90};
ind(end+1, :) = {'foudre_O1_s', mb.O1};
ind(end+1, :) = {'foudre_t50_s', mb.t50};
ind(end+1, :) = {'foudre_crete_corrigee_V', mc.Vc};
fprintf(['Foudre : crête brute %.1f kV à t = %.3f us, eta = %.5f ; T1 = %.3f us, ' ...
         'T2 = %.2f us (origine O1 = %.3f us, t50 = %.2f us)\n'], mb.Vc/1e3, mb.tc*1e6, eta, ...
        mb.T1*1e6, mb.T2*1e6, mb.O1*1e6, mb.t50*1e6);

fig = figure('Visible', visible_fig);
plot(tf*1e6, v_brut/1e3, tf*1e6, v_corr/1e3); hold on;
plot([0 250], [Vmax Vmax]/1e3, 'k:');
grid on;
xlabel('t (\mus)'); ylabel('v_s(t) (kV)');
title('Onde de choc de foudre 1,2/50 \mus, n = 3');
legend('formule brute (\eta = 1)', sprintf('corrigée (\\eta = %.4f)', eta), 'Location', 'northeast');
sauver_figure(fig, fullfile(dossier_fig, 'Q6a_onde_foudre'), 16, 9);
M = [tf(1:10:end); v_brut(1:10:end); v_corr(1:10:end)];
fid = fopen(fullfile(dossier_res, 'Q6a_onde_foudre.csv'), 'w');
fprintf(fid, 't_s,v_brut_V,v_corrige_V\n');
fprintf(fid, '%.10g,%.10g,%.10g\n', M);
fclose(fid);

% Ligne de 100 mi soumise au choc : dt = 60 ns, fenêtre de 250 us.
pf = p0; pf.dt = 60e-9; pf.T = 250e-6; pf.t_ferm = 0;
pf.source = @(t) onde_foudre(t, Vmax, tau1, tau2, nf, eta);
res_f = struct();
for ic = [1 2 4]
    p = pf; p.R = charges{ic, 2}; p.L = charges{ic, 3};
    res_f.(charges{ic, 1}) = simuler_ligne(p);
end
r = res_f.RL;
ecart_i1 = max(abs(r.i1 - r.vs/r.Zc));
dmax_ch = max([max(abs(res_f.ouvert999.i1 - r.i1)), max(abs(res_f.cc.i1 - r.i1))]);
ind(end+1, :) = {'Q6_100mi_max_abs_v2', max(abs(r.v2))};
ind(end+1, :) = {'Q6_100mi_max_abs_i2', max(abs(r.i2))};
ind(end+1, :) = {'Q6_100mi_max_ecart_i1_vs_sur_Zc', ecart_i1};
ind(end+1, :) = {'Q6_100mi_max_i1', max(r.i1)};
ind(end+1, :) = {'Q6_100mi_ecart_entre_charges_i1', dmax_ch};
ind(end+1, :) = {'Q6_100mi_nb_pas', numel(r.t) - 1};
fprintf(['Foudre, 100 mi : max|v2| = %g V, max|i2| = %g A, max|i1 - vs/Zc| = %.3g A, ' ...
         'i1 max = %.1f A, écart entre charges %.3g A, %d pas\n'], max(abs(r.v2)), ...
        max(abs(r.i2)), ecart_i1, max(r.i1), dmax_ch, numel(r.t) - 1);
ecrire_csv(fullfile(dossier_res, 'Q6_foudre_100mi_RL.csv'), r);
tracer_cas({r}, {'charge R-L'}, ...
           sprintf('Choc de foudre, ligne de 100 mi (\\tau = %.1f \\mus > 250 \\mus)', r.tau*1e6), ...
           fullfile(dossier_fig, 'Q6b_foudre_100mi'), Inf, 'us', visible_fig);

% Extension : ligne de 10 mi, les réflexions apparaissent dans la fenêtre de 250 us.
res_10 = struct();
for ic = [1 2 4 5]
    ch = charges{ic, 1};
    p = pf; p.d = 10; p.R = charges{ic, 2}; p.L = charges{ic, 3};
    rr = simuler_ligne(p);
    res_10.(ch) = rr;
    q = indicateurs(rr, Vmax);
    ind(end+1, :) = {['Q6_10mi_' ch '_t_arrivee'], q.t_arrivee};
    ind(end+1, :) = {['Q6_10mi_' ch '_crete_v2'], q.crete_v2};
    ind(end+1, :) = {['Q6_10mi_' ch '_rapport_v2'], q.rapport_v2};
    ind(end+1, :) = {['Q6_10mi_' ch '_crete_i2'], q.crete_i2};
    ind(end+1, :) = {['Q6_10mi_' ch '_crete_i1'], q.crete_i1};
    fprintf(['Foudre, 10 mi, %-9s : arrivée %.3f us (tau = %.3f us), |v2|max = %.1f kV ' ...
             '(rapport %.3f), |i2|max = %.0f A, |i1|max = %.0f A\n'], ch, q.t_arrivee*1e6, ...
            rr.tau*1e6, q.crete_v2/1e3, q.rapport_v2, q.crete_i2, q.crete_i1);
    ecrire_csv(fullfile(dossier_res, ['Q6_foudre_10mi_' charges{ic, 4} '.csv']), rr);
end
ind(end+1, :) = {'Q6_10mi_tau_s', res_10.RL.tau};
tracer_cas({res_10.RL, res_10.ouvert999, res_10.cc, res_10.ccR}, ...
           {'R-L', 'R = 999 \Omega', 'R = L = 0,001', 'R = 0,001, L = 0'}, ...
           sprintf('Choc de foudre, ligne de 10 mi (\\tau = %.2f \\mus)', res_10.RL.tau*1e6), ...
           fullfile(dossier_fig, 'Q6c_foudre_10mi'), Inf, 'us', visible_fig);

% Figures des cas sinusoïdaux et continus.
F = fullfile(dossier_fig, '');
tracer_cas({resultats.AC_RL}, {'R-L'}, 'Q1 : charge R-L, source alternative, 0-5 s', ...
           fullfile(F, 'Q1_RL_5s'), Inf, 'ms', visible_fig);
tracer_cas({resultats.AC_RL}, {'R-L'}, 'Q1 : charge R-L, 10 premières ms', ...
           fullfile(F, 'Q1_RL_zoom'), 0.01, 'ms', visible_fig);
tracer_cas({ra, ri}, {'\tau arrondi à 5\Deltat', '\tau interpolé'}, ...
           'Q1 : arrondi et interpolation du retard, 10 premières ms', ...
           fullfile(F, 'Q1_RL_arrondi_interp'), 0.01, 'ms', visible_fig);
tracer_cas({resultats.AC_ouvert999, resultats.AC_ouvert1e6}, {'R = 999 \Omega', 'R = 10^6 \Omega'}, ...
           'Q2 : extrémité ouverte, 0-5 s', fullfile(F, 'Q2_ouvert_5s'), Inf, 'ms', visible_fig);
tracer_cas({resultats.AC_ouvert999, resultats.AC_ouvert1e6}, {'R = 999 \Omega', 'R = 10^6 \Omega'}, ...
           'Q2 : extrémité ouverte, 20 premières ms', fullfile(F, 'Q2_ouvert_zoom'), 0.02, 'ms', ...
           visible_fig);
tracer_cas({resultats.AC_cc}, {'R = L = 0,001'}, 'Q3 : extrémité en court-circuit, 0-5 s', ...
           fullfile(F, 'Q3_cc_5s'), Inf, 'ms', visible_fig);
tracer_cas({resultats.AC_cc}, {'R = L = 0,001'}, 'Q3 : court-circuit, 20 premières ms', ...
           fullfile(F, 'Q3_cc_zoom'), 0.02, 'ms', visible_fig);
tracer_cas({resultats.DC_RL, resultats.DC_ouvert999}, {'R-L', 'R = 999 \Omega'}, ...
           'Q5 : source continue 230 kV, 0-5 s', fullfile(F, 'Q5_DC_RL_ouvert_5s'), Inf, 'ms', ...
           visible_fig);
tracer_cas({resultats.DC_RL, resultats.DC_ouvert999, resultats.DC_cc}, ...
           {'R-L', 'R = 999 \Omega', 'court-circuit'}, ...
           'Q5 : source continue 230 kV, 10 premières ms', fullfile(F, 'Q5_DC_zoom'), 0.01, 'ms', ...
           visible_fig);
tracer_cas({resultats.DC_cc}, {'R = L = 0,001'}, 'Q5 : source continue, court-circuit, 0-5 s', ...
           fullfile(F, 'Q5_DC_cc_5s'), Inf, 'ms', visible_fig);
pa1 = p0; pa1.R = 1e6; pa1.L = 0.001;
pa2 = pa1; pa2.dt = dt_N;
pc1 = p0; pc1.R = 0.001; pc1.L = 0.001;
pc2 = pc1; pc2.dt = dt_N;
tracer_amortissement({{resultats.AC_ouvert1e6, pa1; res_N.ouvert1e6, pa2}, ...
                      {resultats.AC_cc, pc1; res_N.cc, pc2}}, ...
                     {'Extrémité ouverte, R = 10^6 \Omega', 'Court-circuit, R = L = 0,001'}, ...
                     {'\Deltat = 0,1 ms (retard interpolé)', '\Deltat = \tau/5 (retard exact)'}, ...
                     fullfile(F, 'Q4_amortissement'), Vm, w, visible_fig);

% Vérification croisée avec Simulink (fichier produit par construire_modele_simulink.m).
fichier_slx = fullfile(dossier_tp, 'resultats', 'simulink_Q1.mat');
if exist(fichier_slx, 'file')
    S = load(fichier_slx);
    r = resultats.AC_RL;
    fig = figure('Visible', visible_fig);
    grandeurs = {'i1', 'i2', 'v1', 'v2'};
    unites = {'i_1 (A)', 'i_2 (A)', 'v_1 (kV)', 'v_2 (kV)'};
    gains = [1 1 1e-3 1e-3];
    sel = r.t <= 0.02;
    for k = 1:4
        subplot(2, 2, k);
        plot(r.t(sel)*1e3, r.(grandeurs{k})(sel)*gains(k)); hold on;
        selS = S.t <= 0.02;
        plot(S.t(selS)*1e3, S.(grandeurs{k})(selS)*gains(k), '--');
        grid on; xlabel('t (ms)'); ylabel(unites{k});
        if k == 1, legend('Bergeron + trapèzes (script)', 'Simulink'); end
        ecart = max(abs(r.(grandeurs{k})(sel) - interp1(S.t, S.(grandeurs{k}), r.t(sel))));
        ind(end+1, :) = {['simulink_ecart_' grandeurs{k} '_20ms'], ecart};
        fprintf('Écart script / Simulink sur 20 ms, %s : %.4g\n', grandeurs{k}, ecart);
    end
    titre_figure('Q1 : comparaison script / Simulink, 20 premières ms');
    sauver_figure(fig, fullfile(dossier_fig, 'Q1_comparaison_simulink'), 20, 14);
    fprintf('Comparaison Simulink tracée (%s).\n', fichier_slx);
end

fid = fopen(fullfile(dossier_res, 'indicateurs.csv'), 'w');
fprintf(fid, 'grandeur,valeur\n');
for k = 1:size(ind, 1)
    fprintf(fid, '%s,%.10g\n', ind{k, 1}, ind{k, 2});
end
fclose(fid);
fprintf('Résultats écrits dans %s\n', dossier_res);


% Fonctions locales.

function tab = tableau_validation(res, instants)
% Lignes [t i1 v1 i2 v2] aux instants demandés.
tab = zeros(numel(instants), 5);
for k = 1:numel(instants)
    n = round(instants(k)/(res.t(2) - res.t(1))) + 1;
    tab(k, :) = [res.t(n), res.i1(n), res.v1(n), res.i2(n), res.v2(n)];
end
end

function afficher_tableau(titre, tab)
fprintf('%s\n', titre);
fprintf('   t (s)      i1 (A)        v1 (V)      i2 (A)        v2 (V)\n');
for k = 1:size(tab, 1)
    fprintf('%8.4f %11.2f %13.0f %11.2f %13.0f\n', tab(k, :));
end
end

function G = coefficient_reflexion(ZL, Zc)
G = (ZL - Zc)/(ZL + Zc);
end

function ph = phaseurs_regime_permanent(p, Vm, w)
% Ligne en quadripôle ABCD (sans pertes) fermée sur Z = R + jwL.
Zc = sqrt(p.Lp/p.Cp);
bd = w*p.d*sqrt(p.Lp*p.Cp);
A = cos(bd); B = 1i*Zc*sin(bd); C = 1i*sin(bd)/Zc; D = A;
ZL = p.R + 1i*w*p.L;
V1 = Vm;
I2 = V1/(A*ZL + B);
V2 = ZL*I2;
I1 = C*V2 + D*I2;
ph = struct('V1', V1, 'I1', I1, 'V2', V2, 'I2', I2);
end

function X = ajuster_sinus(t, x, w)
% Moindres carrés x = a.cos(wt) + b.sin(wt) + c ; renvoie le phaseur a - jb.
M = [cos(w*t(:)), sin(w*t(:)), ones(numel(t), 1)];
coef = M\x(:);
X = coef(1) - 1i*coef(2);
end

function [rv2, ri1] = residu_regime_permanent(res, p, Vm, w)
% Plus grand écart entre la simulation et la solution par phaseurs pour t >= 4 s.
ph = phaseurs_regime_permanent(p, Vm, w);
s = res.t >= 4;
v2p = abs(ph.V2)*cos(w*res.t(s) + angle(ph.V2));
i1p = abs(ph.I1)*cos(w*res.t(s) + angle(ph.I1));
rv2 = max(abs(res.v2(s) - v2p));
ri1 = max(abs(res.i1(s) - i1p));
end

function q = indicateurs(res, amplitude_source)
% Arrivée de l'onde en m (v2 ou Zc.i2 hors du bruit numérique), crêtes.
seuil = 1e-6*amplitude_source;
k = find(abs(res.v2) > seuil | res.Zc*abs(res.i2) > seuil, 1);
if isempty(k)
    q.t_arrivee = NaN;
else
    q.t_arrivee = res.t(k);
end
q.crete_v2 = max(abs(res.v2));
q.rapport_v2 = q.crete_v2/amplitude_source;
q.crete_i1 = max(abs(res.i1));
q.crete_i2 = max(abs(res.i2));
end

function ecrire_csv(chemin, res)
fid = fopen(chemin, 'w');
fprintf(fid, 't_s,vs_V,v1_V,i1_A,v2_V,i2_A\n');
fprintf(fid, '%.10g,%.10g,%.10g,%.10g,%.10g,%.10g\n', [res.t; res.vs; res.v1; res.i1; res.v2; res.i2]);
fclose(fid);
end

function [tc, env] = enveloppe_ecart(res, p, Vm, w, fenetre)
% Maximum de |v2 - v2 phaseur| sur des fenêtres successives de durée fenetre.
ph = phaseurs_regime_permanent(p, Vm, w);
e = abs(res.v2 - abs(ph.V2)*cos(w*res.t + angle(ph.V2)));
m = round(fenetre/p.dt);
nb = floor((numel(e) - 1)/m);
env = zeros(1, nb);
for k = 1:nb
    env(k) = max(e(2 + (k-1)*m : 1 + k*m));
end
tc = ((0:nb-1) + 0.5)*m*p.dt;
end

function tracer_amortissement(cas, titres, legendes, chemin, Vm, w, visible_fig)
% Enveloppe de l'écart au régime permanent (échelle log) pour chaque cas.
fig = figure('Visible', visible_fig);
for c = 1:numel(cas)
    subplot(1, numel(cas), c);
    liste = cas{c};
    for m = 1:size(liste, 1)
        [tc, env] = enveloppe_ecart(liste{m, 1}, liste{m, 2}, Vm, w, 0.02);
        semilogy(tc, env/1e3); hold on;
    end
    hold off;
    xlim([0, liste{1, 1}.t(end)]);
    grid on; box on;
    xlabel('t (s)'); ylabel('max |v_2 - v_{2,phaseur}| sur 20 ms (kV)'); title(titres{c});
    legend(legendes, 'Location', 'southwest');
end
sauver_figure(fig, chemin, 28, 11);
end

function titre_figure(titre)
if exist('sgtitle', 'file') || exist('sgtitle', 'builtin')
    sgtitle(titre);
else
    annotation('textbox', [0 0.965 1 0.035], 'String', titre, 'EdgeColor', 'none', ...
               'HorizontalAlignment', 'center', 'FontWeight', 'bold');
end
end

function sauver_figure(fig, chemin, largeur_cm, hauteur_cm)
set(fig, 'PaperUnits', 'centimeters', 'PaperSize', [largeur_cm hauteur_cm], ...
    'PaperPosition', [0 0 largeur_cm hauteur_cm]);
print(fig, [chemin '.png'], '-dpng', '-r300');
print(fig, [chemin '.pdf'], '-dpdf');
end

function tracer_cas(liste_res, legendes, titre, chemin, t_max, unite_t, visible_fig)
% Figure 2x2 : i1, i2 (A) et v1, v2 (kV) en fonction du temps.
if strcmp(unite_t, 'ms')
    ech = 1e3; lab_t = 't (ms)';
else
    ech = 1e6; lab_t = 't (\mus)';
end
grandeurs = {'i1', 'i2', 'v1', 'v2'};
etiquettes = {'i_1(t) (A)', 'i_2(t) (A)', 'v_1(t) (kV)', 'v_2(t) (kV)'};
titres = {'Courant au départ i_1', 'Courant à l''arrivée i_2', 'Tension au départ v_1', ...
          'Tension à l''arrivée v_2'};
gains = [1 1 1e-3 1e-3];
fig = figure('Visible', visible_fig);
for k = 1:4
    subplot(2, 2, k);
    hold on;
    for m = 1:numel(liste_res)
        r = liste_res{m};
        sel = r.t <= t_max + 1e-12;
        plot(r.t(sel)*ech, r.(grandeurs{k})(sel)*gains(k));
    end
    hold off;
    xlim([0, min(t_max, r.t(end))*ech]);
    grid on; box on;
    xlabel(lab_t); ylabel(etiquettes{k}); title(titres{k});
    if numel(liste_res) > 1
        legend(legendes, 'Location', 'best');
    end
end
titre_figure(titre);
sauver_figure(fig, chemin, 25, 17.5);
end

function res = simuler_ligne(p)
% Ligne monophasée sans pertes (modèle de Bergeron) fermée sur une charge R-L
% (règle des trapèzes), pas de temps fixe dt.
%
% Champs de p : Lp, Cp (par mile), d, R, L, dt, T, t_ferm, source (fonction de t),
%               mode_retard ('interpolation' ou 'arrondi'), tau_impose (NaN si calculé),
%               couper_historique (true : pas d'interpolation à travers la fermeture).
%
% i1 entre dans la ligne en k, i2 sort de la ligne en m vers la charge.

Zc  = sqrt(p.Lp/p.Cp);          % impédance caractéristique
vp  = 1/sqrt(p.Lp*p.Cp);        % vitesse de propagation
tau = p.d/vp;                   % temps de propagation
if ~isnan(p.tau_impose)
    tau = p.tau_impose;
end
dt = p.dt;
R  = p.R;
L  = p.L;

% Option « arrondi » : retard ramené au multiple de dt le plus proche.
k_tau = round(tau/dt);
if strcmp(p.mode_retard, 'arrondi')
    tau_eff = k_tau*dt;
else
    tau_eff = tau;
end
if tau_eff < dt
    error('Le temps de propagation doit dépasser le pas de calcul.');
end

% Modèle compagnon de l'inductance : Req en parallèle avec la source Ih.
if L > 0
    Req = 2*L/dt;
else
    Req = 0;
end

N  = round(p.T/dt);
t  = (0:N)*dt;
vs = p.source(t);
v1 = zeros(1, N+1);
i1 = zeros(1, N+1);
v2 = zeros(1, N+1);
i2 = zeros(1, N+1);
vL = zeros(1, N+1);
eps_t = 1e-9*dt;
if p.couper_historique
    t_lim = p.t_ferm;
else
    t_lim = 0;
end

for n = 2:N+1
    % Grandeurs vues à l'autre extrémité un temps de propagation plus tôt.
    ts = t(n) - tau_eff;
    if ts < t_lim - eps_t
        % Avant la fermeture la ligne est au repos : on n'interpole pas
        % à travers l'instant de manoeuvre.
        v1h = 0; i1h = 0; v2h = 0; i2h = 0;
    elseif strcmp(p.mode_retard, 'arrondi')
        j = n - k_tau;
        v1h = v1(j); i1h = i1(j); v2h = v2(j); i2h = i2(j);
    else
        s = ts/dt;
        j = floor(s);
        a = s - j;
        if a > 1 - 1e-9
            j = j + 1;
            a = 0;
        end
        j = j + 1;                      % indice MATLAB de l'échantillon t = j*dt
        v1h = v1(j) + a*(v1(j+1) - v1(j));
        i1h = i1(j) + a*(i1(j+1) - i1(j));
        v2h = v2(j) + a*(v2(j+1) - v2(j));
        i2h = i2(j) + a*(i2(j+1) - i2(j));
    end

    % Sources d'historique du modèle de Bergeron.
    Ik = i2h - v2h/Zc;      % onde réfléchie revenant vers k
    Im = v1h/Zc + i1h;      % onde incidente arrivant en m

    % Extrémité k : tension imposée par la source une fois l'interrupteur fermé.
    if t(n) >= p.t_ferm - eps_t
        v1(n) = vs(n);
        i1(n) = v1(n)/Zc + Ik;
    else
        i1(n) = 0;
        v1(n) = -Zc*Ik;
    end

    % Extrémité m : Zc // Im en série avec R et le compagnon Req // Ih.
    if L > 0
        Ih = i2(n-1) + vL(n-1)/Req;
    else
        Ih = 0;
    end
    i2(n) = (Im + Req*Ih/Zc)/(1 + (R + Req)/Zc);
    v2(n) = Zc*(Im - i2(n));
    vL(n) = v2(n) - R*i2(n);
end

res = struct('t', t, 'vs', vs, 'v1', v1, 'i1', i1, 'v2', v2, 'i2', i2, 'vL', vL, ...
             'Zc', Zc, 'vp', vp, 'tau', tau, 'tau_eff', tau_eff, 'Req', Req);
end

function [v, mes] = onde_foudre(t, Vmax, tau1, tau2, n, eta)
% Onde de choc de foudre :
%   vs(t) = eta.Vmax.(t/tau1)^n/(1+(t/tau1)^n).exp(-t/tau2), nulle pour t < 0.
% eta corrige la crête (la formule brute n'atteint pas Vmax).
% Avec deux sorties, mesure la crête, la durée de front et la durée jusqu'à mi-valeur
% sur la grille t fournie (à prendre fine, de l'ordre de la ns).

if nargin < 6
    eta = 1;
end
x = (max(t, 0)/tau1).^n;
v = eta*Vmax*x./(1 + x).*exp(-max(t, 0)/tau2);
if nargout > 1
    mes = mesurer_onde_choc(t, v);
end
end

function mes = mesurer_onde_choc(t, v)
% Durée de front T1 = 1,67.(t90 - t30), origine conventionnelle O1 = t30 - 0,3.T1,
% durée jusqu'à mi-valeur T2 = t50 - O1 (t50 sur la queue de l'onde).
[Vc, ic] = max(v);
tc  = t(ic);
t30 = franchissement(t(1:ic), v(1:ic), 0.3*Vc);
t90 = franchissement(t(1:ic), v(1:ic), 0.9*Vc);
T1  = 1.67*(t90 - t30);
O1  = t30 - 0.3*T1;
t50 = franchissement(t(ic:end), -v(ic:end), -0.5*Vc);
T2  = t50 - O1;
mes = struct('Vc', Vc, 'tc', tc, 't30', t30, 't90', t90, 'T1', T1, 'O1', O1, ...
             't50', t50, 'T2', T2);
end

function tx = franchissement(t, v, niveau)
% Premier instant où v atteint niveau, par interpolation linéaire.
k = find(v >= niveau, 1);
tx = t(k-1) + (niveau - v(k-1))*(t(k) - t(k-1))/(v(k) - v(k-1));
end
