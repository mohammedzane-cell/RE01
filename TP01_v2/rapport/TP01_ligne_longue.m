% TP 01 - Propagation dans les lignes electriques
% Reseaux Electriques - ENP Alger
% Nom Prenom :
% Groupe     :
%
% Ligne monophasee sans pertes (modele de Bergeron) + charge R-L
% (regle des trapezes). Les valeurs a t - tau sont obtenues par
% interpolation lineaire car tau n'est pas un multiple de dt.

clear; close all; clc;

% Donnees de la ligne
Lp = 1.5e-3;          % H/mi
Cp = 0.02e-6;         % F/mi
d  = 100;             % mi
Zc  = sqrt(Lp/Cp);
vp  = 1/sqrt(Lp*Cp);
tau = d/vp;
fprintf('Zc = %.2f ohm, vp = %.0f mi/s, tau = %.2f us\n', Zc, vp, tau*1e6);

Vm = 230e3*sqrt(2)/sqrt(3);
vs_ac = @(t) Vm*cos(2*pi*60*t);
vs_dc = @(t) 230e3*ones(size(t));

dt = 1e-4;  T = 5;  tf = 1e-4;     % pas, duree, fermeture de l'interrupteur

%% Verification avec la solution du livre (tau arrondi a 0.00055 s)
r = simuler(vs_ac, 0.00055, Zc, 400, 0.25, dt, 1e-3, tf);
fprintf('\n  t (ms)    i1 (A)     v1 (V)    i2 (A)     v2 (V)\n');
for tk = [1 2 7]
    fprintf('%6.1f %10.1f %10.0f %9.1f %10.0f\n', r.t(tk+1)*1e3, ...
            r.i1(tk+1), r.v1(tk+1), r.i2(tk+1), r.v2(tk+1));
end
% livre : 685 A / 187661 V a 0.1 ms ; 662 A, 66 A, 356731 V a 0.7 ms

%% Q1 : charge R-L, 5 s
rRL = simuler(vs_ac, tau, Zc, 400, 0.25, dt, T, tf);
if ~exist('figures', 'dir'), mkdir('figures'); end
tracer({rRL}, {'R-L'}, 'Q1 : charge R-L (0 - 5 s)', T, 'Q1_RL_5s');
tracer({rRL}, {'R-L'}, 'Q1 : charge R-L (10 premieres ms)', 0.01, 'Q1_RL_zoom');

% regime permanent par phaseurs (quadripole de la ligne + charge)
w  = 2*pi*60;  bl = w*d*sqrt(Lp*Cp);
ZL = 400 + 1i*w*0.25;
A = cos(bl); B = 1i*Zc*sin(bl); C = 1i*sin(bl)/Zc;
I2 = Vm/(A*ZL + B);  V2 = ZL*I2;  I1 = C*V2 + A*I2;
fin = rRL.t > 4.9;
fprintf('\nRegime permanent   simulation   phaseurs\n');
fprintf('|I1| (A)       %10.1f %10.1f\n', max(abs(rRL.i1(fin))), abs(I1));
fprintf('|I2| (A)       %10.1f %10.1f\n', max(abs(rRL.i2(fin))), abs(I2));
fprintf('|V2| (kV)      %10.1f %10.1f\n', max(abs(rRL.v2(fin)))/1e3, abs(V2)/1e3);

%% Q2 : extremite ouverte, Q3 : court-circuit
rO  = simuler(vs_ac, tau, Zc, 999, 0.001, dt, T, tf);
rO6 = simuler(vs_ac, tau, Zc, 1e6, 0.001, dt, T, tf);
rCC = simuler(vs_ac, tau, Zc, 0.001, 0.001, dt, T, tf);
tracer({rO, rO6}, {'R = 999 \Omega', 'R = 10^6 \Omega'}, 'Q2 : extremite ouverte (20 ms)', 0.02, 'Q2_ouvert_zoom');
tracer({rO, rO6}, {'R = 999 \Omega', 'R = 10^6 \Omega'}, 'Q2 : extremite ouverte (0 - 5 s)', T, 'Q2_ouvert_5s');
tracer({rCC}, {'R = L = 0.001'}, 'Q3 : court-circuit (20 ms)', 0.02, 'Q3_cc_zoom');
tracer({rCC}, {'R = L = 0.001'}, 'Q3 : court-circuit (0 - 5 s)', T, 'Q3_cc_5s');

