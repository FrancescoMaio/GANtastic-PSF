# GANtastic-PSF 2.0

**Telemetria di ottica adattiva → PSF tramite rete generativa avversaria, con simulazioni SPECULA.**

Repository documentato a partire dai tre sorgenti forniti. Documentazione in italiano, riferita alla versione inclusa il 27 ottobre 2026. I due script Python e il template YAML sono conservati byte per byte: questa consegna organizza e documenta il progetto, senza correggere implicitamente il comportamento scientifico o operativo.

## Prima di eseguire

> `generate_simulations.py` elimina interamente `data/configs`, `data/logs` e `data/sims` quando una di queste directory contiene qualcosa. Succede anche con `--dry-run`. `--run-id` non crea sottocartelle. Eseguire le prime prove in una copia dedicata, priva di dati da conservare.

Il template richiede calibrazioni SPECULA esterne e contiene un percorso assoluto da adattare. Il training richiede FITS con **esattamente 500 frame**, un crop centrale **64×64**, e viene eseguito dalla radice del repository. Il template produce PSF a **2200 nm**, con ingresso ottico dalla sorgente NGS a 5 arcsec; non è una configurazione in banda L.

## Percorso di lettura

| Documento | Contenuto |
|---|---|
| [Installazione](docs/01_INSTALLAZIONE.md) | Ambienti, dipendenze, calibrazioni, GPU e primo avvio |
| [Simulazioni](docs/02_SIMULAZIONI.md) | CLI completa, griglia, vento, YAML e output |
| [Dati e preprocessing](docs/03_DATI.md) | FITS, allineamento, split, scaling, memoria |
| [Modelli e training](docs/04_MODELLI_TRAINING.md) | Architetture, loss, cicli e iperparametri |
| [Gestione delle esecuzioni](docs/05_OPERAZIONI.md) | PAUSE, Ctrl+C, checkpoint, seed, ripresa |
| [Limiti e diagnosi](docs/06_LIMITI_DIAGNOSI.md) | Problemi osservabili nel codice e controlli scientifici |
| [Riferimento codice](docs/07_RIFERIMENTO.md) | Tutte le funzioni, firme, righe e sorgente consultabile |
| [Riferimento YAML](docs/08_YAML.md) | Tutti i parametri del template e collegamenti |
| [Git e pubblicazione](docs/09_GIT.md) | ZIP, bundle, clone e push verso un remote |
| [Verifica](docs/10_VERIFICA.md) | Controlli eseguiti e prove ancora necessarie |

## Avvio essenziale

Da una copia nuova del progetto, con Python e SPECULA correttamente configurati:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
# Configurare main.root_dir in template.yml e rendere disponibile specula.
python generate_simulations.py --n 2 --seed 42 --dry-run
# Il comando seguente sostituisce gli output generati sopra.
python generate_simulations.py --n 10 --seed 42
python GANtastic-PSF2.0.py
```

Questi sono comandi operativi da eseguire nel proprio ambiente scientifico, non la dichiarazione di una validazione end-to-end. SPECULA, calibrazioni, FITS e modelli addestrati non sono inclusi. Le dipendenze non sono congelate perché gli allegati non forniscono un ambiente validato.

## Mappa del progetto

- `GANtastic-PSF2.0.py`: training, caricamento FITS, normalizzazione, modelli, salvataggi, orchestrazione.
- `generate_simulations.py`: generazione configurazioni e lancio sequenziale di SPECULA.
- `template.yml`: catena AO e DataStore.
- `requirements.txt`: dipendenze Python rilevate dagli import.
- `requirements-generation.txt`: dipendenze del solo generatore.
- `tools/verify_repository.py`: verifica offline di sintassi, integrità originali e link locali.
- `SOURCE_MANIFEST.json`: hash SHA-256 dei tre allegati.
- `docs/`: manuale tecnico e operativo.

Le cartelle `data/`, `controllo/`, `seed/` e gli ambienti locali sono esclusi dal versionamento. Non viene assegnata una licenza ai sorgenti: il titolare deve scegliere la licenza prima di una distribuzione con diritti di riuso espliciti; vedere [LICENSE-NOTICE.md](LICENSE-NOTICE.md).
