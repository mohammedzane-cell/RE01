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
