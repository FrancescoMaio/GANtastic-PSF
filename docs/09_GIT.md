# 9. Archivio Git e caricamento

## Contenuto della consegna

Lo ZIP contiene una cartella `GANtastic-PSF/` con file sorgenti e documentazione, più `GANtastic-PSF.bundle`. Il bundle conserva il commit iniziale e il branch `main`; la cartella è uno snapshot leggibile senza Git. Non sono inclusi remote, credenziali, dati simulati, pesi o configurazioni Git personali.

Per ottenere un vero repository con cronologia:

```bash
git clone GANtastic-PSF.bundle GANtastic-PSF-repo
cd GANtastic-PSF-repo
git status
git log --oneline
```

Il clone da bundle può chiamare `origin` il percorso locale del bundle. Dopo aver creato un repository remoto vuoto sul servizio scelto, sostituire l'URL:

```bash
git remote set-url origin <URL-DEL-TUO-REPOSITORY>
git push -u origin main
```

`<URL-DEL-TUO-REPOSITORY>` è un segnaposto da sostituire, non un comando da eseguire letteralmente. Non è stato creato o pubblicato alcun repository remoto per conto dell'utente.

## Alternativa: inizializzare lo snapshot

```bash
cd GANtastic-PSF
git init -b main
git add .
git commit -m "Import source and detailed documentation"
git remote add origin <URL-DEL-TUO-REPOSITORY>
git push -u origin main
```

Questa alternativa crea un nuovo commit invece di conservare quello del bundle. Configurare la propria identità Git se Git la richiede. Il commit nel bundle usa un'identità tecnica locale neutra di importazione, non attribuisce il codice a un autore non verificato.

## Dati grandi e riproducibilità

Il `.gitignore` esclude dati FITS, modelli HDF5/Keras, NumPy, checkpoint e risultati. Non basta aggiungere `.gitignore` dopo aver già committato dati: i file già tracciati restano nella storia. Per questa consegna la storia nasce senza tali dati.

Conservare gli esperimenti in uno storage adeguato e registrare nel progetto identificatori, hash, configurazioni e ambiente. Se in futuro si decide di versionare pesi o dataset tramite un sistema per file grandi, configurarlo esplicitamente: qui non è stato inizializzato Git LFS né caricato alcun file esterno.

## Prima della pubblicazione

Adattare il percorso assoluto `main.root_dir` in una revisione personale o sostituirlo con un esempio portabile. Il template originale è conservato come richiesto dall'impostazione di questa consegna e contiene il percorso locale fornito. Scegliere una licenza, aggiungere autori e citazioni reali, e registrare le versioni con cui è stato verificato il progetto. Non includere credenziali o calibrazioni senza i relativi diritti di distribuzione.

## Flusso di sviluppo suggerito

Per correzioni operative creare un branch separato, descrivere il comportamento prima/dopo e aggiungere test mirati: cleanup non distruttivo, isolamento run, accoppiamento FITS, ripresa e limite epoche. Per modifiche scientifiche conservare un esperimento di confronto con dataset e seed definiti. Non aggiornare gli hash di provenienza per nascondere una modifica: il manifest descrive gli allegati originali.
