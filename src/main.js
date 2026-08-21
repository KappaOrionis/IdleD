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
    const mapBonus = document.getElementById('map-bonus');
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
    const groupHarvestConfig = document.getElementById('group-harvest-config');
    const editHarvestCoords = document.getElementById('edit-harvest-coords');
    const groupActionValue = document.getElementById('group-action-value');
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
            id: 'btn-mining',
            icon: '⛏️',
            label: 'MINAGE',
            sub: 'Carte Actuelle',
            shortcut: 'F3',
            type: 'mining_room',
            harvestResources: ['fer'],
            value: 'fer',
            autoEnter: true
        },
        {
            id: 'btn-debug',
            icon: '🔬',
            label: 'DEBUG',
            sub: 'Minage /2',
            shortcut: 'F4',
            type: 'mining_debug',
            harvestResources: ['fer', 'cuivre'],
            value: 'fer,cuivre',
            autoEnter: true
        },
        {
            id: 'btn-travel',
            icon: '🚀',
            label: 'TRAVEL TO',
            sub: '/travel 4,28',
            shortcut: 'F5',
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

    function updateHarvestFormVisibility(selectedType) {
        if (selectedType === 'harvest' || selectedType === 'mining_room' || selectedType === 'mining_debug') {
            if (groupHarvestConfig) groupHarvestConfig.style.display = 'block';
            if (groupActionValue) groupActionValue.style.display = 'none';

            // Pour mining_room et mining_debug, on masque la saisie manuelle de coordonnées
            const coordsGroup = editHarvestCoords?.closest('.form-group');
            if (coordsGroup) {
                coordsGroup.style.display = (selectedType === 'harvest') ? 'block' : 'none';
            }
        } else {
            if (groupHarvestConfig) groupHarvestConfig.style.display = 'none';
            if (groupActionValue) groupActionValue.style.display = 'block';
        }
    }

    editBtnType?.addEventListener('change', (e) => {
        updateHarvestFormVisibility(e.target.value);
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
        
        const type = btnData.type || 'chat';
        if (editBtnType) editBtnType.value = type;
        updateHarvestFormVisibility(type);

        if (editBtnValue) editBtnValue.value = btnData.value || '';
        if (editBtnShortcut) editBtnShortcut.value = btnData.shortcut || `F${slotIndex + 1}`;
        if (editBtnAutoEnter) editBtnAutoEnter.checked = (btnData.autoEnter !== false);

        if (editHarvestCoords) editHarvestCoords.value = btnData.harvestCoords || btnData.value || '4,28';
        const defaultTarget = (type === 'mining_room' || type === 'mining_debug') ? ['fer', 'cuivre'] : ['cuivre', 'fer'];
        const targetResources = (btnData.harvestResources && btnData.harvestResources.length > 0)
            ? btnData.harvestResources
            : defaultTarget;

        document.querySelectorAll('.harvest-resource-cb').forEach(cb => {
            cb.checked = targetResources.includes(cb.value);
        });

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

        const selectedResources = [];
        document.querySelectorAll('.harvest-resource-cb:checked').forEach(cb => {
            selectedResources.push(cb.value);
        });
        const harvestCoords = editHarvestCoords ? editHarvestCoords.value.trim() : '4,28';

        customButtonsConfig[currentEditingSlotIndex] = {
            icon,
            label,
            sub,
            type,
            value,
            shortcut,
            autoEnter,
            harvestCoords,
            harvestResources: selectedResources
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
        } else if (type === 'mining_room' || type === 'mining_debug') {
            const isDebug = (type === 'mining_debug');
            const speedMultiplier = isDebug ? 0.5 : 1.0;
            const resources = (btnData.harvestResources && btnData.harvestResources.length > 0)
                ? btnData.harvestResources
                : ['fer'];
            const resText = resources.join(', ');
            const labelPrefix = isDebug ? '🔬 DEBUG Minage /2' : '⛏️ Minage Carte';
            if (activeScriptLabel) activeScriptLabel.innerText = `${labelPrefix}: [${resText}]`;

            await invokeTauri('set_supervisor_state', { newState: 'Harvesting' });
            await invokeTauri('send_ipc_message', {
                agent: 'cerveau',
                action: 'mine_current_room',
                payload: {
                    resources: resources,
                    speed_multiplier: speedMultiplier,
                    debug_mode: isDebug
                }
            });
            console.log(`[StreamDeck IPC -> Le Cerveau] Macro ${labelPrefix} démarrée pour minerais:`, resources);
        } else if (type === 'harvest') {
            const harvestCoords = btnData.harvestCoords || val || '4,28';
            const coords = harvestCoords.split(',').map(s => parseInt(s.trim(), 10));
            const x = !isNaN(coords[0]) ? coords[0] : 4;
            const y = !isNaN(coords[1]) ? coords[1] : 28;
            const resources = btnData.harvestResources || ['copper_ore', 'iron_ore'];

            if (activeScriptLabel) activeScriptLabel.innerText = `🌾 Récolte [${x},${y}] (${resources.length} res.)`;
            
            // 1. Envoi de la commande de déplacement /travel vers la tuile surveillée
            await invokeTauri('send_ipc_message', {
                agent: 'scaphandre',
                action: 'travel_to',
                payload: { x, y }
            });

            // 2. Activation du mode Récolte multi-agents
            await invokeTauri('send_ipc_message', {
                agent: 'cerveau',
                action: 'start_harvest_mode',
                payload: {
                    target_coords: [x, y],
                    resources: resources
                }
            });
            console.log(`[StreamDeck IPC -> Le Cerveau] Mode Récolte activé sur [${x}, ${y}] avec ressources:`, resources);
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

    async function handlePadPlayPause(pad, btnData) {
        if (btnData.type === 'config') {
            openConfigModal();
            return;
        }
        if (btnData.type === 'stop') {
            handlePadStop(pad, btnData);
            return;
        }

        const isRunning = pad.classList.contains('running');
        const isPaused = pad.classList.contains('paused');
        const statusBadge = pad.querySelector('.pad-status-badge');

        if (isRunning) {
            // Clic Gauche sur Macro Active -> Pause
            pad.classList.remove('running');
            pad.classList.add('paused');
            if (statusBadge) statusBadge.innerText = 'PAUSE';
            if (activeScriptLabel) activeScriptLabel.innerText = `⏸️ Pause: ${btnData.label}`;
            await invokeTauri('set_supervisor_state', { newState: 'Paused' });
            await invokeTauri('send_ipc_message', {
                agent: 'cerveau',
                action: 'pause_macro',
                payload: { id: btnData.id }
            });
            console.log(`[StreamDeck] Clic Gauche -> Macro '${btnData.label}' mise en PAUSE.`);
        } else if (isPaused) {
            // Clic Gauche sur Macro en Pause -> Reprise (Play)
            pad.classList.remove('paused');
            pad.classList.add('running');
            if (statusBadge) statusBadge.innerText = 'RUN';
            if (activeScriptLabel) activeScriptLabel.innerText = `▶️ Reprise: ${btnData.label}`;
            await invokeTauri('set_supervisor_state', { newState: 'Harvesting' });
            await invokeTauri('send_ipc_message', {
                agent: 'cerveau',
                action: 'resume_macro',
                payload: { id: btnData.id }
            });
            console.log(`[StreamDeck] Clic Gauche -> Macro '${btnData.label}' REPRISE.`);
        } else {
            // Clic Gauche sur Macro Inactive -> Démarrage (Play)
            gridContainer?.querySelectorAll('.deck-pad').forEach(p => {
                p.classList.remove('running', 'paused');
            });
            pad.classList.add('running');
            if (statusBadge) statusBadge.innerText = 'RUN';
            await executeButtonAction(btnData);
        }
    }

    async function handlePadStop(pad, btnData) {
        // Clic Droit -> Arrêt Immédiat (Stop)
        pad.classList.remove('running', 'paused');
        pad.classList.add('stopped-flash');
        setTimeout(() => pad.classList.remove('stopped-flash'), 400);

        if (activeScriptLabel) activeScriptLabel.innerText = `⏹️ STOP: ${btnData.label || 'Macro'}`;
        await invokeTauri('trigger_emergency_stop');
        await invokeTauri('send_ipc_message', {
            agent: 'cerveau',
            action: 'stop_macro',
            payload: { id: btnData.id }
        });
        console.log(`[StreamDeck] Clic Droit -> STOP immédiat pour '${btnData.label}'.`);
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
                <span class="pad-status-badge">RUN</span>
                <div class="pad-icon" style="font-size: ${iconSize};">${btnData.icon}</div>
                <div class="pad-label" style="font-size: ${labelSize};">${btnData.label}</div>
                ${showSub ? `<div class="pad-sub">${btnData.sub}</div>` : ''}
                ${!isMini ? `<kbd class="pad-shortcut">${btnData.shortcut}</kbd>` : ''}
                <div class="long-press-progress"></div>
            `;

            // Gestion de l'Appui Long (1 seconde = 1000 ms) pour la configuration
            let pressTimer = null;
            let isLongPress = false;

            const startPress = (e) => {
                if (e.button !== 0) return; // Uniquement clic gauche pour l'appui long
                isLongPress = false;
                pad.classList.add('pressing');

                pressTimer = setTimeout(() => {
                    isLongPress = true;
                    pad.classList.remove('pressing');
                    if (btnData.type === 'config') {
                        openConfigModal();
                    } else {
                        openButtonEditModal(i, btnData);
                    }
                }, 1000);
            };

            const cancelPress = () => {
                if (pressTimer) {
                    clearTimeout(pressTimer);
                    pressTimer = null;
                }
                pad.classList.remove('pressing');
            };

            // 1. Clic Gauche : Play / Pause (court) ou Configuration (long)
            pad.addEventListener('pointerdown', startPress);
            pad.addEventListener('pointerup', (e) => {
                if (e.button !== 0) return;
                cancelPress();
                if (!isLongPress) {
                    triggerPadFeedback(pad);
                    handlePadPlayPause(pad, btnData);
                }
            });
            pad.addEventListener('pointerleave', cancelPress);
            pad.addEventListener('pointercancel', cancelPress);

            // 2. Clic Droit : Stop Immédiat
            pad.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                cancelPress();
                handlePadStop(pad, btnData);
            });

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
        let targetHeight = 195 + gridHeight + 34 + 24 + 35;

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
    const streamUnavailablePlaceholder = document.getElementById('stream-unavailable-placeholder');

    // Actualisation périodique du titre, du flux vidéo et des métadonnées de la carte
    async function updateActiveWindowStream() {
        try {
            const thumb = await invokeTauri('get_stream_thumbnail');
            if (thumb) {
                if (previewWindowTitle) {
                    previewWindowTitle.innerText = thumb.title || 'Détection...';
                }
                if (thumb.is_valid && thumb.data_url && streamThumbnailImg) {
                    streamThumbnailImg.src = thumb.data_url;
                    streamThumbnailImg.style.display = 'block';
                    if (streamUnavailablePlaceholder) {
                        streamUnavailablePlaceholder.style.display = 'none';
                    }
                } else {
                    if (streamThumbnailImg) {
                        streamThumbnailImg.src = '';
                        streamThumbnailImg.style.display = 'none';
                    }
                    if (streamUnavailablePlaceholder) {
                        streamUnavailablePlaceholder.style.display = 'flex';
                    }
                }
            } else {
                if (streamThumbnailImg) {
                    streamThumbnailImg.src = '';
                    streamThumbnailImg.style.display = 'none';
                }
                if (streamUnavailablePlaceholder) {
                    streamUnavailablePlaceholder.style.display = 'flex';
                }
            }

            const mapInfo = await invokeTauri('get_current_map_info');
            if (mapInfo && mapInfo.is_detected && mapInfo.pos_x !== null && mapInfo.pos_y !== null) {
                if (mapCoords) mapCoords.innerText = `[${mapInfo.pos_x}, ${mapInfo.pos_y}]`;
                if (mapZoneName) mapZoneName.innerText = mapInfo.zone_name || '--';
                if (mapLevel) mapLevel.innerText = mapInfo.area_level ? `Niv. ${mapInfo.area_level}` : '--';
                if (mapBonus) mapBonus.innerText = mapInfo.zone_bonus || '--';
                if (sunNodesBadge) {
                    const count = mapInfo.sun_nodes_count || 0;
                    sunNodesBadge.innerText = count === 1 ? '1 plot' : `${count} plots`;
                }
            } else {
                if (mapCoords) mapCoords.innerText = '--';
                if (mapZoneName) mapZoneName.innerText = '--';
                if (mapLevel) mapLevel.innerText = '--';
                if (mapBonus) mapBonus.innerText = '--';
                if (sunNodesBadge) sunNodesBadge.innerText = '--';
            }
        } catch (err) {
            console.debug("Erreur rafraîchissement flux visuel / map info:", err);
        }
    }
    updateActiveWindowStream();
    setInterval(updateActiveWindowStream, 400);

    // =========================================================================
    // Gestion de la Synthèse Cartographique & SLAM Cognitif
    // =========================================================================
    const mapSynthModal = document.getElementById('map-synthesis-modal');
    const btnOpenMapSynth = document.getElementById('btn-open-map-synth');
    const tileInfoBadge = document.getElementById('tile-info-badge');
    const footerMapSynthBtn = document.getElementById('footer-map-synth-btn');
    const btnCloseMapSynth = document.getElementById('btn-close-map-synth');
    const btnCloseMapSynthAction = document.getElementById('btn-close-map-synth-action');
    const btnSynthInspectRoom = document.getElementById('btn-synth-inspect-room');

    const synthZoneName = document.getElementById('synth-zone-name');
    const synthZoneSub = document.getElementById('synth-zone-sub');
    const synthCoordsVal = document.getElementById('synth-coords-val');
    const synthLevelVal = document.getElementById('synth-level-val');
    const synthOresList = document.getElementById('synth-ores-list');
    const synthOresCount = document.getElementById('synth-ores-count');
    const synthExitsList = document.getElementById('synth-exits-list');
    const synthExitsCount = document.getElementById('synth-exits-count');
    const synthMobsList = document.getElementById('synth-mobs-list');
    const synthMobsCount = document.getElementById('synth-mobs-count');
    const synthRadarGrid = document.getElementById('synth-radar-grid');

    // Base de Connaissance Locale / Synthèse Dynamique par Coordonnées
    const SLAM_MAP_DATABASE = {
        "-3,9": {
            zone: "Mine Istairameur",
            sub: "Étage Souterrain • Salle Centrale (Baril TNT)",
            coords: "[-3, 9]",
            level: "Niv. 120",
            ores: [
                { name: "Bronze (Niv. 40)", count: 6, status: "3 Disponibles • 3 Épuisés", pillClass: "pill-avail" },
                { name: "Fer (Niv. 1)", count: 1, status: "Disponible", pillClass: "pill-avail" }
            ],
            exits: [
                { name: "Sortie Nord (Galerie)", target: "[-3, 8]", type: "Nord ↑", pillClass: "pill-exit" },
                { name: "Sortie Sud (Voie ferrée)", target: "[-3, 10]", type: "Sud ↓", pillClass: "pill-exit" },
                { name: "Plots de Soleil (☀️)", target: "Transitions Directes", type: "2 Soleils", pillClass: "pill-exit" }
            ],
            mobs: [
                { name: "Mineurs Sombres", level: "Niv. 35 - 48", threat: "🛡️ Passif", pillClass: "pill-passive" },
                { name: "Chauve-souris des Mines", level: "Niv. 28 - 36", threat: "🛡️ Neutre", pillClass: "pill-passive" }
            ]
        },
        "4,28": {
            zone: "Amakna (Souterrains)",
            sub: "Mine des Craqueleurs • Salle d'Entrée",
            coords: "[4, 28]",
            level: "Niv. 1",
            ores: [
                { name: "Cuivre (Niv. 20)", count: 4, status: "Disponible", pillClass: "pill-avail" },
                { name: "Fer (Niv. 1)", count: 3, status: "Disponible", pillClass: "pill-avail" }
            ],
            exits: [
                { name: "Passage Est", target: "[5, 28]", type: "Est →", pillClass: "pill-exit" },
                { name: "Galerie Ouest", target: "[3, 28]", type: "Ouest ←", pillClass: "pill-exit" }
            ],
            mobs: [
                { name: "Arakné Mineuse", level: "Niv. 12 - 18", threat: "🛡️ Passif", pillClass: "pill-passive" }
            ]
        }
    };

    function renderMapSynthesis(tileKey = "-3,9") {
        const data = SLAM_MAP_DATABASE[tileKey] || {
            zone: mapZoneName?.innerText || "Zone Inconnue",
            sub: "Tuile Découverte",
            coords: mapCoords?.innerText || "[0, 0]",
            level: mapLevel?.innerText || "Niv. 1",
            ores: [
                { name: "Bronze (Niv. 40)", count: 6, status: "6 Filons Répertoriés", pillClass: "pill-avail" }
            ],
            exits: [
                { name: "Sorties Détectées", target: "Graphe", type: "Soleils ☀️", pillClass: "pill-exit" }
            ],
            mobs: [
                { name: "Aucune menace détectée", level: "Calme", threat: "🛡️ Sûr", pillClass: "pill-passive" }
            ]
        };

        if (synthZoneName) synthZoneName.innerText = data.zone;
        if (synthZoneSub) synthZoneSub.innerText = data.sub;
        if (synthCoordsVal) synthCoordsVal.innerText = data.coords;
        if (synthLevelVal) synthLevelVal.innerText = data.level;

        // Rendu Ressources
        if (synthOresList) {
            synthOresList.innerHTML = data.ores.map(o => `
                <div class="synth-item-row">
                    <span class="synth-item-name">⛏️ ${o.name}</span>
                    <span class="synth-status-pill ${o.pillClass}">${o.status}</span>
                </div>
            `).join('');
        }
        if (synthOresCount) {
            const totalCount = data.ores.reduce((acc, curr) => acc + (curr.count || 1), 0);
            synthOresCount.innerText = `${totalCount} filons`;
        }

        // Rendu Sorties
        if (synthExitsList) {
            synthExitsList.innerHTML = data.exits.map(e => `
                <div class="synth-item-row">
                    <span class="synth-item-name">🚪 ${e.name}</span>
                    <span class="synth-status-pill ${e.pillClass}">${e.type} (${e.target})</span>
                </div>
            `).join('');
        }
        if (synthExitsCount) {
            synthExitsCount.innerText = `${data.exits.length} sorties`;
        }

        // Rendu Monstres
        if (synthMobsList) {
            synthMobsList.innerHTML = data.mobs.map(m => `
                <div class="synth-item-row">
                    <span class="synth-item-name">👾 ${m.name} (${m.level})</span>
                    <span class="synth-status-pill ${m.pillClass}">${m.threat}</span>
                </div>
            `).join('');
        }
        if (synthMobsCount) {
            synthMobsCount.innerText = `${data.mobs.length} groupes`;
        }

        // Rendu Radar 3x3
        renderRadarGrid(data.coords);
    }

    function renderRadarGrid(currentCoordsStr) {
        if (!synthRadarGrid) return;
        const match = currentCoordsStr.match(/\[?\s*(-?\d+)\s*,\s*(-?\d+)\s*\]?/);
        const curX = match ? parseInt(match[1], 10) : -3;
        const curY = match ? parseInt(match[2], 10) : 9;

        const cells = [];
        for (let dy = -1; dy <= 1; dy++) {
            for (let dx = -1; dx <= 1; dx++) {
                const tx = curX + dx;
                const ty = curY + dy;
                const key = `${tx},${ty}`;
                const isCurrent = (dx === 0 && dy === 0);
                const hasData = SLAM_MAP_DATABASE[key] !== undefined;

                cells.push(`
                    <div class="radar-tile-cell ${isCurrent ? 'current-tile' : ''}" data-key="${key}">
                        <span class="radar-tile-coords">[${tx}, ${ty}]</span>
                        <span class="radar-tile-sub">${isCurrent ? '📍 ICI' : (hasData ? '⛏️ 6 filons' : '❓ Inconnu')}</span>
                    </div>
                `);
            }
        }
        synthRadarGrid.innerHTML = cells.join('');

        synthRadarGrid.querySelectorAll('.radar-tile-cell').forEach(cell => {
            cell.addEventListener('click', () => {
                const k = cell.getAttribute('data-key');
                if (k) renderMapSynthesis(k);
            });
        });
    }

    function openMapSynthesis() {
        if (!mapSynthModal) return;
        const curCoords = mapCoords?.innerText.replace(/[\[\]]/g, '').trim() || "-3,9";
        renderMapSynthesis(curCoords);
        mapSynthModal.classList.add('open');
    }

    function closeMapSynthesis() {
        if (mapSynthModal) mapSynthModal.classList.remove('open');
    }

    if (tileInfoBadge) tileInfoBadge.addEventListener('click', openMapSynthesis);
    if (btnOpenMapSynth) btnOpenMapSynth.addEventListener('click', (e) => {
        e.stopPropagation();
        openMapSynthesis();
    });
    if (footerMapSynthBtn) footerMapSynthBtn.addEventListener('click', openMapSynthesis);
    if (btnCloseMapSynth) btnCloseMapSynth.addEventListener('click', closeMapSynthesis);
    if (btnCloseMapSynthAction) btnCloseMapSynthAction.addEventListener('click', closeMapSynthesis);

    if (btnSynthInspectRoom) {
        btnSynthInspectRoom.addEventListener('click', () => {
            if (activeScriptLabel) {
                activeScriptLabel.innerText = "🔍 Inspection Filon (Noxine + Scaphandre)";
            }
            // Feedback visuel et fermeture
            btnSynthInspectRoom.innerText = "⚡ Balayage en cours...";
            setTimeout(() => {
                btnSynthInspectRoom.innerText = "🔍 Inspecter la Salle (Noxine + Scaphandre)";
                closeMapSynthesis();
            }, 800);
        });
    }

    // Fermeture en cliquant à l'extérieur
    window.addEventListener('click', (e) => {
        if (e.target === mapSynthModal) {
            closeMapSynthesis();
        }
    });

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

        // Touche 'M' pour basculer la Synthèse Cartographique
        if ((e.key === 'm' || e.key === 'M') && !document.querySelector('input:focus')) {
            e.preventDefault();
            if (mapSynthModal?.classList.contains('open')) {
                closeMapSynthesis();
            } else {
                openMapSynthesis();
            }
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
            matchingPad.dispatchEvent(new MouseEvent('pointerdown', { bubbles: true, button: 0 }));
            setTimeout(() => {
                matchingPad.dispatchEvent(new MouseEvent('pointerup', { bubbles: true, button: 0 }));
            }, 50);
        }
    });
});