for R = [400 999 1e6 0.001]
    fprintf('Gamma(R = %g) = %.4f\n', R, (R - Zc)/(R + Zc));
end
fprintf('max|v2| / Vm : ouvert 999 = %.2f, ouvert 1e6 = %.2f, cc = %.3f\n', ...
        max(abs(rO.v2))/Vm, max(abs(rO6.v2))/Vm, max(abs(rCC.v2))/Vm);

%% Q5 : source continue 230 kV
dRL = simuler(vs_dc, tau, Zc, 400, 0.25, dt, T, tf);
dO  = simuler(vs_dc, tau, Zc, 999, 0.001, dt, T, tf);
dCC = simuler(vs_dc, tau, Zc, 0.001, 0.001, dt, T, tf);
tracer({dRL, dO, dCC}, {'R-L', 'ouvert', 'court-circuit'}, 'Q5 : source continue (10 ms)', 0.01, 'Q5_DC_zoom');
tracer({dRL, dO}, {'R-L', 'ouvert'}, 'Q5 : source continue (0 - 5 s)', T, 'Q5_DC_5s');
tracer({dCC}, {'court-circuit'}, 'Q5 : source continue, court-circuit (0 - 5 s)', T, 'Q5_DC_cc_5s');
fprintf('\nQ5 a t = 5 s : v2 (kV) R-L = %.1f, ouvert = %.1f, cc = %.2f ; i2 (A) R-L = %.1f, ouvert = %.1f, cc = %.0f\n', ...
        dRL.v2(end)/1e3, dO.v2(end)/1e3, dCC.v2(end)/1e3, dRL.i2(end), dO.i2(end), dCC.i2(end));

%% Q6 : onde de choc de foudre 1,2/50 us
Vmax = 230e3;  t1 = 1.2e-6;  t2 = 50e-6;  n = 3;
choc = @(t) Vmax*(t/t1).^n./(1 + (t/t1).^n).*exp(-t/t2);
tt = 0:1e-9:250e-6;
[vc, kc] = max(choc(tt));
eta = Vmax/vc;               % la formule n'atteint pas Vmax, on corrige la crete
fprintf('\nChoc : crete %.1f kV a %.2f us, eta = %.4f\n', vc/1e3, tt(kc)*1e6, eta);

figure;
plot(tt*1e6, choc(tt)/1e3, tt*1e6, eta*choc(tt)/1e3); grid on;
xlabel('t (\mus)'); ylabel('v_s (kV)');
legend('formule de l''enonce', 'crete corrigee a 230 kV');
title('Q6a : onde de choc de foudre');
print(gcf, fullfile('figures', 'Q6a_onde'), '-dpng', '-r200');

choc_c = @(t) eta*choc(t);
dtf = 60e-9;  Tf = 250e-6;
fRL = simuler(choc_c, tau, Zc, 400, 0.25, dtf, Tf, 0);
tracer({fRL}, {'R-L'}, 'Q6 : choc de foudre, ligne de 100 mi', Tf, 'Q6_100mi');
% tau = 548 us > 250 us : l'onde n'arrive pas en m pendant la simulation
fprintf('Q6 100 mi : max|v2| = %g V, max|i2| = %g A\n', max(abs(fRL.v2)), max(abs(fRL.i2)));

% meme essai sur une ligne de 10 mi pour voir les reflexions
tau10 = 10/vp;
gRL = simuler(choc_c, tau10, Zc, 400, 0.25, dtf, Tf, 0);
gO  = simuler(choc_c, tau10, Zc, 999, 0.001, dtf, Tf, 0);
gCC = simuler(choc_c, tau10, Zc, 0.001, 0, dtf, Tf, 0);
tracer({gRL, gO, gCC}, {'R-L', 'R = 999 \Omega', 'court-circuit (R seule)'}, ...
       'Q6 : choc de foudre, ligne de 10 mi', Tf, 'Q6_10mi');
