import { MapVisualizer } from './map_visualizer/map.js';

document.addEventListener('DOMContentLoaded', () => {
    console.log("[IdleD StreamDeck] Initialisation de la console de supervision tactile.");

    // Moteur Cartographique
    const visualizer = new MapVisualizer('map-container');
    visualizer.init();

    // Éléments UI
    const statusBadge = document.getElementById('supervisor-status');
    const activeScriptLabel = document.getElementById('active-script');
    const lastKeyBadge = document.getElementById('last-key');
    const btnFocusDofus = document.getElementById('btn-focus-dofus');

    // Pads StreamDeck
    const pads = document.querySelectorAll('.deck-pad');
    const padPlay = document.getElementById('pad-play');
    const padPause = document.getElementById('pad-pause');
    const padStop = document.getElementById('pad-stop');
    const padFocus = document.getElementById('pad-focus');
    const padHarvest = document.getElementById('pad-harvest');
    const padCombat = document.getElementById('pad-combat');
    const padPathfinding = document.getElementById('pad-pathfinding');
    const padScan = document.getElementById('pad-scan');

    // Éléments de la Carte Dofus Unity
    const mapCard = document.getElementById('map-info-card');
    const mapZoneName = document.getElementById('map-zone-name');
    const mapCoords = document.getElementById('map-coords');
    const mapLevel = document.getElementById('map-level');
    const mapErrorBanner = document.getElementById('map-error-banner');

    function updateMapDisplay(isDetected, zoneName, posX, posY, level, errorMsg = null) {
        if (!isDetected) {
            mapCard?.classList.add('detection-error');
            if (mapZoneName) mapZoneName.innerText = '⚠️ Détection Impossible';
            if (mapCoords) mapCoords.innerText = '[-- , --]';
            if (mapLevel) mapLevel.innerText = 'N/A';
            if (mapErrorBanner) {
                mapErrorBanner.innerText = errorMsg || 'Fenêtre Dofus Unity introuvable';
            }
            return;
        }

        mapCard?.classList.remove('detection-error');
        if (mapZoneName) mapZoneName.innerText = zoneName;
        if (mapCoords) mapCoords.innerText = `[${posX}, ${posY}]`;
        if (mapLevel) mapLevel.innerText = `Niveau ${level}`;
        visualizer.addTileMarker(posX, posY, { zone: zoneName, level: level });
    }

    // Affichage initial
    updateMapDisplay(true, 'Amakna (Souterrains)', 4, 28, 1);

    // Fonction d'animation tactile StreamDeck
    function triggerPadFeedback(padElement) {
        if (!padElement) return;
        padElement.classList.add('pressed');
        setTimeout(() => {
            padElement.classList.remove('pressed');
        }, 200);
    }

    // Action : Focus Fenêtre Dofus Unity
    function triggerFocusDofus() {
        if (statusBadge) statusBadge.innerText = 'Action: Win32 Focus Dofus.exe';
        console.log("[StreamDeck Action] Focus Dofus Unity demandé.");
        triggerPadFeedback(padFocus);
    }

    btnFocusDofus?.addEventListener('click', triggerFocusDofus);
    padFocus?.addEventListener('click', triggerFocusDofus);

    // Action : Play
    padPlay?.addEventListener('click', () => {
        if (statusBadge) statusBadge.innerText = 'FSM: En Cours (Navigation)';
        if (activeScriptLabel) activeScriptLabel.innerText = 'Recolte_Astrub_Circuit.json';
        triggerPadFeedback(padPlay);
        console.log("[StreamDeck Action] Séquence démarrée.");
    });

    // Action : Pause
    padPause?.addEventListener('click', () => {
        if (statusBadge) statusBadge.innerText = 'FSM: En Pause';
        if (activeScriptLabel) activeScriptLabel.innerText = 'En Pause';
        triggerPadFeedback(padPause);
        console.log("[StreamDeck Action] Séquence en pause.");
    });

    // Action : Stop
    padStop?.addEventListener('click', () => {
        if (statusBadge) statusBadge.innerText = 'FSM: Arrêt Urgence (EmergencyStop)';
        if (activeScriptLabel) activeScriptLabel.innerText = 'Aucun script (Interrompu)';
        triggerPadFeedback(padStop);
        console.log("[StreamDeck Action] Arrêt d'urgence.");
    });

    // Sélection de mode Récolte / Combat
    padHarvest?.addEventListener('click', () => {
        padHarvest.classList.add('active');
        padCombat?.classList.remove('active');
        if (activeScriptLabel) activeScriptLabel.innerText = 'Recolte_Astrub_Circuit.json';
        triggerPadFeedback(padHarvest);
    });

    padCombat?.addEventListener('click', () => {
        padCombat.classList.add('active');
        padHarvest?.classList.remove('active');
        if (activeScriptLabel) activeScriptLabel.innerText = 'Combat_Ia_Tactique.json';
        triggerPadFeedback(padCombat);
    });

    padPathfinding?.addEventListener('click', () => {
        if (statusBadge) statusBadge.innerText = 'Cerveau: Calcul A* exécuté';
        triggerPadFeedback(padPathfinding);
    });

    padScan?.addEventListener('click', () => {
        if (statusBadge) statusBadge.innerText = 'Noxine: Scan visuel CUDA effectué';
        triggerPadFeedback(padScan);
    });

    // Binding des Raccourcis Clavier vers le StreamDeck
    const keyMap = {
        'F5': padPlay,
        'F6': padPause,
        'F7': padStop,
        'F8': padFocus,
        '1': padHarvest,
        '2': padCombat,
        '3': padPathfinding,
        '4': padScan
    };

    window.addEventListener('keydown', (e) => {
        let keyDisplay = e.key;
        if (e.key === 'ArrowUp') keyDisplay = '↑ Flèche Haut';
        else if (e.key === 'ArrowDown') keyDisplay = '↓ Flèche Bas';
        else if (e.key === 'ArrowLeft') keyDisplay = '← Flèche Gauche';
        else if (e.key === 'ArrowRight') keyDisplay = '→ Flèche Droite';
        else if (e.key === ' ') keyDisplay = 'Espace';

        if (lastKeyBadge) {
            lastKeyBadge.innerText = keyDisplay;
            lastKeyBadge.classList.add('pressed');
            setTimeout(() => lastKeyBadge.classList.remove('pressed'), 300);
        }

        const targetPad = keyMap[e.key];
        if (targetPad) {
            e.preventDefault();
            targetPad.click();
        }
    });
});
