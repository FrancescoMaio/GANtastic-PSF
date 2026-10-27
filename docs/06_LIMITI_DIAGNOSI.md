# 6. Limiti noti e troubleshooting

Questa lista deriva dalla lettura del codice, non da una campagna di test con SPECULA e GPU. I sorgenti sono stati mantenuti invariati per non cambiare implicitamente risultati o flusso di lavoro.

## Problemi prioritari

| Problema | Effetto | Azione operativa / futura correzione |
|---|---|---|
| Cleanup globale anche in dry-run | Perdita degli output standard precedenti | Copia isolata e backup; in futuro directory per run e overwrite esplicito |
| run-id non usato nei percorsi | Mancata separazione degli esperimenti | Non affidarsi al flag per conservare dati |
| Accumulo Y prima della validazione X | Mismatch o disallineamento dei campioni | Validare coppia prima di appendere |
| Adattamento seed prima del restore | Pad/trim anche con checkpoint | Verificare dimensione e semantica dei modi |
| Checkpoint prima della costruzione modelli | Possibile snapshot incompleto | Ripristino anticipato e verifica rigorosa in una futura revisione |
| MAX_GLOBAL_EPOCHS solo tra cicli | Possibile superamento soglia | Controllo anche nel loop epoche |
| Ctrl+C può lanciare simulazioni | Arresto ritardato e cleanup dei dati | Prevedere il comportamento, separare stop e refresh in futuro |
| LAST non salvato sempre alla fine | HDF5 last potenzialmente obsoleto | Usare checkpoint verificato o aggiungere salvataggio finale |
| Stato e checkpoint separati | Ripresa non atomica | Backup completo, futura scrittura transazionale |
| Nessun controllo NaN/negativi | Loss non finite | Controlli su input e target prima del training |

## Diagnosi per sintomo

**`ModuleNotFoundError: ruamel`**: il generatore necessita di `ruamel.yaml`, anche per dry-run. Installarlo nell'interprete che esegue lo script, non in un ambiente diverso.

**Eseguibile `specula` non trovato**: controllare PATH o usare `--specula-exe /percorso/assoluto/specula`. Il training automatico non passa questo flag: adattare esplicitamente `SPECULA_CMD` o l'ambiente se necessario.

**Template/calibrazioni non trovati**: verificare `--template`, `main.root_dir` e i tag della propria installazione. Il percorso dello script e la directory corrente hanno ruoli diversi nei due programmi.

**Nessuna nuova simulazione dopo un run**: controllare `data_store.store_dir`, `BASE_DIR`, cwd, sottocartelle realmente create e `used_folders`. Nomi riutilizzati possono essere considerati già consumati; non correggere alla cieca cancellando lo stato.

**Unexpected PSF/commands shape**: il codice pretende 500 frame e HDU primaria. Controllare gli assi e la serializzazione SPECULA. Modificare solo total_time non rende il loader generico.

**Inconsistent numbers of samples**: verificare ogni coppia FITS e in particolare il problema di accumulo Y prima della validazione X. Non troncare automaticamente i due array alla lunghezza minima: potrebbe nascondere un disallineamento temporale.

**NaN nelle loss**: controllare NaN/inf in X/Y, PSF negative, scale delle feature, sigma quasi zero, incompatibilità dello scaler e gradienti. Ridurre learning rate senza identificare la causa non corregge un logaritmo di un numero non positivo.

**OOM**: ridurre BATCH_SIZE in una revisione dichiarata, limitare cartelle per ciclo e misurare RAM/VRAM. La Dense a 65536 unità e le convoluzioni transposte sono costose. Non sono presenti gradient accumulation o caricamento streaming.

**Errore GPU con una sola scheda**: il codice usa indice 1. Modificare consapevolmente la selezione, poi controllare la GPU effettiva; un'eccezione catturata non garantisce la configurazione desiderata.

**Errore caricando HDF5 o checkpoint**: registrare versioni TensorFlow/Keras/h5py e confrontare architettura e dimensioni. Non è disponibile un ambiente originale congelato; conversioni e migrazioni richiedono una prova di equivalenza.

**PAUSE sembra ignorato**: il controllo è a fine epoca. Il tempo di validazione e scrittura immagini si aggiunge al tempo di training. Controllare che il file si trovi nel WORKDIR della directory corrente del processo.

**Metriche migliori ma PSF poco convincenti**: la validazione L1 può essere dominata da regioni estese a bassa intensità e cambia campioni tra cicli. Confrontare metriche spaziali, casi fuori distribuzione e colorbar comuni.

## Validazione scientifica prima dell'uso

- Confermare che la telemetria salvata sia la quantità fisica desiderata: modi ricostruiti e comandi integrati non coincidono per definizione.
- Verificare allineamento temporale con ritardo dell'integratore e semantica temporale dell'output PSF.
- Confrontare sorgente NGS a 5 arcsec e sorgente on-axis: nel template la PSF usa la prima.
- Il valore 2200 nm è quello del template. Un passaggio a banda L richiede una configurazione e una validazione dedicate, non una nuova etichetta nel README.
- Il profilo Cn2 ha somma 0.999999663, coerente con uno entro l’arrotondamento dei valori. Verificare comunque la convenzione fisica dei pesi nella propria installazione SPECULA.
- Definire split per run/condizioni e test indipendente. Non usare il best su una validazione variabile come unica evidenza di generalizzazione.
- Valutare flusso, campionamento angolare, centro PSF e normalizzazione prima dell'impiego in una pipeline fotometrica.

Nessuna accuratezza, contrasto raggiunto, Strehl o velocità di inferenza è attestata da questo archivio.
