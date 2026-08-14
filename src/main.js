document.addEventListener('DOMContentLoaded', () => {
    console.log("[IdleD StreamDeck] Console StreamDeck avec IPC Bridge & Focus Automatique.");

    // Helper d'appel IPC Tauri sécurisé avec fallback navigateur
    async function invokeTauri(cmd, args = {}) {
        if (window.__TAURI__ && window.__TAURI__.invoke) {
            try {
                return await window.__TAURI__.invoke(cmd, args);
            } catch (err) {
                console.warn(`[Tauri IPC] Commande '${cmd}' :`, err);
                return null;
            }
        }
        return null;
    }

    // Éléments UI Globaux
    const statusBadge = document.getElementById('supervisor-status');
    const activeScriptLabel = document.getElementById('active-script');
    const lastKeyBadge = document.getElementById('last-key');
    const gridContainer = document.getElementById('streamdeck-grid');
    const subtitleInfo = document.getElementById('deck-subtitle-info');

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

    // Dimensions de la grille par défaut (2 lignes x 3 colonnes)
    let gridConfig = {
        rows: 2,
        cols: 3
    };

    // Liste des boutons configurables
    const defaultButtons = [
        {
            id: 'btn-config',
            icon: '⚙️',
            label: 'CONFIG',
            sub: 'Lignes & Colonnes',
            shortcut: 'F1',
            action: openConfigModal
        },
        {
            id: 'btn-salut',
            icon: '💬',
            label: 'SALUT',
            sub: 'Écris "salut" dans le chat',
            shortcut: 'F2',
            action: sendSalutChat
        },
        {
            id: 'btn-travel',
            icon: '🚀',
            label: 'TRAVEL TO',
            sub: 'Envoie /travel x,y',
            shortcut: 'F3',
            action: sendTravelToChat
        },
        {
            id: 'btn-stop',
            icon: '⏹',
            label: 'STOP URGENCE',
            sub: 'Interruption 0ms',
            shortcut: 'F4',
            action: triggerEmergencyStop
        }
    ];

    function openConfigModal() {
        if (inputRows) inputRows.value = gridConfig.rows;
        if (inputCols) inputCols.value = gridConfig.cols;
        configModal?.classList.add('open');
    }

    function closeConfigModal() {
        configModal?.classList.remove('open');
    }

    btnCloseModal?.addEventListener('click', closeConfigModal);

    btnSaveConfig?.addEventListener('click', () => {
        const rows = parseInt(inputRows.value, 10) || 2;
        const cols = parseInt(inputCols.value, 10) || 3;
        
        gridConfig.rows = Math.max(1, Math.min(6, rows));
        gridConfig.cols = Math.max(1, Math.min(6, cols));

        renderGrid();
        closeConfigModal();
        if (statusBadge) statusBadge.innerText = `Grille réconfigurée: ${gridConfig.rows}x${gridConfig.cols}`;
    });

    function triggerPadFeedback(padElement) {
        if (!padElement) return;
        padElement.classList.add('pressed');
        setTimeout(() => {
            padElement.classList.remove('pressed');
        }, 200);
    }

    async function sendSalutChat() {
        if (statusBadge) statusBadge.innerText = 'Focus Win32 & Chat: "salut"';
        if (activeScriptLabel) activeScriptLabel.innerText = 'Écrit: salut';
        
        await invokeTauri('send_ipc_message', {
            agent: 'scaphandre',
            action: 'send_chat_message',
            payload: { text: 'salut' }
        });
        console.log("[StreamDeck IPC -> Le Scaphandre] Message 'salut' transmis.");
    }

    async function sendTravelToChat() {
        const travelCmd = "/travel 4,28";
        if (statusBadge) statusBadge.innerText = `Focus Win32 & Chat: "${travelCmd}"`;
        if (activeScriptLabel) activeScriptLabel.innerText = `Écrit: ${travelCmd}`;
        
        await invokeTauri('send_ipc_message', {
            agent: 'scaphandre',
            action: 'travel_to',
            payload: { x: 4, y: 28 }
        });
        console.log(`[StreamDeck IPC -> Le Scaphandre] Commande '${travelCmd}' transmise.`);
    }

    async function triggerEmergencyStop() {
        if (statusBadge) statusBadge.innerText = 'FSM: Arrêt Urgence (EmergencyStop)';
        if (activeScriptLabel) activeScriptLabel.innerText = 'Commande interrompue';
        
        await invokeTauri('trigger_emergency_stop');
        console.log("[StreamDeck IPC -> Le Cadran] Arrêt d'urgence déclenché.");
    }

    // Rendu dynamique de la grille selon rows x cols
    function renderGrid() {
        if (!gridContainer) return;
        
        gridContainer.style.gridTemplateRows = `repeat(${gridConfig.rows}, 1fr)`;
        gridContainer.style.gridTemplateColumns = `repeat(${gridConfig.cols}, 1fr)`;

        gridContainer.innerHTML = '';
        const totalSlots = gridConfig.rows * gridConfig.cols;

        if (subtitleInfo) {
            subtitleInfo.innerText = `Grille active : ${gridConfig.rows} ligne(s) × ${gridConfig.cols} colonne(s) (${totalSlots} boutons)`;
        }

        for (let i = 0; i < totalSlots; i++) {
            const btnData = defaultButtons[i] || {
                id: `btn-custom-${i+1}`,
                icon: '➕',
                label: `SLOT ${i+1}`,
                sub: 'Libre / Configurable',
                shortcut: `F${i+1}`,
                action: () => {
                    if (statusBadge) statusBadge.innerText = `Bouton ${i+1} activé`;
                }
            };

            const pad = document.createElement('button');
            pad.className = 'deck-pad';
            pad.id = btnData.id;
            pad.setAttribute('data-key', btnData.shortcut);

            pad.innerHTML = `
                <div class="pad-icon">${btnData.icon}</div>
                <div class="pad-label">${btnData.label}</div>
                <div class="pad-sub">${btnData.sub}</div>
                <kbd class="pad-shortcut">${btnData.shortcut}</kbd>
            `;

            pad.addEventListener('click', () => {
                triggerPadFeedback(pad);
                if (btnData.action) btnData.action();
            });

            gridContainer.appendChild(pad);
        }
    }

    // Initialisation de la grille
    renderGrid();

    // Raccourcis clavier globaux
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

        const matchingPad = gridContainer?.querySelector(`[data-key="${e.key}"]`);
        if (matchingPad) {
            e.preventDefault();
            matchingPad.click();
        }
    });
});
