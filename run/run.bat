@echo off
TITLE IdleD - Lancement de la Plateforme Multi-Agents
CHCP 65001 > NUL
COLOR 0A

echo ====================================================================
echo                   ◈ IdleD Platform Launcher ◈
echo ====================================================================
echo.

:: Vérification de la présence de Python
python --version >NUL 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] Python n'est pas installe ou n'est pas accessible dans le PATH.
    echo Veuillez installer Python 3.10+ pour exécuter le harnais multi-agents.
    pause
    exit /b 1
)

:: Répertoire racine du projet
set "PROJECT_ROOT=%~dp0.."
cd /d "%PROJECT_ROOT%"

echo [1/3] Verification de l'environnement virtuel Python...
if not exist "venv" (
    echo [*] Creation de l'environnement virtuel venv...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo [2/3] Verification des dependances du harnais agentique...
pip install -r agents\requirements.txt --quiet --disable-pip-version-check

echo [3/3] Initialisation de la base de donnees locale SQLite...
if not exist "data\databases" mkdir "data\databases"
if not exist "data\databases\encyclopedia.db" (
    echo [*] Creation de encyclopedia.db avec le schema Grimoire...
    python -c "import sqlite3; conn = sqlite3.connect('data/databases/encyclopedia.db'); conn.executescript(open('data/databases/schema.sql', 'r', encoding='utf-8').read()); conn.close(); print('[SQL] Base encyclopedia.db initialisee avec succes.')"
)

echo.
echo ====================================================================
echo [OK] Environnement IdleD pret.
echo.
echo Options de lancement :
echo   [1] Demarrer le Superviseur Rust / Tauri (UI Overlay)
echo   [2] Executer le Harnais Multi-Agents Python en mode Standalone
echo   [3] Quitter
echo ====================================================================
echo.

set /p choice="Faites votre choix [1-3] : "

if "%choice%"=="1" (
    echo [*] Lancement du Superviseur Tauri...
    cd /d "%PROJECT_ROOT%\src-tauri"
    cargo run
) else if "%choice%"=="2" (
    echo [*] Lancement du test du harnais agentique...
    cd /d "%PROJECT_ROOT%"
    python agents\brain\pathfinding.py
    python agents\motor\bezier_mouse.py
    pause
) else (
    echo Exiting...
)
