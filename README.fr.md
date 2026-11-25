# Émulateur de Fathom (dumpulator)

[![CI](https://github.com/EGKrb/fathom-emulator/actions/workflows/ci.yml/badge.svg)](https://github.com/EGKrb/fathom-emulator/actions/workflows/ci.yml)
[![Licence](https://img.shields.io/badge/licence-GPL--3.0%20%2F%20BSL--1.0%20%2F%20MIT-blue)](#licences)

*[English](README.md) · Français*

Exécuter le code d'un processus Windows **dans un émulateur**, à partir d'un minidump : la mémoire, les
modules et le thread du processus sont chargés dans [Unicorn](https://www.unicorn-engine.org/), et ce
que le code demande à Windows (les **appels système** : mémoire, fichiers, registre, événements,
sections, threads... et les **exceptions** : SEH, VEH, filtre d'exception non gérée) est implémenté en
Python. On peut appeler une fonction du processus avec les arguments de son choix, ou faire avancer le
programme, **avec ses threads**, jusqu'à sa sortie ; le vrai processus n'est jamais touché.

C'est [dumpulator](https://github.com/mrexodia/dumpulator) de Duncan Ogilvie (mrexodia, l'auteur de
x64dbg), intégré ici avec de nombreuses modifications (décrites dans le [README anglais](README.md#changes-to-dumpulator)),
plus `fathom_emu.py` : une ligne de commande qu'utilisent les commandes `emu.*` de
[Fathom](https://github.com/EGKrb/Fathom) et pybridge, et qui enregistre le code émulé au format de
trace de x64dbg.

Ce dépôt contient l'émulateur seul, tel qu'il est livré dans le dossier `emulator` de Fathom (il
fonctionne sans Fathom : un minidump et Python suffisent). Il est développé dans
[Fathom](https://github.com/EGKrb/Fathom/tree/main/emulator) et publié ici à chaque release de Fathom :
la version 1.9.0 est l'émulateur de Fathom 1.9.0.

## Ce qu'il émule

- **Une fonction** du processus, avec des entiers, des chaînes (`str:`, `wstr:`), des tampons (`buf:`)
  ou des octets en arguments ; ou **le programme entier**, de son point d'entrée à sa sortie.
- **Les threads** (création, attentes, sections critiques, verrous SRW, variables de condition,
  TLS), entrelacés comme sur un multiprocesseur avec une graine fixe ; le temps est virtuel.
- **Les DLL** chargées par le programme, la console, les exceptions, le registre et les fichiers (lus
  sur l'hôte, écrits dans l'émulateur seulement).
- **Hors du processus** : les fenêtres (dessinées : images PNG), le réseau (simulé par défaut), les
  processus enfants et les processus simultanés, COM, GDI+, OpenGL, Direct3D 9 à 12 avec leurs
  shaders (DXBC, DXIL, lancer de rayons, mesh shaders, work graphs).
- **Les traces** : le code émulé est enregistré au format de x64dbg (`.trace64` / `.trace32`), que
  la vue Time Travel de Fathom et TraceExport lisent.

Le détail de tout cela, et ses limites, est dans le [README anglais](README.md).

## Installation

Python 3.9 ou plus récent (64 bits pour un processus 64 bits, 32 bits pour un processus 32 bits),
sous Windows :

```
git clone https://github.com/EGKrb/fathom-emulator
cd fathom-emulator
python -m pip install -r requirements.txt
```

Avec Python 32 bits, ajouter `--prefer-binary` (le dernier capstone 5 n'a pas de wheel 32 bits et serait
compilé depuis ses sources).

ou le zip d'une [release](https://github.com/EGKrb/fathom-emulator/releases), qui contient aussi les
programmes `emulator_host` compilés (`hosts\`, pour les processus enfants de l'autre architecture ;
`hosts\build.ps1` les compile avec MSVC).

## Démarrage rapide

```
python tools\dump_process.py 1234 app.dmp                  # un minidump complet du processus 1234
python fathom_emu.py info app.dmp                          # ses threads et ses modules
python fathom_emu.py call app.dmp kernel32!lstrlenA str:hello
python fathom_emu.py call app.dmp ntdll!RtlComputeCrc32 0 str:hello 5 --trace crc.trace64
python fathom_emu.py run  app.dmp --count 100000 --syscalls
python fathom_emu.py script app.dmp examples\crc_strings.py ntdll!RtlComputeCrc32
```

`--result FICHIER` écrit le résultat en JSON (valeur de retour, adresse finale, tampons, trace, code de
sortie). Le dump doit contenir toute la mémoire du processus : `tools\dump_process.py`, la commande
`minidump` de Fathom, « Créer un fichier de vidage » du Gestionnaire des tâches, `procdump -ma`.

Depuis Python, l'API de dumpulator :

```python
from dumpulator import Dumpulator

dp = Dumpulator("app.dmp", quiet=True)
text = dp.allocate(16)
dp.write(text, b"hello\0")
print(dp.call(dp.modules["kernel32.dll"].find_export("lstrlenA").address, [text]))  # 5
```

À lancer depuis ce dossier, ou en l'ajoutant à `sys.path` : les paquets `dumpulator` et `minidump` sont
ceux de ce dépôt (ils diffèrent de ceux de PyPI).

## Dans Fathom

Le plugin ExtraCmds enregistre le débogué dans un minidump quand il le faut et exécute l'émulateur
dessus (voir la section « Emulator » du [README de Fathom](https://github.com/EGKrb/Fathom#emulator-running-the-debuggees-code-without-running-it)) :

```
emu.call ntdll.RtlComputeCrc32, 0, str:hello, 5     // $result = 0x3610A686
emu.trace on                                        // les émulations suivantes s'ouvrent dans Time Travel
emu.run 0, .10000                                   // le thread courant, 10 000 instructions plus loin
emu.script "C:\scripts\decrypt.py", 0x140001000     // l'API de dumpulator depuis Python
```

Depuis [pybridge](https://github.com/EGKrb/pybridge) : `dbg.emulate_call(...)`, `dbg.emulate_run(...)`
et `dbg.emulator()`. Une autre copie de l'émulateur est utilisée quand `FATHOM_EMULATOR` désigne son
dossier.

## Tests

```
python tests\test_call.py      # le dump d'un processus en cours : lstrlenA, RtlComputeCrc32, examples\crc_strings.py
python tests\test_avx.py       # les instructions AVX / AVX2 / FMA / BMI de avx.py comparées au processeur
```

GitHub Actions les exécute avec Python 64 bits et 32 bits à chaque push. Les tests de programmes
entiers (threads, fenêtres, processus enfants, réseau, Direct3D...) demandent les programmes de test
de Fathom et s'exécutent là-bas :
[`extracmds/tests/test_emulator.py`](https://github.com/EGKrb/Fathom/blob/main/extracmds/tests/test_emulator.py).

## Licences

dumpulator : Boost Software License 1.0 ([`LICENSE.dumpulator`](LICENSE.dumpulator)), Copyright
Duncan Ogilvie. minidump : MIT ([`LICENSE.minidump`](LICENSE.minidump)), Copyright Tamas Jos
(skelsec). Les modifications de dumpulator et `avx.py` : Boost Software License 1.0 aussi, pour
qu'elles puissent revenir à dumpulator. `fathom_emu.py`, les tests, les outils et `emulator_host` :
GPL-3.0-or-later ([`LICENSE`](LICENSE)), comme Fathom. `dumpulator/tessellator.py` : MIT, un portage du
tessellateur de référence de Microsoft (notice dans le fichier).
