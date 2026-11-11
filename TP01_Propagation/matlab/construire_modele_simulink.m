% Construction et simulation du modèle de vérification TP01_simulink_check.slx
% (Simscape Electrical, Specialized Power Systems), cas Q1 : charge R-L.
%
% Source alternative -> disjoncteur (fermeture à 0,1 ms) -> ligne à constantes
% réparties monophasée sans pertes -> charge R-L série. powergui discret, Ts = 0,1 ms.
% Les grandeurs v1, i1, v2, i2 sont enregistrées dans resultats/simulink_Q1.mat,
% que TP01_ligne_longue.m superpose ensuite aux résultats du modèle de Bergeron.
%
% Le script n'a pas pu être exécuté sans Simscape : en cas d'erreur sur un nom de
% paramètre de masque, la liste des noms valides du bloc est affichée.

clear; clc;
dossier_tp = fileparts(fileparts(mfilename('fullpath')));
modele = 'TP01_simulink_check';
fichier_slx = fullfile(dossier_tp, 'matlab', [modele '.slx']);

mi = 1.609344;                  % km par mile
Lp_km = 1.5e-3/mi;              % H/km
Cp_km = 0.02e-6/mi;             % F/km
d_km  = 100*mi;                 % km
Vm = 230000*sqrt(2)/sqrt(3);
dt = 1e-4;
T_sim = 0.1;
inverser_source = false;        % à passer à true si le contrôle de polarité échoue

if bdIsLoaded(modele), close_system(modele, 0); end
new_system(modele);
open_system(modele);
set_param(modele, 'StopTime', num2str(T_sim));

% Blocs (positions [gauche haut droite bas]).
ajouter(modele, 'powergui', 'powergui', [20 20 90 60]);
ajouter(modele, 'AC Voltage Source', 'Source', [40 140 80 200]);
ajouter(modele, 'Breaker', 'Disjoncteur', [140 120 190 160]);
ajouter(modele, 'Current Measurement', 'Mesure_i1', [230 120 270 160]);
ajouter(modele, 'Voltage Measurement', 'Mesure_v1', [300 200 340 240]);
ajouter(modele, 'Distributed Parameters Line', 'Ligne', [380 120 460 160]);
ajouter(modele, 'Current Measurement', 'Mesure_i2', [500 120 540 160]);
ajouter(modele, 'Voltage Measurement', 'Mesure_v2', [560 200 600 240]);
ajouter(modele, 'Series RLC Branch', 'Charge', [620 130 660 190]);
ajouter(modele, 'Ground', 'Masse1', [40 260 80 290]);
ajouter(modele, 'Ground', 'Masse2', [300 280 340 310]);
ajouter(modele, 'Ground', 'Masse3', [560 280 600 310]);
ajouter(modele, 'Ground', 'Masse4', [620 260 660 290]);

regler([modele '/powergui'], 'SimulationMode', 'Discrete', 'SampleTime', num2str(dt));
% La source SPS est en sinus : phase de 90 degrés pour obtenir Vm.cos(wt).
regler([modele '/Source'], 'Amplitude', num2str(Vm, 12), 'Phase', '90', 'Frequency', '60');
regler([modele '/Disjoncteur'], 'InitialState', '0', 'SwitchTimes', '[1e-4]', ...
       'BreakerResistance', '1e-3', 'SnubberResistance', 'inf', 'SnubberCapacitance', 'inf');
regler([modele '/Ligne'], 'Phases', '1', 'Frequency', '60', 'Resistance', '0', ...
       'Inductance', num2str(Lp_km, 12), 'Capacitance', num2str(Cp_km, 12), ...
       'Length', num2str(d_km, 12));
regler([modele '/Charge'], 'BranchType', 'RL', 'Resistance', '400', 'Inductance', '0.25');

% Connexions électriques : source -> disjoncteur -> mesure i1 -> ligne -> mesure i2 -> charge.
if inverser_source
    relier(modele, 'Source', 'L', 1, 'Disjoncteur', 'L', 1);
    relier(modele, 'Source', 'R', 1, 'Masse1', 'L', 1);
else
    relier(modele, 'Source', 'R', 1, 'Disjoncteur', 'L', 1);
    relier(modele, 'Source', 'L', 1, 'Masse1', 'L', 1);
