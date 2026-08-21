# ADR-0004: Adoption de RapidOCR (ONNX Runtime) pour la Reconnaissance Textuelle

## Statut

Accepté

## Contexte

IdleD nécessite une reconnaissance optique de caractères (OCR) précise, réactive et autonome pour :
- Décoder les infobulles (tooltips) apparaissant au survol de la souris (nature de la ressource, niveau requis, état épuisé).
- Reconnaître les coordonnées et zones dans l'en-tête du HUD de Dofus Unity.
- Analyser les canaux de discussion (chat) pour détecter les messages privés, mentions de modération et alertes de combat.

Plusieurs moteurs OCR ont été évalués :
1. **Tesseract (`pytesseract`)** : Moteur historique nécessitant des binaires C++ système externes (`tesseract.exe`) et des variables d'environnement Windows.
2. **RapidOCR (`rapidocr-onnxruntime`)** : Moteur moderne basé sur les modèles PaddleOCR exécutés via ONNX Runtime en inférence locale.
3. **EasyOCR** : Moteur basé sur PyTorch, très précis mais nécessitant une empreinte mémoire lourde (> 1.5 Go de dépendances).

## Facteurs de Décision

- **100% Hors-ligne & Sécurité** : Aucune dépendance externe ni appel réseau d'API cloud (Directive `.agents/AGENTS.md`).
- **Autonomie & Portabilité** : Installation complète via `pip` sans installateur système externe tiers sous Windows.
- **Performance & Latence** : Inférence CPU < 15 ms par infobulle, compatible avec la boucle motrice temps réel.
- **Précision** : Excellente reconnaissance des textes courts multi-lignes sur fond sombre/semi-transparent.

## Options Considérées

### Option 1: Tesseract (`pytesseract`)
- **Avantages** : Très répandu, supporte les langues multiples.
- **Inconvénients** : Dépendance sur un exécutable Windows externe non packagé dans `pip`, configuration complexe du chemin `tesseract_cmd`.

### Option 2: RapidOCR (`rapidocr-onnxruntime`) [Sélectionné]
- **Avantages** : 100% embarqué via `pip`, modèles ONNX pré-packagés, zéro installation externe, inférence ultra-rapide sur CPU, excellente robustesse sur les caractères accentués français et chiffres.
- **Inconvénients** : Légère empreinte de modèles ONNX (~12 Mo au total).

### Option 3: EasyOCR
- **Avantages** : Détection PyTorch de pointe.
- **Inconvénients** : Dépendances PyTorch très lourdes (> 1 Go), temps de chargement initial élevé.

## Décision

Nous adoptons **RapidOCR via `rapidocr-onnxruntime`** comme moteur OCR principal dans le micro-agent de perception visuelle (**La Noxine**), encapsulé dans `agents/vision/ocr_engine.py`.

## Conséquences

### Positives
- Reconnaissance textuelle complète et robuste de toutes les infobulles et coordonnées en jeu.
- Solution 100% autonome et portable sur Windows sans configuration manuelle.
- Faible consommation CPU et mémoire.

### Négatives / Risques
- Nécessite la présence des fichiers ONNX fournis dans la bibliothèque Python.
- Atténuation : Mécanisme de repli défensif intégré en cas d'image non exploitable.
