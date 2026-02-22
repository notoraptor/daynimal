# Guide de developpement et test Android sur Windows

Guide complet pour compiler l'APK Daynimal, configurer l'emulateur Android, et tester l'interface sur une machine Windows.

**Derniere mise a jour** : 2026-02-22 11:17

---

## Prerequis

| Outil | Version testee | Installation |
|-------|---------------|--------------|
| **Python** | 3.12+ | python.org |
| **uv** | 0.6+ | `pip install uv` ou [docs](https://docs.astral.sh/uv/) |
| **Git Bash** | (fourni avec Git for Windows) | git-scm.com |
| **Android Studio** | Hedgehog+ | developer.android.com |
| **Java JDK** | 17+ | Auto-installe par `flet build` |

> **Note** : Flet CLI installe automatiquement le JDK et le SDK Android au premier build. Android Studio est necessaire uniquement pour creer l'AVD (emulateur).

---

## 1. Installation de l'environnement

### 1.1. Cloner et installer les dependances

```bash
git clone <repo-url>
cd daynimal
uv sync
```

### 1.2. Configurer Android Studio (une seule fois)

1. Installer Android Studio depuis developer.android.com
2. Au premier lancement, installer les SDK recommandes (API 35)
3. Ouvrir **Tools > Device Manager** et creer un AVD :
   - Device : **Pixel 6** (ou similaire)
   - System Image : **API 35 x86_64** (avec Google APIs)
   - Nom AVD : `daynimal_test`
4. Reperer le chemin du SDK Android installe (ex: `C:\Users\<user>\AppData\Local\Android\Sdk` ou `~/Android/Sdk`)

> **Note** : sur cette machine, `$ANDROID_HOME` n'est PAS defini. Toutes les commandes ci-dessous utilisent des variables shell explicites. Voir `CLAUDE.md` pour les chemins exacts.

### 1.3. Definir les chemins et verifier l'installation

```bash
# Definir les chemins (obligatoire dans chaque terminal)
ADB="$HOME/Android/Sdk/platform-tools/adb"
EMULATOR="$HOME/Android/Sdk/emulator/emulator"

# Verifier que adb est accessible
"$ADB" version

# Verifier que l'emulateur est accessible
"$EMULATOR" -list-avds
# Doit afficher : daynimal_test
```

---

## 2. Compilation de l'APK

### 2.1. Commande de build

```bash
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run flet build apk --no-rich-output
```

**Flags importants** :
- `PYTHONUTF8=1` + `PYTHONIOENCODING=utf-8` : evite les erreurs d'encodage sur Windows
- `--no-rich-output` : desactive les spinners Rich qui polluent les logs

**Duree** : ~1-2 min (premier build plus long car installe JDK + SDK).

### 2.2. Resultat

Les APKs sont generes dans `build/apk/` :
- `app-arm64-v8a-release.apk` — appareils ARM 64-bit (la plupart des telephones modernes)
- `app-armeabi-v7a-release.apk` — appareils ARM 32-bit (anciens telephones)
- `app-x86_64-release.apk` — emulateur x86_64

### 2.3. Configuration du build

La configuration Flet est dans `pyproject.toml` :

```toml
[tool.flet]
org = "com.daynimal"
product = "Daynimal"

[tool.flet.app]
module = "app"
path = "daynimal"

[tool.flet.android]
split_per_abi = true    # Genere un APK par architecture

[tool.flet.android.permission]
"android.permission.INTERNET" = true
```

### 2.4. En cas d'erreur de build

| Erreur | Solution |
|--------|----------|
| Encodage UTF-8 | Verifier `PYTHONUTF8=1 PYTHONIOENCODING=utf-8` |
| JDK introuvable | Flet l'installe automatiquement, relancer le build |
| SDK introuvable | Verifier les chemins SDK ou laisser Flet installer |
| `flet` introuvable | `uv sync` pour reinstaller les dependances |

---

## 3. Lancer l'emulateur

### 3.1. Demarrer l'emulateur (mode visible — avec fenetre)

Par defaut, l'emulateur s'ouvre avec une fenetre visible ou l'on peut interagir directement (souris, clavier) :

```bash
# Lancer l'emulateur avec fenetre visible (RECOMMANDE pour le developpement)
"$EMULATOR" -avd daynimal_test -no-audio

# Attendre que l'emulateur soit pret (dans un autre terminal)
"$ADB" wait-for-device
```

> **Note** : la commande `emulator` bloque le terminal. Ouvrir un **second terminal** pour les commandes ADB. Alternativement, ajouter `&` a la fin pour lancer en arriere-plan, mais la fenetre sera quand meme visible.

### 3.2. Demarrer l'emulateur (mode headless — sans fenetre)

Le mode headless est utile pour les scripts CI ou quand Claude Code execute les tests automatiquement :

```bash
# Lancer sans fenetre (mode headless)
"$EMULATOR" -avd daynimal_test -no-audio -no-window &

# Attendre que l'emulateur soit pret
"$ADB" wait-for-device
```

> **Quand utiliser quel mode ?**
> - **Mode visible** : developpement interactif, debug visuel, tester le toucher/scroll manuellement
> - **Mode headless** (`-no-window`) : scripts automatises, CI/CD, tests via ADB uniquement

### 3.3. Options utiles de l'emulateur

| Option | Effet |
|--------|-------|
| `-no-audio` | Desactive l'audio (evite les erreurs audio sur certaines machines) |
| `-no-window` | Mode headless, pas de fenetre affichee |
| `-no-snapshot-load` | Demarre sans restaurer l'etat precedent (clean boot) |
| `-wipe-data` | Remet l'emulateur a zero (utile pour tester le premier lancement) |
| `-gpu auto` | Utilise le GPU hardware si disponible (meilleures performances) |

### 3.4. Verifier que l'emulateur est connecte

```bash
"$ADB" devices
# Doit afficher :
# emulator-5554   device
```

---

## 4. Installer et lancer l'app

### 4.1. Installer l'APK

```bash
# Pour l'emulateur x86_64
"$ADB" install -r build/apk/app-x86_64-release.apk
```

- `-r` : remplace l'installation precedente si elle existe

### 4.2. Lancer l'app

```bash
"$ADB" shell monkey -p com.daynimal.daynimal -c android.intent.category.LAUNCHER 1
```

### 4.3. Forcer l'arret et relancer

```bash
# Forcer l'arret
"$ADB" shell am force-stop com.daynimal.daynimal

# Relancer
"$ADB" shell monkey -p com.daynimal.daynimal -c android.intent.category.LAUNCHER 1
```

### 4.4. Desinstaller l'app (pour tester le premier lancement)

```bash
"$ADB" uninstall com.daynimal.daynimal
```

---

## 5. Interagir avec l'emulateur via ADB

### 5.1. Prendre un screenshot

```bash
# Sauvegarder dans tmp/ (git-ignored)
"$ADB" exec-out screencap -p > tmp/screenshot.png
```

> **Important** : toujours sauvegarder dans `tmp/` pour eviter de committer les screenshots.

### 5.2. Consulter les logs

```bash
# Logs filtres (Flutter + Python + erreurs)
"$ADB" logcat -d | grep -i "flutter\|python\|error" | grep -v "audit\|InetDiag"

# Logs en temps reel
"$ADB" logcat | grep -i "flutter\|python\|error" | grep -v "audit\|InetDiag"

# Effacer les logs (avant un test)
"$ADB" logcat -c
```

### 5.3. Reperer un widget a l'ecran (UI Automator)

Flet utilise Flutter pour le rendu, donc les widgets ne sont pas des vues Android natives. Cependant, UI Automator peut identifier certains elements :

```bash
# Dumper la hierarchie UI dans un fichier XML
"$ADB" shell uiautomator dump //sdcard/ui.xml

# Lire le fichier XML
"$ADB" shell cat //sdcard/ui.xml
```

> **Note Windows/Git Bash** : utiliser `//sdcard/` (double slash) pour eviter que MSYS convertisse le chemin.

Le XML contient des elements avec attributs `bounds="[left,top][right,bottom]"` qu'on peut utiliser pour calculer les coordonnees de tap.

### 5.4. Cliquer sur un element

Flet/Flutter rend l'UI dans un canvas unique, donc on doit taper a des coordonnees precises :

```bash
# 1. Dumper la hierarchie UI
"$ADB" shell uiautomator dump //sdcard/ui.xml && "$ADB" shell cat //sdcard/ui.xml

# 2. Trouver les bounds du bouton dans le XML
#    Exemple : bounds="[100,200][300,250]"

# 3. Calculer le centre
#    x = (100 + 300) / 2 = 200
#    y = (200 + 250) / 2 = 225

# 4. Taper
"$ADB" shell input tap 200 225
```

**Attention** : ne PAS deviner les coordonnees a partir d'un screenshot. Toujours utiliser `uiautomator dump` pour obtenir les bounds exacts.

### 5.5. Autres interactions

```bash
# Appuyer sur le bouton Back
"$ADB" shell input keyevent KEYCODE_BACK

# Appuyer sur Home
"$ADB" shell input keyevent KEYCODE_HOME

# Saisir du texte
"$ADB" shell input text "Canis lupus"

# Swipe (scroll vers le bas)
"$ADB" shell input swipe 500 1500 500 500 300
# Arguments : startX startY endX endY duration_ms
```

---

## 6. Workflow de test complet

Voici le workflow typique pour tester une modification :

```bash
# 0. Definir les chemins (obligatoire)
ADB="$HOME/Android/Sdk/platform-tools/adb"
EMULATOR="$HOME/Android/Sdk/emulator/emulator"

# 1. Compiler l'APK
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run flet build apk --no-rich-output

# 2. Demarrer l'emulateur (si pas deja lance)
"$EMULATOR" -avd daynimal_test -no-audio &
"$ADB" wait-for-device

# 3. Installer l'APK
"$ADB" install -r build/apk/app-x86_64-release.apk

# 4. Lancer l'app
"$ADB" shell monkey -p com.daynimal.daynimal -c android.intent.category.LAUNCHER 1

# 5. Attendre le chargement (3-5 secondes)
sleep 5

# 6. Prendre un screenshot
"$ADB" exec-out screencap -p > tmp/screenshot.png

# 7. Verifier les logs
"$ADB" logcat -d | grep -i "flutter\|python\|error" | grep -v "audit\|InetDiag"
```

### Test du premier lancement (onboarding)

Pour tester l'ecran de premier lancement (telechargement de la DB) :

```bash
# 1. Desinstaller l'app completement
"$ADB" uninstall com.daynimal.daynimal

# 2. Reinstaller et lancer
"$ADB" install -r build/apk/app-x86_64-release.apk
"$ADB" shell monkey -p com.daynimal.daynimal -c android.intent.category.LAUNCHER 1

# 3. Prendre des screenshots a intervalles
sleep 3 && "$ADB" exec-out screencap -p > tmp/onboarding_1.png
sleep 10 && "$ADB" exec-out screencap -p > tmp/onboarding_2.png
sleep 30 && "$ADB" exec-out screencap -p > tmp/onboarding_3.png
```

L'onboarding suit ce flux :
1. Ecran d'accueil avec bouton "Commencer"
2. Ecran de progression ("Preparation des donnees...") avec barre reelle
3. Ecran "Tout est pret !" (2 secondes)
4. Transition automatique vers la vue Decouverte

---

## 7. Problemes connus et solutions

### BlueStacks ne fonctionne pas

BlueStacks est **incompatible** avec les apps Flet (ecran blanc). Utiliser l'emulateur Android Studio (AVD) a la place.

### Chemin Windows vs Unix dans Git Bash

Git Bash (MSYS) convertit automatiquement les chemins commencant par `/`. Pour les commandes ADB :
- Utiliser `//sdcard/` au lieu de `/sdcard/` pour les chemins Android
- Utiliser des chemins entre guillemets pour les chemins Windows avec espaces

### L'app plante au demarrage

1. Verifier les logs : `"$ADB" logcat -d | grep -i "error\|exception\|crash"`
2. Causes frequentes :
   - Import Python manquant (verifier que toutes les dependances sont dans `pyproject.toml`)
   - Chemin fichier hardcode (utiliser `get_app_data_dir()` / `get_app_temp_dir()`)
   - Widget Flet deprecated (verifier les migrations dans le roadmap)

### L'APK est trop gros

Le `split_per_abi = true` dans `pyproject.toml` genere un APK par architecture (~30 MB chacun au lieu d'un seul gros APK). La DB (117 MB) est telechargee au premier lancement, pas embarquee dans l'APK.

### Emulateur lent

- Activer HAXM ou Hyper-V dans le BIOS (virtualisation hardware)
- Utiliser une image x86_64 (pas ARM — beaucoup plus rapide en emulation)
- Allouer au moins 2 GB de RAM a l'AVD

---

## 8. Arborescence des fichiers generes

```
build/
└── apk/
    ├── app-arm64-v8a-release.apk     # Pour telephones ARM modernes
    ├── app-armeabi-v7a-release.apk    # Pour telephones ARM anciens
    └── app-x86_64-release.apk         # Pour emulateur

tmp/                                    # Git-ignored
├── screenshot.png                      # Screenshots de test
├── onboarding_1.png
└── ...
```

---

## 9. Reference rapide des commandes ADB

> Toutes les commandes supposent que `ADB` et `EMULATOR` sont definis (voir section 1.3).

| Action | Commande |
|--------|----------|
| Lister les appareils | `"$ADB" devices` |
| Installer APK | `"$ADB" install -r <apk>` |
| Desinstaller app | `"$ADB" uninstall com.daynimal.daynimal` |
| Lancer app | `"$ADB" shell monkey -p com.daynimal.daynimal -c android.intent.category.LAUNCHER 1` |
| Forcer l'arret | `"$ADB" shell am force-stop com.daynimal.daynimal` |
| Screenshot | `"$ADB" exec-out screencap -p > tmp/screenshot.png` |
| Logs filtres | `"$ADB" logcat -d \| grep -i "flutter\|python\|error"` |
| Effacer logs | `"$ADB" logcat -c` |
| Dump UI | `"$ADB" shell uiautomator dump //sdcard/ui.xml` |
| Lire dump UI | `"$ADB" shell cat //sdcard/ui.xml` |
| Tap a (x,y) | `"$ADB" shell input tap <x> <y>` |
| Bouton Back | `"$ADB" shell input keyevent KEYCODE_BACK` |
| Saisir texte | `"$ADB" shell input text "<texte>"` |
| Scroll bas | `"$ADB" shell input swipe 500 1500 500 500 300` |
| Wipe emulateur | `"$EMULATOR" -avd daynimal_test -wipe-data` |