end
relier(modele, 'Disjoncteur', 'R', 1, 'Mesure_i1', 'L', 1);
relier(modele, 'Mesure_i1', 'R', 1, 'Ligne', 'L', 1);
relier(modele, 'Mesure_i1', 'R', 1, 'Mesure_v1', 'L', 1);
relier(modele, 'Mesure_v1', 'L', 2, 'Masse2', 'L', 1);
relier(modele, 'Ligne', 'R', 1, 'Mesure_i2', 'L', 1);
relier(modele, 'Ligne', 'R', 1, 'Mesure_v2', 'L', 1);
relier(modele, 'Mesure_v2', 'L', 2, 'Masse3', 'L', 1);
relier(modele, 'Mesure_i2', 'R', 1, 'Charge', 'L', 1);
relier(modele, 'Charge', 'R', 1, 'Masse4', 'L', 1);

% Enregistrement vers l'espace de travail.
add_block('simulink/Sources/Clock', [modele '/Horloge'], 'Position', [700 20 730 50]);
signaux = {'Horloge', 't_slx'; 'Mesure_v1', 'v1_slx'; 'Mesure_i1', 'i1_slx'; ...
           'Mesure_v2', 'v2_slx'; 'Mesure_i2', 'i2_slx'};
for k = 1:size(signaux, 1)
    nom = ['Vers_' signaux{k, 2}];
    add_block('simulink/Sinks/To Workspace', [modele '/' nom], 'VariableName', signaux{k, 2}, ...
              'SaveFormat', 'Array', 'Position', [780 20+60*(k-1) 860 50+60*(k-1)]);
    add_line(modele, [signaux{k, 1} '/1'], [nom '/1'], 'autorouting', 'on');
end

save_system(modele, fichier_slx);
fprintf('Modèle enregistré : %s\n', fichier_slx);

so = sim(modele, 'ReturnWorkspaceOutputs', 'on');
t  = so.get('t_slx').';
v1 = so.get('v1_slx').';
i1 = so.get('i1_slx').';
v2 = so.get('v2_slx').';
i2 = so.get('i2_slx').';

% Contrôle de polarité : après fermeture, v1 doit suivre Vm.cos(wt).
sel = t > 2e-4;
c = sum(v1(sel).*cos(2*pi*60*t(sel)));
if c < 0
    warning(['v1 est en opposition avec Vm.cos(wt) : relancer avec inverser_source = true ' ...
             '(ou inverser les bornes de Mesure_v1).']);
end
fprintf('v1 au premier pas après fermeture : %.0f V (attendu : environ %.0f V)\n', ...
        v1(find(t >= 1e-4 - 1e-9, 1) + 1), Vm*cos(2*pi*60*2e-4));

save(fullfile(dossier_tp, 'resultats', 'simulink_Q1.mat'), 't', 'v1', 'i1', 'v2', 'i2');
fprintf('Grandeurs enregistrées dans resultats/simulink_Q1.mat ; relancer TP01_ligne_longue.m\n');


function ajouter(modele, nom_bibli, nom, position)
% Recherche le bloc par son nom dans la bibliothèque SPS (le chemin change selon la version).
chemin = '';
for bibli = {'sps_lib', 'powerlib'}
    try
        load_system(bibli{1});
        trouve = find_system(bibli{1}, 'LookUnderMasks', 'on', 'FollowLinks', 'on', ...
                             'Name', nom_bibli);
        if ~isempty(trouve)
            chemin = trouve{1};
            break;
        end
    catch
    end
end
if isempty(chemin)
    error('Bloc « %s » introuvable : Simscape Electrical (Specialized Power Systems) est-il installé ?', ...
          nom_bibli);
end
add_block(chemin, [modele '/' nom], 'Position', position);
end

function regler(bloc, varargin)
% set_param paramètre par paramètre ; en cas de nom invalide, affiche les noms acceptés.
for k = 1:2:numel(varargin)
    try
        set_param(bloc, varargin{k}, varargin{k+1});
    catch err
        fprintf('Paramètre « %s » refusé pour %s (%s).\nParamètres disponibles :\n', ...
                varargin{k}, bloc, err.message);
        disp(fieldnames(get_param(bloc, 'DialogParameters')));
        rethrow(err);
    end
end
end

function relier(modele, blocA, coteA, kA, blocB, coteB, kB)
% Liaison électrique entre ports physiques (L : LConn, R : RConn).
hA = get_param([modele '/' blocA], 'PortHandles');
hB = get_param([modele '/' blocB], 'PortHandles');
pA = port_physique(hA, coteA, kA);
pB = port_physique(hB, coteB, kB);
add_line(modele, pA, pB, 'autorouting', 'on');
end

function p = port_physique(h, cote, k)
if strcmp(cote, 'L')
    p = h.LConn(k);
else
    p = h.RConn(k);
end
end
