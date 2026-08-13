@echo off
setlocal enabledelayedexpansion
title IdleD - Lancement de la Plateforme Multi-Agents
chcp 65001 >nul

echo ====================================================================
echo                   [IdleD Platform Launcher]
echo ====================================================================
echo.

REM 1. Verification de Python
py --version >nul 2>&1
if !ERRORLEVEL! EQU 0 (
    set "PY_CMD=py"
) else (
    python --version >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        set "PY_CMD=python"
    ) else (
        echo [ERREUR] Python n'est pas installe ou n'est pas accessible dans le PATH.
        echo Veuillez installer Python 3.10+ pour executer le harnais multi-agents.
        pause
        exit /b 1
    )
)

REM 2. Repertoire racine du projet
set "PROJECT_ROOT=%~dp0.."
cd /d "%PROJECT_ROOT%"

echo [1/3] Verification de l'environnement virtuel Python...
if not exist "venv" (
    echo [*] Creation de l'environnement virtuel venv...
    !PY_CMD! -m venv venv
)

call venv\Scripts\activate.bat

echo [2/3] Verification des dependances du harnais agentique...
python -m pip install -r agents\requirements.txt --quiet --disable-pip-version-check

echo [3/3] Initialisation de la base de donnees locale SQLite...
if not exist "data\databases" mkdir "data\databases"
if not exist "data\databases\encyclopedia.db" call :init_db

echo.
echo ====================================================================
echo [OK] Environnement IdleD pret.
echo.
echo Options de lancement :
echo   [1] Demarrer le Superviseur Rust / Tauri (UI Overlay) [PAR DEFAUT]
echo   [2] Executer le Harnais Multi-Agents Python en mode Standalone
echo   [3] Lancer la Suite de Tests Unitaires Complete (pytest + cargo test)
echo   [4] Quitter
echo ====================================================================
echo.

set "user_choice=1"
set /p user_choice="Faites votre choix [1-4] (Defaut: 1) : "

if "!user_choice!"=="1" goto option_1
if "!user_choice!"=="2" goto option_2
if "!user_choice!"=="3" goto option_3
if "!user_choice!"=="4" goto option_exit
goto option_1

:option_1
echo [*] Nettoyage des anciennes instances d'IdleD...
taskkill /F /IM idled-backend.exe >nul 2>&1
echo [*] Lancement du Superviseur Tauri...
cd /d "%PROJECT_ROOT%\src-tauri"
call cargo run
pause
goto :eof

:option_2
echo [*] Lancement du test du harnais agentique...
cd /d "%PROJECT_ROOT%"
python agents\brain\pathfinding.py
python agents\motor\bezier_mouse.py
pause
goto :eof

:option_3
echo [*] Execution des tests unitaires Python (pytest)...
cd /d "%PROJECT_ROOT%"
python -m pytest tests/
echo.
echo [*] Execution des tests unitaires Rust (cargo test)...
cd /d "%PROJECT_ROOT%\src-tauri"
cargo test
pause
goto :eof

:option_exit
echo Fermeture...
goto :eof

:init_db
echo [*] Creation de encyclopedia.db avec le schema Grimoire...
python -c "import sqlite3; conn = sqlite3.connect('data/databases/encyclopedia.db'); conn.executescript(open('data/databases/schema.sql', 'r', encoding='utf-8').read()); conn.close(); print('[SQL] Base encyclopedia.db initialisee avec succes.')"
goto :eof
