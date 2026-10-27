# 5. Ciclo operativo, stato e ripartenza

## Avvio e scoperta dei dati

Il main carica `controllo/state.json` se esiste, crea ottimizzatori e oggetti checkpoint, poi cerca cartelle sotto `BASE_DIR`. Sono nuove le stringhe di percorso non contenute in `used_folders`. Il sistema non identifica un dataset tramite hash: spostamenti, riuso dei nomi o sostituzioni di contenuto possono confondere questo criterio.

Se non ci sono cartelle nuove salva checkpoint e stato, eventualmente salva il generatore last, quindi lancia `generate_simulations.py` senza argomenti aggiuntivi. Il default genera 10 simulazioni. Il limite di 20 cartelle per ciclo non obbliga ad averne 20. Se il subprocess fallisce o non compaiono cartelle nuove, il training esce dal loop.

I modelli vengono costruiti quando si conosce la forma dei dati. La precedenza dichiarata è checkpoint, poi coppia di seed compatibili, poi inizializzazione casuale. Gli ottimizzatori sono associati ai checkpoint già prima della costruzione dei modelli.

## Salvataggi

| Percorso sotto controllo/ | Quando / contenuto |
|---|---|
| state.json | Stato applicativo e history cumulativa |
| ckpt/ | Checkpoint TensorFlow, massimo 5 mantenuti dal manager |
| x_mu.npy, x_sigma.npy | Scaler telemetria |
| best_generator_model.h5 | Quando val_l1 migliora il best globale |
| last_generator_model.h5 | Nei rami di pausa e prima di nuove simulazioni se il generatore esiste |
| images/val_target_epoch_NNNN.fits | Target normalizzato del primo esempio di validazione |
| images/val_pred_epoch_NNNN.fits | Predizione corrispondente |
| images/val_epoch_NNNN.png | Target log10, predizione log10, residuo lineare |
| loss/loss_log.txt | Append a ogni epoca registrata |
| loss/loss_cycle_NNNN.txt | Metriche del ciclo, scritto al termine del ciclo |
| loss/loss_cycle_NNNN.png | Curve del ciclo |
| specula_run.log | stdout/stderr cumulativo del wrapper di generazione |
| PAUSE | Sentinella controllata dopo l'epoca |

Il last non viene aggiornato sistematicamente a ogni epoca né alla conclusione normale dell'ultimo ciclo: non assumere che contenga l'ultimo stato dei pesi. Il checkpoint è il riferimento per una ripresa del training. Il best è selezionato su validazioni che cambiano fra cicli.

## Stato JSON e checkpoint

Lo stato contiene `used_folders`, `global_epoch`, `cycle_index`, `best_val_l1`, `wait` e `history`. Le liste history sono `gen_loss`, `disc_loss`, `val_l1`, `alpha`, `cycle`. Gli indici ciclo partono da zero; le epoche stampate nei log e nei nomi dei file partono da uno.

Il checkpoint traccia ottimizzatori, modelli quando collegati, `global_epoch`, `best_val_l1`, `wait`. Non salva direttamente tutte le informazioni del JSON. Il restore usa `expect_partial()`: non certifica che ogni variabile attesa sia stata ripristinata. Il JSON viene scritto direttamente, senza file temporaneo o transazione comune con i checkpoint. Un arresto improvviso può lasciare JSON e checkpoint non allineati.

Per backup conservare insieme l'intera `controllo/`, i dati ancora necessari, i seed, i YAML, la revisione del codice e l'ambiente. Un singolo HDF5 del generatore non è sufficiente a riprendere discriminatore, Adam, history e contatore dei cicli.

## PAUSE

Da un'altra shell, nella radice del progetto:

```bash
touch controllo/PAUSE
```

Il file viene controllato dopo training, validazione e salvataggi dell'epoca. Non interrompe immediatamente un batch. Il programma salva last, checkpoint e stato, esegue il generatore di simulazioni, rimuove la sentinella e riprende il ciclo corrente. I dataset già caricati in RAM restano quelli del ciclo: i nuovi FITS verranno considerati successivamente.

Il wrapper di generazione può cancellare i vecchi FITS mentre i dati del ciclo corrente restano in memoria. Il return value di `run_specula_command()` nel ramo PAUSE non viene usato per impedire la ripresa: un fallimento qui può essere seguito da ulteriore training sul dataset già caricato. Il ramo senza dati, invece, controlla il risultato e termina in caso di errore.

## Ctrl+C

L'handler SIGINT imposta un flag; non solleva direttamente KeyboardInterrupt. Il flag è controllato nel loop batch e all'inizio dell'epoca. Se arriva durante un batch, l'epoca può essere registrata con un numero ridotto di batch, seguita da validazione e salvataggi; il ramo pausa può lanciare SPECULA prima dell'uscita. Se il flag è già impostato all'inizio dell'epoca, il ciclo può terminare senza quel ramo.

L'arresto non è quindi sempre immediato e il comportamento dipende dal punto in cui arriva il segnale. Durante un subprocess la gestione del segnale dipende anche dall'ambiente e dal figlio. SIGTERM e arresti forzati non hanno un handler di salvataggio dedicato.

## Seed e adattamento dimensionale

I file opzionali sono `seed/generator_seed.h5` e `seed/discriminator_seed.h5`. `try_load_seed_models` richiede entrambi e confronta la forma di input del generatore con X e quella del discriminatore con Y. Non verifica esplicitamente la forma di output del generatore o l'intera semantica della base modale.

Prima della scelta checkpoint/seed viene chiamato `adjust_X_to_seed_if_needed`: se esiste il seed del generatore, legge la sua forma e può aggiungere colonne zero o tagliare colonne finali. **Questo avviene anche in presenza di checkpoint**, diversamente da una lettura superficiale del docstring. Lo stesso numero di feature non garantisce che i modi abbiano la stessa base, normalizzazione e ordine.

Se il pad/trim rileva scaler dimensionalmente incompatibili prova a rimuoverli. Non introdurre o cambiare seed a metà di una ripresa senza verificare il contratto dei dati e dei checkpoint. Non eliminare singoli elementi di `controllo/` per forzare un reset: per un nuovo esperimento usare una copia del progetto con una nuova directory di lavoro.

## Ripresa e limiti del ciclo

Per riprendere, avviare lo stesso script dalla stessa radice con stato, checkpoint e dati coerenti. Non c'è un flag `--resume`. Il codice non salva l'indice del batch né il progresso locale completo del ciclo. Dopo un'uscita gestita le cartelle del ciclo vengono marcate usate anche se il ciclo è stato interrotto; una ripresa può passare a nuovi dati. Non è una ripartenza esatta dal batch interrotto.

Se mancano nuovi dati, il main può salvare un checkpoint prima che i modelli siano costruiti o ripristinati. Questi checkpoint iniziali possono essere incompleti rispetto a uno stato di training. Conservare backup prima delle riprese importanti e verificare i messaggi e i contenuti effettivi anziché affidarsi solo all'esistenza di un file checkpoint.
