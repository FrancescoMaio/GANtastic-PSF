# 4. Architetture, obiettivo e training

## Generatore

Input: vettore di telemetria di dimensione M. Non c'è un vettore casuale latente esplicito. In inferenza il modello è una mappa deterministica per input fissato; durante il training il dropout introduce casualità.

| Passaggio | Output senza asse batch | Note |
|---|---|---|
| Input | M | nome telemetry |
| Dense + BatchNorm + Dropout | 128 | ReLU, dropout 0.1 |
| Dense + Dropout | 50 | ReLU, dropout 0.1 |
| Dense + Dropout | 40 | ReLU, dropout 0.1 |
| Dense + Dropout | 20 | ReLU, dropout 0.1 |
| Dense | 256 | ReLU |
| Dense | 65536 | ReLU |
| Reshape | 8×8×1024 | ponte verso immagini |
| Conv2DTranspose + BatchNorm | 16×16×512 | kernel 4, stride 2, same, ReLU |
| Conv2DTranspose + BatchNorm | 32×32×256 | kernel 4, stride 2, same, ReLU |
| Conv2DTranspose + BatchNorm | 64×64×128 | kernel 4, stride 2, same, ReLU |
| Conv2D | 64×64×1 | kernel 3, same, sigmoid, nome psf |

La Dense 256→65536 e le convoluzioni ampie rendono il modello impegnativo. Non assumere che la dimensione di 64 pixel implichi un training leggero. Il modello non incorpora esplicitamente propagazione ottica, OTF, pupil geometry, conservazione dell'energia o simmetrie.

## Discriminatore

Input: immagine PSF, senza telemetria. Quattro convoluzioni kernel 4 con ReLU e BatchNorm: filtri 64/128/256/256, stride 2/2/2/1, padding same. Su immagini 64×64 si passa a 32×32, 16×16, 8×8, 8×8. La Dense finale con una unità opera sull'ultimo asse senza flatten: produce **8×8×1 logits**, non un unico scalare per immagine.

Il discriminatore giudica quindi una mappa spaziale di realismo della PSF. La condizione telemetrica entra nel generatore e nel termine di ricostruzione, ma non viene passata direttamente al discriminatore. Chiamarlo discriminatore condizionato su telemetria sarebbe inesatto per questa implementazione.

## Loss

Indichiamo con D i logits del discriminatore, G(X) la PSF generata e Y il target normalizzato. `BinaryCrossentropy(from_logits=True)` gestisce i logits senza sigmoid finale del discriminatore.

```text
L_D = BCE(1, D(Y)) + BCE(0, D(G(X)))
L_adv = BCE(1, D(G(X)))
L_rec = alpha * mean((Y-G(X))²)
      + (1-alpha) * mean((ln(Y+eps)-ln(G(X)+eps))²)
L_G = L_adv + lambda_rec * L_rec
eps = 1e-10; lambda_rec = 5.0
```

I logaritmi nella loss sono naturali. Le figure diagnostiche usano invece log10 con epsilon 1e-6. Non confrontare i numeri come se fossero la stessa trasformazione. Il termine logaritmico rende importanti differenze relative a bassa intensità; la sua scala non è automaticamente confrontabile con la MSE lineare. La loss non separa core, anelli e halo mediante maschere.

La metrica di validazione è la media dell'errore assoluto `mean(abs(Y-G(X)))`, aggregata come media dei batch completi. Non include il termine avversario o logaritmico. `best_val_l1` seleziona il generatore best su questa metrica.

## Schedule alpha

| Indice ciclo (zero-based) | alpha | Peso log-MSE |
|---|---|---|
| 0 | 0.5 | 0.5 |
| 1 | 0.4 | 0.6 |
| 2 | 0.3 | 0.7 |
| 3 | 0.4 | 0.6 |
| 4 | 0.5 | 0.5 |
| 5 | 0.6 | 0.4 |
| ≥6 | 0.7 | 0.3 |

Un indice negativo restituisce il valore del ciclo 0. Alpha è fissato per il ciclo e passato come tensore float32 al train step. Poiché cambia l'obiettivo tra cicli, una variazione della generator loss non misura da sola un miglioramento. Cambiano anche i dati e la validazione, quindi confrontare i best tra cicli richiede cautela.

## Ottimizzazione e costanti

| Costante | Valore | Implicazione |
|---|---|---|
| FOLDERS_PER_CYCLE | 20 | Usa fino a 20 cartelle non ancora registrate |
| EPOCHS_PER_CYCLE | 50 | Epoche locali per ciclo |
| START_FRAME | 50 | Esclusione del transitorio iniziale per indice |
| CROP_SIZE | 64 | Coerente con l'output fisso del generatore |
| BATCH_SIZE | 32 | Batch completi nel loop |
| LAMBDA_REC | 5.0 | Peso ricostruzione |
| PATIENCE | 20 | Reset contatore; nessuna interruzione |
| MAX_GLOBAL_EPOCHS | 5000 | Controllato all'inizio del ciclo esterno |
| SAVE_IMG_EVERY | 2 | Epoca 1 e poi epoche pari |

Entrambi gli ottimizzatori sono Adam con learning rate 2e-4 e beta_1=0.5; gli altri parametri sono i default della versione installata. Il train step è decorato con `tf.function`. Due GradientTape calcolano gradienti sulle rispettive variabili trainable, poi entrambi gli ottimizzatori aggiornano i pesi. Generatore e discriminatore usano `training=True` nel training e il generatore `training=False` in validazione.

Non sono implementati gradient clipping, mixed precision esplicita, learning-rate scheduler, early stopping, augmentation o regolarizzazione fisica. PATIENCE non ferma il programma. La soglia globale viene verificata solo tra cicli: riprese da epoche non allineate possono superare il limite di fino a 49 epoche con il default di 50.

## Interpretazione scientifica

Le diagnostiche visualizzano il primo esempio di validazione, non un campione rappresentativo dell'intera distribuzione. I pannelli target e predizione hanno colorbar indipendenti. Una somiglianza visiva non prova accuratezza fotometrica. Prima di usare il modello in analisi di contrasto, costruire una valutazione esterna con profili radiali, energia encircled, residui spaziali, metriche su core/halo e condizioni AO indipendenti. Queste valutazioni sono proposte metodologiche e non risultati già prodotti dal repository.