fprintf('Q6 10 mi, R-L : arrivee en m a %.2f us, max|v2| = %.1f kV\n', gRL.t(find(abs(gRL.v2) + Zc*abs(gRL.i2) > 1, 1))*1e6, max(abs(gRL.v2))/1e3);
fprintf('Q6 10 mi, 999 ohm : arrivee en m a %.2f us, max|v2| = %.1f kV\n', gO.t(find(abs(gO.v2) + Zc*abs(gO.i2) > 1, 1))*1e6, max(abs(gO.v2))/1e3);
fprintf('Q6 10 mi, cc : arrivee en m a %.2f us, max|v2| = %.1f kV\n', gCC.t(find(abs(gCC.v2) + Zc*abs(gCC.i2) > 1, 1))*1e6, max(abs(gCC.v2))/1e3);


%% ------------------------------------------------------------------
function r = simuler(source, tau, Zc, R, L, dt, T, tf)
% i1 entre dans la ligne en k, i2 sort de la ligne en m vers la charge.
N  = round(T/dt);
t  = (0:N)*dt;
vs = source(t);
v1 = zeros(1, N+1); i1 = v1; v2 = v1; i2 = v1; vL = v1;
Req = 2*L/dt;                  % modele compagnon de l'inductance

for k = 2:N+1
    % valeurs a l'autre extremite a l'instant t - tau
    ts = t(k) - tau;
    if ts < tf - 1e-12
        % avant la fermeture la ligne est au repos (pas d'interpolation
        % a travers l'instant de fermeture)
        v1h = 0; i1h = 0; v2h = 0; i2h = 0;
    else
        j = floor(ts/dt + 1e-9);
        a = ts/dt - j;
        j = j + 1;
        v1h = v1(j) + a*(v1(j+1) - v1(j));
        i1h = i1(j) + a*(i1(j+1) - i1(j));
        v2h = v2(j) + a*(v2(j+1) - v2(j));
        i2h = i2(j) + a*(i2(j+1) - i2(j));
    end
    Ik = i2h - v2h/Zc;         % source d'historique en k
    Im = i1h + v1h/Zc;         % source d'historique en m

    % extremite k : tension imposee par la source
    if t(k) >= tf - 1e-12
        v1(k) = vs(k);
        i1(k) = v1(k)/Zc + Ik;
    end

    % extremite m : Zc // Im, puis R en serie avec Req // Ih
    if L > 0
        Ih = i2(k-1) + vL(k-1)/Req;
    else
        Ih = 0;
    end
    i2(k) = (Im + Req*Ih/Zc)/(1 + (R + Req)/Zc);
    v2(k) = Zc*(Im - i2(k));
    vL(k) = v2(k) - R*i2(k);
end
r = struct('t', t, 'v1', v1, 'i1', i1, 'v2', v2, 'i2', i2);
end

function tracer(liste, leg, titre, tmax, nom)
if tmax < 1e-3
    e = 1e6; ut = 't (\mus)';
else
    e = 1e3; ut = 't (ms)';
end
noms = {'i1', 'i2', 'v1', 'v2'};
lab  = {'i_1 (A)', 'i_2 (A)', 'v_1 (kV)', 'v_2 (kV)'};
g    = [1 1 1e-3 1e-3];
figure('Name', titre);
for q = 1:4
    subplot(2, 2, q); hold on;
    for m = 1:numel(liste)
        s = liste{m}.t <= tmax;
        plot(liste{m}.t(s)*e, liste{m}.(noms{q})(s)*g(q));
    end
    grid on; xlabel(ut); ylabel(lab{q});
    if q == 1 && numel(liste) > 1, legend(leg); end
end
subplot(2, 2, 1); title(titre);
print(gcf, fullfile('figures', nom), '-dpng', '-r200');
end
