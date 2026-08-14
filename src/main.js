document.addEventListener('DOMContentLoaded', () => {
    console.log("[IdleD StreamDeck] Initialisation de la console StreamDeck Macro Chat.");

    // Éléments UI
    const statusBadge = document.getElementById('supervisor-status');
    const activeScriptLabel = document.getElementById('active-script');
    const lastKeyBadge = document.getElementById('last-key');
    const btnFocusDofus = document.getElementById('btn-focus-dofus');

    // Infos Tuile
    const mapZoneName = document.getElementById('map-zone-name');
    const mapCoords = document.getElementById('map-coords');
    const mapLevel = document.getElementById('map-level');

    // Pads StreamDeck
    const padSalut = document.getElementById('pad-salut');
    const padTravel = document.getElementById('pad-travel');
    const padFocus = document.getElementById('pad-focus');
    const padStop = document.getElementById('pad-stop');

    // Fonction d'animation tactile StreamDeck
    function triggerPadFeedback(padElement) {
        if (!padElement) return;
        padElement.classList.add('pressed');
        setTimeout(() => {
            padElement.classList.remove('pressed');
        }, 200);
    }

    // Mise à jour de l'affichage de la tuile en jeu
    function updateTileDisplay(zoneName, posX, posY, level) {
        if (mapZoneName) mapZoneName.innerText = zoneName;
        if (mapCoords) mapCoords.innerText = `[${posX}, ${posY}]`;
        if (mapLevel) mapLevel.innerText = `Niv. ${level}`;
    }

    // Affichage initial de la tuile
    updateTileDisplay('Amakna (Souterrains)', 4, 28, 1);

    // Action : Focus Fenêtre Dofus Unity
    function triggerFocusDofus() {
        if (statusBadge) statusBadge.innerText = 'Win32 Focus Dofus.exe';
        console.log("[StreamDeck Action] Focus Dofus Unity demandé.");
        triggerPadFeedback(padFocus);
    }

    btnFocusDofus?.addEventListener('click', triggerFocusDofus);
    padFocus?.addEventListener('click', triggerFocusDofus);

    // Pad 1 : Action Salut (Écris "salut" dans le chat Dofus)
    padSalut?.addEventListener('click', () => {
        triggerFocusDofus();
        if (statusBadge) statusBadge.innerText = 'Chat: "salut" envoyé';
        if (activeScriptLabel) activeScriptLabel.innerText = 'Commande: salut';
        triggerPadFeedback(padSalut);
        console.log("[StreamDeck Chat] Envoi du message 'salut' au client Dofus.");
    });

    // Pad 2 : Action Travel To (Envoie la commande "/travel x,y")
    padTravel?.addEventListener('click', () => {
        triggerFocusDofus();
        // Exemple avec coordonnées dynamique de la tuile active
        const travelCmd = "/travel 4,28";
        if (statusBadge) statusBadge.innerText = `Chat: "${travelCmd}" envoyé`;
        if (activeScriptLabel) activeScriptLabel.innerText = `Commande: ${travelCmd}`;
        triggerPadFeedback(padTravel);
        console.log(`[StreamDeck Chat] Envoi de la commande '${travelCmd}' au client Dofus.`);
    });

    // Pad 4 : Stop d'urgence
    padStop?.addEventListener('click', () => {
        if (statusBadge) statusBadge.innerText = 'FSM: Arrêt Urgence (EmergencyStop)';
        if (activeScriptLabel) activeScriptLabel.innerText = 'Commande interrompue';
        triggerPadFeedback(padStop);
        console.log("[StreamDeck Action] Arrêt d'urgence.");
    });

    // Binding des Raccourcis Clavier vers les Pads
    const keyMap = {
        'F5': padSalut,
        'F6': padTravel,
        'F7': padFocus,
        'F8': padStop
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
