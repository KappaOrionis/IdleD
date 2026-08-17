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
    const sunNodesBadge = document.getElementById('sun-nodes-badge');

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

    const BUTTONS_STORAGE_KEY = 'idled_streamdeck_buttons_config';

    // Modale d'Édition de Bouton
    const buttonEditModal = document.getElementById('button-edit-modal');
    const btnCloseEditModal = document.getElementById('btn-close-edit-modal');
    const btnSaveEditButton = document.getElementById('btn-save-edit-button');
    const editModalTitle = document.getElementById('edit-modal-title');
    const editBtnIcon = document.getElementById('edit-btn-icon');
    const editBtnLabel = document.getElementById('edit-btn-label');
    const editBtnSub = document.getElementById('edit-btn-sub');
    const editBtnType = document.getElementById('edit-btn-type');
    const editBtnValue = document.getElementById('edit-btn-value');
    const editBtnShortcut = document.getElementById('edit-btn-shortcut');

    const editBtnAutoEnter = document.getElementById('edit-btn-auto-enter');
    const iconPickerGrid = document.getElementById('icon-picker-grid');

    const PRESET_ICONS = [
        '💬', '🚀', '⚡', '⚔️', '🛡️', '🌾', '⛏️', '🎣',
        '❤️', '🎯', '🔥', '💧', '🌿', '✨', '🎁', '🏆',
        '📢', '🖐️', '👋', '🛑', '🔑', '⭐', '🧪', '📜'
    ];

    function renderIconPicker(selectedIcon) {
        if (!iconPickerGrid) return;
        iconPickerGrid.innerHTML = '';

        PRESET_ICONS.forEach(icon => {
            const item = document.createElement('div');
            item.className = 'icon-option';
            if (icon === selectedIcon) item.classList.add('selected');
            item.innerText = icon;

            item.addEventListener('click', () => {
                if (editBtnIcon) editBtnIcon.value = icon;
                iconPickerGrid.querySelectorAll('.icon-option').forEach(el => el.classList.remove('selected'));
                item.classList.add('selected');
            });

            iconPickerGrid.appendChild(item);
        });
    }

    let currentEditingSlotIndex = null;

    // Configuration des boutons par défaut
    const defaultButtons = [
        {
            id: 'btn-config',
            icon: '⚙️',
            label: 'CONFIG',
            sub: 'Dimensions',
            shortcut: 'F1',
            type: 'config',
            value: '',
            autoEnter: true
        },
        {
            id: 'btn-salut',
            icon: '💬',
            label: 'SALUT',
            sub: 'Écrit salut',
            shortcut: 'F2',
            type: 'chat',
            value: 'salut',
            autoEnter: true
        },
        {
            id: 'btn-travel',
            icon: '🚀',
            label: 'TRAVEL TO',
            sub: '/travel 4,28',
            shortcut: 'F3',
            type: 'travel',
            value: '4,28',
            autoEnter: true
        }
    ];

    let customButtonsConfig = {};

    function loadSavedButtonsConfig() {
        try {
            const saved = localStorage.getItem(BUTTONS_STORAGE_KEY);
            if (saved) {
                const parsed = JSON.parse(saved);
                if (parsed && typeof parsed === 'object') {
                    // Nettoyer les anciennes configurations qui auraient sauvegardé un bouton STOP sur un slot intermédiaire
                    Object.keys(parsed).forEach(slotIdx => {
                        if (parsed[slotIdx] && (parsed[slotIdx].type === 'stop' || parsed[slotIdx].label === 'STOP')) {
                            delete parsed[slotIdx];
                        }
                    });
                    customButtonsConfig = parsed;
                }
            }
        } catch (e) {
            console.warn("[StreamDeck Buttons] Erreur chargement boutons persistant :", e);
        }
    }

    function saveButtonsConfig() {
        try {
            localStorage.setItem(BUTTONS_STORAGE_KEY, JSON.stringify(customButtonsConfig));
        } catch (e) {
            console.warn("[StreamDeck Buttons] Erreur sauvegarde boutons persistant :", e);
        }
    }

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

    // Ouverture et enregistrement du Modal d'Édition de Bouton
    function openButtonEditModal(slotIndex, btnData) {
        const isConfigBtn = (slotIndex === 0 || btnData.id === 'btn-config' || btnData.type === 'config');
        const isStopBtn = (slotIndex === 1 || btnData.id === 'btn-stop' || btnData.type === 'stop');

        if (isConfigBtn || isStopBtn) {
            console.log(`[StreamDeck] Le bouton ${isConfigBtn ? 'CONFIG' : 'STOP'} est verrouillé et ne peut pas être modifié.`);
            return;
        }

        currentEditingSlotIndex = slotIndex;
        if (editModalTitle) editModalTitle.innerText = `✏️ Éditer le Bouton Slot ${slotIndex + 1}`;
        if (editBtnIcon) editBtnIcon.value = btnData.icon || '💬';
        renderIconPicker(btnData.icon || '💬');
        if (editBtnLabel) editBtnLabel.value = btnData.label || `Slot ${slotIndex + 1}`;
        if (editBtnSub) editBtnSub.value = btnData.sub || '';
        if (editBtnType) editBtnType.value = btnData.type || 'chat';
        if (editBtnValue) editBtnValue.value = btnData.value || '';
        if (editBtnShortcut) editBtnShortcut.value = btnData.shortcut || `F${slotIndex + 1}`;
        if (editBtnAutoEnter) editBtnAutoEnter.checked = (btnData.autoEnter !== false);

        buttonEditModal?.classList.add('open');
        autoAdjustWindowSize(true);
    }

    function closeButtonEditModal() {
        buttonEditModal?.classList.remove('open');
        currentEditingSlotIndex = null;
        autoAdjustWindowSize(false);
    }

    btnCloseEditModal?.addEventListener('click', closeButtonEditModal);

    btnSaveEditButton?.addEventListener('click', () => {
        if (currentEditingSlotIndex === null) return;

        const icon = editBtnIcon.value.trim() || '⚡';
        const label = editBtnLabel.value.trim() || `Slot ${currentEditingSlotIndex + 1}`;
        const sub = editBtnSub.value.trim();
        const type = editBtnType.value;
        const value = editBtnValue.value.trim();
        const shortcut = editBtnShortcut.value.trim().toUpperCase() || `F${currentEditingSlotIndex + 1}`;
        const autoEnter = editBtnAutoEnter ? editBtnAutoEnter.checked : true;

        customButtonsConfig[currentEditingSlotIndex] = {
            icon,
            label,
            sub,
            type,
            value,
            shortcut,
            autoEnter
        };

        saveButtonsConfig();
        renderGrid();
        closeButtonEditModal();
    });

    function triggerPadFeedback(padElement) {
        if (!padElement) return;
        padElement.classList.add('pressed');
        setTimeout(() => {
            padElement.classList.remove('pressed');
        }, 200);
    }

    async function executeButtonAction(btnData) {
        const type = btnData.type || 'custom';
        const val = btnData.value || '';
        const autoEnter = (btnData.autoEnter !== false);

        if (type === 'config') {
            openConfigModal();
            return;
        }

        if (type === 'chat') {
            const chatText = val || btnData.label || 'salut';
            if (activeScriptLabel) activeScriptLabel.innerText = chatText;
            
            const actionCmd = autoEnter ? 'send_chat_message' : 'type_text';
            await invokeTauri('send_ipc_message', {
                agent: 'scaphandre',
                action: actionCmd,
                payload: { text: chatText }
            });
            console.log(`[StreamDeck IPC -> Le Scaphandre] Chat (${actionCmd}): '${chatText}'`);
        } else if (type === 'travel') {
            const coords = val.split(',').map(s => parseInt(s.trim(), 10));
            const x = !isNaN(coords[0]) ? coords[0] : 0;
            const y = !isNaN(coords[1]) ? coords[1] : 0;
            const travelCmd = `/travel ${x},${y}`;
            if (activeScriptLabel) activeScriptLabel.innerText = travelCmd;
            await invokeTauri('send_ipc_message', {
                agent: 'scaphandre',
                action: 'travel_to',
                payload: { x, y }
            });
            console.log(`[StreamDeck IPC -> Le Scaphandre] Travel: ${travelCmd}`);
        } else if (type === 'stop') {
            if (activeScriptLabel) activeScriptLabel.innerText = 'STOP';
            await invokeTauri('trigger_emergency_stop');
            console.log("[StreamDeck IPC -> Le Cadran] Arrêt d'urgence déclenché.");
        } else {
            if (activeScriptLabel) activeScriptLabel.innerText = btnData.label;
            await invokeTauri('send_ipc_message', {
                agent: 'scaphandre',
                action: 'custom_action',
                payload: { command: val }
            });
            console.log(`[StreamDeck IPC] Action personnalisée: ${btnData.label}`);
        }
    }

    // Rendu dynamique de la grille selon rows x cols
    function renderGrid() {
        if (!gridContainer) return;
        
        const w = gridConfig.btnWidth;
        const h = gridConfig.btnHeight;

        gridContainer.style.gridTemplateRows = `repeat(${gridConfig.rows}, ${h}px)`;
        gridContainer.style.gridTemplateColumns = `repeat(${gridConfig.cols}, ${w}px)`;

        gridContainer.innerHTML = '';
        const totalSlots = gridConfig.rows * gridConfig.cols;

        const isMini = (w <= 55 || h <= 55);
        const isMedium = (w <= 85 || h <= 85);

        for (let i = 0; i < totalSlots; i++) {
            let btnData;

            // Slot 0 = Toujours CONFIG (F1, à gauche)
            if (i === 0) {
                btnData = defaultButtons[0];
            } 
            // Slot 1 = Toujours STOP (F2, à la place de SALUT, à droite immédiate de CONFIG)
            else if (i === 1) {
                btnData = {
                    id: 'btn-stop',
                    icon: '⏹',
                    label: 'STOP',
                    sub: 'Urgence',
                    shortcut: 'F2',
                    type: 'stop',
                    value: ''
                };
            } 
            // Slots à partir de index 2 = Modifiables par l'utilisateur
            else {
                // Décalage pour utiliser le reste de defaultButtons s'il y en a (ex: TRAVEL TO sur F3)
                btnData = defaultButtons[i - 1] || {
                    id: `btn-custom-${i+1}`,
                    icon: '➕',
                    label: `P${i+1}`,
                    sub: '',
                    shortcut: `F${i+1}`,
                    type: 'chat',
                    value: `Slot ${i+1}`
                };

                if (customButtonsConfig[i]) {
                    btnData = {
                        ...btnData,
                        ...customButtonsConfig[i],
                        id: `btn-custom-${i+1}`
                    };
                }
            }

            const pad = document.createElement('button');
            pad.className = 'deck-pad';
            if (i === 0 || i === 1) pad.classList.add('locked-config');
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
                <div class="long-press-progress"></div>
            `;

            // Gestion de l'Appui Long (2 secondes = 2000 ms)
            let pressTimer = null;
            let isLongPress = false;

            const startPress = (e) => {
                if (e.button !== 0 && e.type === 'pointerdown') return;
                isLongPress = false;
                pad.classList.add('pressing');

                // Ni CONFIG (index 0) ni STOP (index 1) ne déclenchent la modale d'édition
                if (i > 1) {
                    pressTimer = setTimeout(() => {
                        isLongPress = true;
                        pad.classList.remove('pressing');
                        openButtonEditModal(i, btnData);
                    }, 1000);
                }
            };

            const cancelPress = () => {
                if (pressTimer) {
                    clearTimeout(pressTimer);
                    pressTimer = null;
                }
                pad.classList.remove('pressing');
            };

            pad.addEventListener('pointerdown', startPress);
            pad.addEventListener('pointerup', (e) => {
                cancelPress();
                if (!isLongPress) {
                    triggerPadFeedback(pad);
                    executeButtonAction(btnData);
                }
            });
            pad.addEventListener('pointerleave', cancelPress);
            pad.addEventListener('pointercancel', cancelPress);

            gridContainer.appendChild(pad);
        }

        autoAdjustWindowSize(false);
    }

    // Calcule et applique automatiquement la taille idéale de la fenêtre Tauri
    async function autoAdjustWindowSize(isModalOpen = false) {
        const w = gridConfig.btnWidth;
        const h = gridConfig.btnHeight;
        const cols = gridConfig.cols;
        const rows = gridConfig.rows;

        // Largeur = padding latéral (24px) + boutons + gaps (10px par colonne) + marge de sécurité
        const gridWidth = (cols * w) + ((cols - 1) * 10) + 32;
        const targetWidth = Math.max(280, gridWidth);

        // Hauteur de base de la fenêtre
        const gridHeight = (rows * h) + ((rows - 1) * 10);
        let targetHeight = 145 + gridHeight + 34 + 24 + 35;

        // Si une modale est ouverte, on passe la hauteur à 620px pour tout afficher sans scrollbar
        if (isModalOpen) {
            targetHeight = Math.max(620, targetHeight);
        }

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
    loadSavedButtonsConfig();
    renderGrid();

    // Éléments du Flux Visuel
    const streamThumbnailImg = document.getElementById('stream-thumbnail-img');

    // Actualisation périodique du titre, de la tuile active et du nombre de plots de changement de carte
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

            const mapInfo = await invokeTauri('get_current_map_info');
            if (mapInfo && sunNodesBadge) {
                const count = mapInfo.sun_nodes_count || 0;
                const text = count === 1 ? '☀️ 1 plot' : `☀️ ${count} plots`;
                sunNodesBadge.innerText = text;
            }
        } catch (err) {
            console.debug("Erreur rafraîchissement flux visuel / map info:", err);
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

        // Interception des flèches directionnelles pour le swipe opposé de changement de carte
        if (e.key === 'ArrowUp') {
            e.preventDefault();
            invokeTauri('trigger_directional_move', { direction: 'Up' }).then(() => window.focus());
        } else if (e.key === 'ArrowDown') {
            e.preventDefault();
            invokeTauri('trigger_directional_move', { direction: 'Down' }).then(() => window.focus());
        } else if (e.key === 'ArrowLeft') {
            e.preventDefault();
            invokeTauri('trigger_directional_move', { direction: 'Left' }).then(() => window.focus());
        } else if (e.key === 'ArrowRight') {
            e.preventDefault();
            invokeTauri('trigger_directional_move', { direction: 'Right' }).then(() => window.focus());
        }

        // Déclenchement du raccourci pad correspondant (ex: F1, F2, F3, etc.) insensible à la casse
        const pressedKeyUpper = e.key.toUpperCase();
        const allPads = gridContainer?.querySelectorAll('.deck-pad') || [];
        let matchingPad = null;
        allPads.forEach(pad => {
            const padKey = (pad.getAttribute('data-key') || '').toUpperCase();
            if (padKey && padKey === pressedKeyUpper) {
                matchingPad = pad;
            }
        });

        if (matchingPad) {
            e.preventDefault();
            triggerPadFeedback(matchingPad);
            // Simuler la récréation de l'action du pad
            matchingPad.dispatchEvent(new MouseEvent('pointerdown', { bubbles: true, button: 0 }));
            setTimeout(() => {
                matchingPad.dispatchEvent(new MouseEvent('pointerup', { bubbles: true, button: 0 }));
            }, 50);
        }
    });
});
