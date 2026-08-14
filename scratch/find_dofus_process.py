import ctypes
import os
import subprocess

# Tasklist pour trouver le nom exact d'exécutable de Dofus Unity
output = subprocess.check_output("tasklist /FO CSV", shell=True).decode('oem')
print("=== PROCESSUS EN COURS D'EXÉCUTION DÉTECTÉS ===")
matching_procs = []
for line in output.splitlines():
    if any(k in line.lower() for k in ['dofus', 'ankama', 'unity', 'game']):
        matching_procs.append(line)
        print("  -->", line)

if not matching_procs:
    print("  Aucun processus contenant dofus/ankama/unity dans tasklist.")
