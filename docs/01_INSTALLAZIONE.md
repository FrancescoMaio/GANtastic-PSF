# 1. Installazione e primo avvio

## Ambito della consegna

Il progetto è costituito da script, non da un pacchetto installabile con `pip install .`. Non esistono una CLI per il training, un servizio di inferenza o un file di configurazione unico per entrambi gli script. Il nome `GANtastic-PSF2.0.py` va usato come percorso di script; non è un normale nome di modulo Python importabile con la sintassi `import`.

Le indicazioni descrivono il codice allegato. Non è stata verificata una specifica release esterna di SPECULA o TensorFlow e non vengono inventati numeri di versione compatibili. La sintassi del generatore usa union type `int | None`: adottare Python 3.10 o superiore come base di lavoro, scegliendo poi una versione supportata dalle dipendenze effettivamente installate.

## Ambiente Python

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Su PowerShell l'attivazione è `.venv\Scripts\Activate.ps1`. I comandi di gestione segnali e sentinella nel manuale assumono una shell POSIX; per un ambiente AO con GPU è opportuno usare il sistema già validato dal proprio gruppo. `requirements.txt` è un inventario delle dipendenze, non un lockfile e non una promessa di compatibilità con ogni versione futura.

Per preparare soltanto YAML:

```bash
python -m pip install -r requirements-generation.txt
python generate_simulations.py --help
```

| Dipendenza | Utilizzo |
|---|---|
| NumPy | Generazione casuale, tensori, normalizzazione e statistiche |
| ruamel.yaml | Lettura/scrittura YAML round-trip con commenti e stile |
| TensorFlow/Keras | Modelli, autodifferenziazione, dataset, checkpoint |
| Astropy | FITS e stile grafico |
| scikit-learn | Split sequenziale e shuffle di coppie X/Y |
| tqdm | Barra di avanzamento dei batch |
| Matplotlib | Diagnostiche PSF e curve delle loss |
| h5py | Backend per i file di modello HDF5 usati dal training |

## SPECULA e calibrazioni

Il generatore invoca un eseguibile chiamato `specula`, oppure quello passato a `--specula-exe`. Non importa il pacchetto SPECULA in Python. Occorre predisporre autonomamente un'installazione coerente con il template e con i propri prodotti di calibrazione. Controllare che `command -v specula` restituisca il comando previsto; il solo successo di questa verifica non valida la simulazione.

Modificare `main.root_dir` nel template: il valore allegato è un percorso assoluto della macchina di origine. La directory deve consentire alla propria installazione di risolvere almeno i tag `pupilstop_vlt_360p`, `subapdata_vlt`, `eris_rec_test`, `DSMifuncZonal360pV1`, `modal_base_vlt`. Le dimensioni di matrici di ricostruzione, basi modali, influence functions, numero di modi e maschere devono essere coerenti. Questi asset non sono ricostruibili dai tre allegati.

## Directory di lavoro

Eseguire il training dalla radice del repository. `BASE_DIR`, `WORKDIR`, `SEED_DIR`, `SPECULA_WORKDIR` e il percorso dello script di generazione sono relativi alla directory corrente. Il generatore invece calcola `project_root` dal proprio file e lancia SPECULA da quella radice: questa asimmetria può far cercare dati e stato in posti diversi se il training parte altrove.

Non importare il training per una semplice ispezione: a livello di modulo esso importa TensorFlow, configura GPU, crea directory e registra un handler SIGINT. Per controllare la sintassi è sufficiente il verificatore offline, che usa AST e non importa i modelli.

## GPU

Il codice seleziona `gpus[1]`: la seconda GPU visibile, non la prima. Con una sola GPU la selezione solleva un'eccezione catturata dal blocco generico; non equivale a una selezione controllata della CPU. Con zero GPU il blocco non viene eseguito. Con più GPU viene tentata anche l'allocazione progressiva della memoria sulla seconda.

Prima di un run lungo verificare l'indice desiderato e, se necessario, modificare esplicitamente quel blocco in una propria revisione. Usare `CUDA_VISIBLE_DEVICES` cambia l'elenco visibile: lasciare una sola GPU visibile non risolve da solo l'indice 1 nel sorgente. Non viene fornita una stima di VRAM garantita; attivazioni, gradienti e stati Adam pesano molto più dei soli FITS.

## Sequenza di collaudo locale

1. Estrarre una copia dedicata senza risultati precedenti.
2. Eseguire `python tools/verify_repository.py`.
3. Configurare calibrazioni e ambiente, poi generare due YAML con `--dry-run`.
4. Aprire i YAML e controllare percorso calibrazioni, vento, magnitudini e modalità AO.
5. Eseguire una simulazione reale e verificare HDU, assi, frame e associazione temporale.
6. Conservare una copia dei dati prima di qualsiasi nuovo lancio del generatore.
7. Avviare una prova breve di training mediante una revisione esplicita delle costanti, senza confonderla con il sorgente originale.
8. Registrare l'ambiente riuscito con `python -m pip freeze > environment-tested.txt` e registrare anche release SPECULA, driver e calibrazioni.

La generazione automatica durante il training usa lo stesso interprete Python (`sys.executable`) e i default del generatore; non eredita automaticamente `--seed`, `--n` o `--specula-exe` da un precedente lancio manuale.
