import { MapVisualizer } from './map_visualizer/map.js';

document.addEventListener('DOMContentLoaded', () => {
    console.log("[IdleD UI] Démarrage de l'interface de supervision 'La Ruche'.");

    // Initialisation Moteur Cartographique
    const visualizer = new MapVisualizer('map-container');
    visualizer.init();

    // Binding des éléments de statut
    const btnPlay = document.getElementById('btn-play');
    const btnPause = document.getElementById('btn-pause');
    const btnStop = document.getElementById('btn-stop');
    const statusBadge = document.getElementById('supervisor-status');
    const activeScriptLabel = document.getElementById('active-script');
    const lastKeyBadge = document.getElementById('last-key');

    // Éléments de la Carte d'Information Dofus Unity
    const mapCard = document.querySelector('.map-info-card');
    const mapZoneName = document.getElementById('map-zone-name');
    const mapCoords = document.getElementById('map-coords');
    const mapLevel = document.getElementById('map-level');
    const mapErrorBanner = document.getElementById('map-error-banner');

    function updateMapDisplay(isDetected, zoneName, posX, posY, level, errorMsg = null) {
        if (!isDetected) {
            mapCard?.classList.add('detection-error');
            mapLevel?.classList.add('error');
            if (mapZoneName) mapZoneName.innerText = '⚠️ Détection Impossible';
            if (mapCoords) mapCoords.innerText = '[-- , --]';
            if (mapLevel) mapLevel.innerText = 'Indisponible';
            if (mapErrorBanner) {
                mapErrorBanner.innerText = errorMsg || 'Fenêtre Dofus Unity masquée ou en cours de chargement';
            }
            console.warn(`[La Noxine Signal] Échec de détection : ${errorMsg}`);
            return;
        }

        mapCard?.classList.remove('detection-error');
        mapLevel?.classList.remove('error');
        if (mapZoneName) mapZoneName.innerText = zoneName;
        if (mapCoords) mapCoords.innerText = `[${posX}, ${posY}]`;
        if (mapLevel) mapLevel.innerText = `Niveau ${level}`;
        visualizer.addTileMarker(posX, posY, { zone: zoneName, level: level });
    }

    // Données actives détectées sur le client Dofus Unity
    updateMapDisplay(true, 'Amakna (Souterrains)', 4, 28, 1);

    btnPlay?.addEventListener('click', () => {
        if (statusBadge) statusBadge.innerText = 'Machine à États: En Cours (Navigation)';
        if (activeScriptLabel) activeScriptLabel.innerText = 'Recolte_Astrub_Circuit.json';
        console.log('[UI Event] Démarrage de la séquence d\'action');
    });

    btnPause?.addEventListener('click', () => {
        if (statusBadge) statusBadge.innerText = 'Machine à États: En Pause';
        if (activeScriptLabel) activeScriptLabel.innerText = 'En Pause';
        console.log('[UI Event] Mise en pause du système');
    });

    btnStop?.addEventListener('click', () => {
        if (statusBadge) statusBadge.innerText = 'Machine à États: Arrêt d\'Urgence (EmergencyStop)';
        if (activeScriptLabel) activeScriptLabel.innerText = 'Aucun script (Interrompu)';
        console.log('[UI Event] Arrêt d\'urgence manuel');
    });

    // Interception des frappes clavier en temps réel pour affichage dans la barre de statut
    window.addEventListener('keydown', (e) => {
        if (!lastKeyBadge) return;
        
        let keyDisplay = e.key;
        if (e.key === 'ArrowUp') keyDisplay = '↑ Flèche Haut';
        else if (e.key === 'ArrowDown') keyDisplay = '↓ Flèche Bas';
        else if (e.key === 'ArrowLeft') keyDisplay = '← Flèche Gauche';
        else if (e.key === 'ArrowRight') keyDisplay = '→ Flèche Droite';
        else if (e.key === ' ') keyDisplay = 'Espace';

        lastKeyBadge.innerText = keyDisplay;
        lastKeyBadge.classList.add('pressed');

        setTimeout(() => {
            lastKeyBadge.classList.remove('pressed');
        }, 300);

        console.log(`[Key Listener] Touche enfoncée: ${e.key}`);
    });
});
