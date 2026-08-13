import { MapVisualizer } from './map_visualizer/map.js';

document.addEventListener('DOMContentLoaded', () => {
    console.log("[IdleD UI] Démarrage de l'interface de supervision 'La Ruche'.");

    // Initialisation Moteur Cartographique
    const visualizer = new MapVisualizer('map-container');
    visualizer.init();

    // Binding des boutons de contrôle du Superviseur
    const btnPlay = document.getElementById('btn-play');
    const btnPause = document.getElementById('btn-pause');
    const btnStop = document.getElementById('btn-stop');
    const statusBadge = document.getElementById('supervisor-status');

    btnPlay?.addEventListener('click', () => {
        if (statusBadge) statusBadge.innerText = 'Machine à États: En Cours (Navigation)';
        console.log('[UI Event] Démarrage de la séquence d\'action');
    });

    btnPause?.addEventListener('click', () => {
        if (statusBadge) statusBadge.innerText = 'Machine à États: En Pause';
        console.log('[UI Event] Mise en pause du système');
    });

    btnStop?.addEventListener('click', () => {
        if (statusBadge) statusBadge.innerText = 'Machine à États: Arrêt d\'Urgence (EmergencyStop)';
        console.log('[UI Event] Arrêt d\'urgence manuel');
    });
});
