# Script de Lancement PowerShell pour IdleD (Windows)
$ErrorActionPreference = "Stop"

Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "                  ◈ IdleD Platform Launcher ◈" -ForegroundColor Yellow
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""

$ScriptDir = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
$ProjectRoot = Resolve-Path "$ScriptDir\.."
Set-Location $ProjectRoot

# 1. Vérification Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[1/3] Python détecté : $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERREUR] Python n'a pas été trouvé dans le PATH système." -ForegroundColor Red
    Exit 1
}

# 2. Venv & Dépendances
if (-not (Test-Path "$ProjectRoot\venv")) {
    Write-Host "[*] Création de l'environnement virtuel venv..." -ForegroundColor Yellow
    python -m venv "$ProjectRoot\venv"
}

$VenvPython = "$ProjectRoot\venv\Scripts\python.exe"
Write-Host "[2/3] Installation / Vérification des dépendances Python..." -ForegroundColor Green
& $VenvPython -m pip install -r "$ProjectRoot\agents\requirements.txt" --quiet

# 3. SQLite Database
$DbDir = "$ProjectRoot\data\databases"
if (-not (Test-Path $DbDir)) {
    New-Item -ItemType Directory -Path $DbDir | Out-Null
}

$DbPath = "$DbDir\encyclopedia.db"
if (-not (Test-Path $DbPath)) {
    Write-Host "[3/3] Initialisation de la base SQLite encyclopedia.db..." -ForegroundColor Yellow
    $SchemaScript = Get-Content "$ProjectRoot\data\databases\schema.sql" -Raw
    & $VenvPython -c "import sqlite3; conn = sqlite3.connect(r'$DbPath'); conn.executescript('''$SchemaScript'''); conn.close(); print('[SQL] Database initialisée.')"
} else {
    Write-Host "[3/3] Base de données SQLite détectée." -ForegroundColor Green
}

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  [1] Lancer le Superviseur Rust / Tauri (UI Overlay) [PAR DÉFAUT]" -ForegroundColor White
Write-Host "  [2] Tester le Harnais Agents Python" -ForegroundColor White
Write-Host "  [3] Lancer la Suite de Tests Unitaires Complète (pytest + cargo test)" -ForegroundColor White
Write-Host "  [4] Quitter" -ForegroundColor White
Write-Host "====================================================================" -ForegroundColor Cyan

$Choice = Read-Host "Faites votre choix [1-4] (Défaut: 1)"
if ([string]::IsNullOrWhiteSpace($Choice)) {
    $Choice = "1"
}

switch ($Choice) {
    "1" {
        Write-Host "[*] Lancement du Superviseur Tauri..." -ForegroundColor Yellow
        Set-Location "$ProjectRoot\src-tauri"
        cargo run
    }
    "2" {
        Write-Host "[*] Exécution du test des agents..." -ForegroundColor Yellow
        & $VenvPython "$ProjectRoot\agents\brain\pathfinding.py"
        & $VenvPython "$ProjectRoot\agents\motor\bezier_mouse.py"
    }
    "3" {
        Write-Host "[*] Exécution des tests unitaires Python (pytest)..." -ForegroundColor Yellow
        & $VenvPython -m pytest "$ProjectRoot\tests"
        Write-Host "[*] Exécution des tests unitaires Rust (cargo test)..." -ForegroundColor Yellow
        Set-Location "$ProjectRoot\src-tauri"
        cargo test
    }
    Default {
        Write-Host "Fermeture." -ForegroundColor Gray
    }
}
