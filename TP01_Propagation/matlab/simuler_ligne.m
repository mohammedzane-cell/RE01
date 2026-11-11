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
