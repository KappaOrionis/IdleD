document.addEventListener('DOMContentLoaded', () => {
    console.log("[IdleD StreamDeck] Console StreamDeck initialisée.");

    const CONFIG_STORAGE_KEY = 'idled_streamdeck_config';

    // Helper d'appel IPC Tauri sécurisé avec détection universelle
    async function invokeTauri(cmd, args = {}) {
        try {
            if (window.__TAURI__) {
                if (typeof window.__TAURI__.invoke === 'function') {
                    return await window.__TAURI__.invoke(cmd, args);
                }
                if (window.__TAURI__.tauri && typeof window.__TAURI__.tauri.invoke === 'function') {
                    return await window.__TAURI__.tauri.invoke(cmd, args);
                }
            }
            if (typeof window.__TAURI_INVOKE__ === 'function') {
                return await window.__TAURI_INVOKE__(cmd, args);
            }
        } catch (err) {
            console.warn(`[Tauri IPC] Erreur appel '${cmd}':`, err);
        }
        return null;
    }

    // Éléments UI Globaux
    const activeScriptLabel = document.getElementById('active-script');
    const lastKeyBadge = document.getElementById('last-key');
    const gridContainer = document.getElementById('streamdeck-grid');
    const previewWindowTitle = document.getElementById('preview-window-title');

    // Infos Tuile
    const mapZoneName = document.getElementById('map-zone-name');
    const mapCoords = document.getElementById('map-coords');
    const mapLevel = document.getElementById('map-level');

    // Modale de Configuration
    const configModal = document.getElementById('config-modal');
    const btnCloseModal = document.getElementById('btn-close-modal');
    const btnSaveConfig = document.getElementById('btn-save-config');
    const inputRows = document.getElementById('input-rows');
    const inputCols = document.getElementById('input-cols');
    const inputBtnWidth = document.getElementById('input-btn-width');
    const inputBtnHeight = document.getElementById('input-btn-height');

    // Configuration par défaut mémorisée dans localStorage
    let gridConfig = {
        rows: 2,
        cols: 3,
        btnWidth: 70,
        btnHeight: 70
    };

    // Chargement de la configuration mémorisée
    function loadSavedConfig() {
        try {
            const saved = localStorage.getItem(CONFIG_STORAGE_KEY);
            if (saved) {
                const parsed = JSON.parse(saved);
                if (parsed && typeof parsed === 'object') {
                    gridConfig.rows = Math.max(1, Math.min(6, parseInt(parsed.rows, 10) || 2));
                    gridConfig.cols = Math.max(1, Math.min(6, parseInt(parsed.cols, 10) || 3));
                    gridConfig.btnWidth = Math.max(40, Math.min(250, parseInt(parsed.btnWidth, 10) || 70));
                    gridConfig.btnHeight = Math.max(40, Math.min(250, parseInt(parsed.btnHeight, 10) || 70));
                }
            }
        } catch (e) {
            console.warn("[StreamDeck Config] Erreur chargement configuration locale :", e);
        }
    }

    function saveConfig() {
        try {
            localStorage.setItem(CONFIG_STORAGE_KEY, JSON.stringify(gridConfig));
        } catch (e) {
            console.warn("[StreamDeck Config] Erreur sauvegarde configuration locale :", e);
        }
    }

    // Liste des boutons configurables
    const defaultButtons = [
        {
            id: 'btn-config',
            icon: '⚙️',
            label: 'CONFIG',
            sub: 'Dimensions',
            shortcut: 'F1',
            action: openConfigModal
        },
        {
            id: 'btn-salut',
            icon: '💬',
            label: 'SALUT',
            sub: 'Écrit salut',
            shortcut: 'F2',
            action: sendSalutChat
        },
        {
            id: 'btn-travel',
            icon: '🚀',
            label: 'TRAVEL TO',
            sub: '/travel 4,28',
            shortcut: 'F3',
            action: sendTravelToChat
        },
        {
            id: 'btn-stop',
            icon: '⏹',
            label: 'STOP',
            sub: 'Urgence',
            shortcut: 'F4',
            action: triggerEmergencyStop
        }
    ];

    function openConfigModal() {
        if (inputRows) inputRows.value = gridConfig.rows;
        if (inputCols) inputCols.value = gridConfig.cols;
        if (inputBtnWidth) inputBtnWidth.value = gridConfig.btnWidth;
        if (inputBtnHeight) inputBtnHeight.value = gridConfig.btnHeight;
        configModal?.classList.add('open');
    }

    function closeConfigModal() {
        configModal?.classList.remove('open');
    }

    btnCloseModal?.addEventListener('click', closeConfigModal);

    btnSaveConfig?.addEventListener('click', () => {
        const rows = parseInt(inputRows.value, 10) || 2;
        const cols = parseInt(inputCols.value, 10) || 3;
        const width = parseInt(inputBtnWidth.value, 10) || 70;
        const height = parseInt(inputBtnHeight.value, 10) || 70;
        
        gridConfig.rows = Math.max(1, Math.min(6, rows));
        gridConfig.cols = Math.max(1, Math.min(6, cols));
        gridConfig.btnWidth = Math.max(40, Math.min(250, width));
        gridConfig.btnHeight = Math.max(40, Math.min(250, height));

        saveConfig();
        renderGrid();
        closeConfigModal();
    });

    function triggerPadFeedback(padElement) {
        if (!padElement) return;
        padElement.classList.add('pressed');
        setTimeout(() => {
            padElement.classList.remove('pressed');
        }, 200);
    }

    async function sendSalutChat() {
        if (activeScriptLabel) activeScriptLabel.innerText = 'salut';
        
        await invokeTauri('send_ipc_message', {
            agent: 'scaphandre',
            action: 'send_chat_message',
            payload: { text: 'salut' }
        });
        console.log("[StreamDeck IPC -> Le Scaphandre] Message 'salut' transmis.");
    }

    async function sendTravelToChat() {
        const travelCmd = "/travel 4,28";
        if (activeScriptLabel) activeScriptLabel.innerText = travelCmd;
        
        await invokeTauri('send_ipc_message', {
            agent: 'scaphandre',
            action: 'travel_to',
            payload: { x: 4, y: 28 }
        });
        console.log(`[StreamDeck IPC -> Le Scaphandre] Commande '${travelCmd}' transmise.`);
    }

    async function triggerEmergencyStop() {
        if (activeScriptLabel) activeScriptLabel.innerText = 'STOP';
        
        await invokeTauri('trigger_emergency_stop');
        console.log("[StreamDeck IPC -> Le Cadran] Arrêt d'urgence déclenché.");
    }

    // Rendu dynamique de la grille selon rows x cols et taille personnalisée des pads (ex: 50x50)
    function renderGrid() {
        if (!gridContainer) return;
        
        const w = gridConfig.btnWidth;
        const h = gridConfig.btnHeight;

        gridContainer.style.gridTemplateRows = `repeat(${gridConfig.rows}, ${h}px)`;
        gridContainer.style.gridTemplateColumns = `repeat(${gridConfig.cols}, ${w}px)`;

        gridContainer.innerHTML = '';
        const totalSlots = gridConfig.rows * gridConfig.cols;

        // Déterminer la taille optimale de la police / icones selon les dimensions px
        const isMini = (w <= 55 || h <= 55);
        const isMedium = (w <= 85 || h <= 85);

        for (let i = 0; i < totalSlots; i++) {
            const btnData = defaultButtons[i] || {
                id: `btn-custom-${i+1}`,
                icon: '➕',
                label: `P${i+1}`,
                sub: '',
                shortcut: `F${i+1}`,
                action: () => {
                    if (activeScriptLabel) activeScriptLabel.innerText = `Slot ${i+1} activé`;
                }
            };

            const pad = document.createElement('button');
            pad.className = 'deck-pad';
            pad.id = btnData.id;
            pad.setAttribute('data-key', btnData.shortcut);
            pad.style.width = `${w}px`;
            pad.style.height = `${h}px`;

            const iconSize = isMini ? '1rem' : (isMedium ? '1.3rem' : '1.8rem');
            const labelSize = isMini ? '0.62rem' : (isMedium ? '0.72rem' : '0.85rem');
            const showSub = !isMini && Boolean(btnData.sub);

            pad.innerHTML = `
                <div class="pad-icon" style="font-size: ${iconSize};">${btnData.icon}</div>
                <div class="pad-label" style="font-size: ${labelSize};">${btnData.label}</div>
                ${showSub ? `<div class="pad-sub">${btnData.sub}</div>` : ''}
                ${!isMini ? `<kbd class="pad-shortcut">${btnData.shortcut}</kbd>` : ''}
            `;

            pad.addEventListener('click', () => {
                triggerPadFeedback(pad);
                if (btnData.action) btnData.action();
            });

            gridContainer.appendChild(pad);
        }

        autoAdjustWindowSize();
    }

    // Calcule et applique automatiquement la taille idéale de la fenêtre Tauri
    async function autoAdjustWindowSize() {
        const w = gridConfig.btnWidth;
        const h = gridConfig.btnHeight;
        const cols = gridConfig.cols;
        const rows = gridConfig.rows;

        // Largeur = padding latéral (24px) + boutons + gaps (10px par colonne) + marge de sécurité
        const gridWidth = (cols * w) + ((cols - 1) * 10) + 32;
        // Largeur minimale requise pour afficher l'en-tête (bannière active + flux + tuile) proprement
        const targetWidth = Math.max(280, gridWidth);

        // Hauteur = En-tête (~145px) + grille ((rows * h) + gaps) + footer (~32px) + padding global (~24px) + barre titre (~35px)
        const gridHeight = (rows * h) + ((rows - 1) * 10);
        const targetHeight = 145 + gridHeight + 34 + 24 + 35;

        try {
            await invokeTauri('adjust_window_size', {
                width: targetWidth,
                height: targetHeight
            });
        } catch (e) {
            console.debug("Redimensionnement automatique ignoré (hors Tauri):", e);
        }
    }

    // Initialisation
    loadSavedConfig();
    renderGrid();

    // Éléments du Flux Visuel
    const streamThumbnailImg = document.getElementById('stream-thumbnail-img');

    // Actualisation périodique du titre et de la vignette de flux visuel
    async function updateActiveWindowStream() {
        try {
            const thumb = await invokeTauri('get_stream_thumbnail');
            if (thumb) {
                if (thumb.title && previewWindowTitle) {
                    previewWindowTitle.innerText = thumb.title;
                }
                if (thumb.data_url && streamThumbnailImg) {
                    streamThumbnailImg.src = thumb.data_url;
                }
            }
        } catch (err) {
            console.debug("Erreur rafraîchissement flux visuel:", err);
        }
    }
    updateActiveWindowStream();
    setInterval(updateActiveWindowStream, 400);

    // Raccourcis clavier globaux
    window.addEventListener('keydown', (e) => {
        let keyDisplay = e.key;
        if (e.key === 'ArrowUp') keyDisplay = '↑ Haut';
        else if (e.key === 'ArrowDown') keyDisplay = '↓ Bas';
        else if (e.key === 'ArrowLeft') keyDisplay = '← Gauche';
        else if (e.key === 'ArrowRight') keyDisplay = '→ Droite';
        else if (e.key === ' ') keyDisplay = 'Espace';

        if (lastKeyBadge) {
            lastKeyBadge.innerText = keyDisplay;
            lastKeyBadge.classList.add('pressed');
            setTimeout(() => lastKeyBadge.classList.remove('pressed'), 300);
        }

        const matchingPad = gridContainer?.querySelector(`[data-key="${e.key}"]`);
        if (matchingPad) {
            e.preventDefault();
            matchingPad.click();
        }
    });
});
