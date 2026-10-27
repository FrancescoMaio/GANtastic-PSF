# 3. Contratto dei dati e preprocessing

## Organizzazione attesa

Ogni elemento sotto `data/sims/` candidato al caricamento deve contenere `psf.fits` e `commands.fits`. `list_specula_folders` usa `glob('*')` e ordina il risultato: non filtra esplicitamente le sole directory. I file non pertinenti vengono quindi considerati candidati e poi saltati per mancanza della coppia FITS.

| Oggetto | Forma attesa | Contenuto letto |
|---|---|---|
| `psf.fits` | (500, H, W) | `hdul[0].data` |
| `commands.fits` | (500, M) | `hdul[0].data` |
| X dopo selezione | (N, M) | float32, telemetria |
| Y dopo crop | (N, 64, 64, 1) | float32, PSF |

Il DataStore etichetta `commands` l'output `modalrec.out_modes`. Questo nome non prova che si tratti dei comandi effettivi applicati al DM: il DM riceve `integrator.out_comm`. Tale distinzione va mantenuta nell'interpretazione scientifica. Unità e convenzioni della base modale non sono specificate dai FITS allegati, perché non sono stati forniti FITS.

Il codice non legge timestamp o header per sincronizzare X e Y: accoppia gli indici. Verificare che il salvataggio di `PSF.out_psf` e dei modi sia compatibile temporalmente nella propria versione SPECULA, soprattutto con integrazione PSF da 0.05 s e ritardi del controllo.

## Selezione temporale e crop

Entrambi i file devono avere esattamente 500 campioni. Il rapporto `total_time/time_step` del template è 500, ma questo da solo non dimostra che una specifica versione di SPECULA serializzi 500 frame nell'HDU primaria. Il loader scarta gli indici 0…49 e usa 50…499: **450 esempi per cartella valida**.

Il crop usa `startx=W//2-size//2` e `starty=H//2-size//2`. Non esegue ricentraggio sul picco, interpolazione o controllo del centro fisico della PSF. H e W devono essere almeno 64; il codice non lo verifica esplicitamente. Con dimensioni insufficienti lo slicing può produrre forme inattese. Il generatore di rete produce sempre 64×64: modificare solo `CROP_SIZE` non cambia l'architettura.

## Ordine, split e batch

Le cartelle del ciclo sono concatenate nel loro ordine lessicografico e i frame restano temporalmente ordinati. `train_test_split(test_size=0.2, shuffle=False)` assegna l'ultimo 20% alla validazione. Solo dopo lo split le coppie sono mescolate con scikit-learn e `random_state=42`; il dataset TensorFlow di training applica un ulteriore shuffle con buffer 1000 senza seed esplicito.

Non esiste uno split stratificato per seeing, magnitudine o run, né un insieme di test indipendente. Con una sola cartella, train e validazione condividono la stessa simulazione; con più cartelle il confine dipende dal loro ordine. Una metrica su questo split non dimostra generalizzazione a nuove condizioni atmosferiche o nuove calibrazioni.

`steps_per_epoch` e `validation_steps` sono divisioni intere della lunghezza per 32. Il dataset costruisce anche l'eventuale batch parziale, ma `.take(steps)` lo esclude. Per 450 esempi si ottengono 360 train e 90 validation: vengono usati 11 batch train (352 esempi) e 2 validation (64 esempi) per epoca. La composizione del residuo di training può cambiare con lo shuffle. Se uno dei due numeri di step è zero il ciclo viene saltato e le cartelle sono marcate usate.

## Scaling X

La prima volta vengono calcolati sul training `mu=mean(X_train,axis=0)` e `sigma=std(X_train,axis=0)+1e-12`, conservando la dimensione iniziale 1. Si salva in `controllo/x_mu.npy` e `controllo/x_sigma.npy`, poi si usa `(X-mu)/sigma` su training e validazione.

Nei cicli successivi gli scaler esistenti vengono riusati. Non vengono adattati automaticamente a ogni nuova distribuzione atmosferica. Il controllo ordinario di compatibilità considera la dimensione di mu; non valida sistematicamente tutte le proprietà di sigma. Il percorso di adattamento ai seed effettua ulteriori controlli. Una feature costante ha sigma circa 1e-12: valori successivi diversi possono produrre valori normalizzati molto grandi.

## Scaling Y e significato fisico

Ogni frame viene diviso per il proprio massimo più 1e-12. I fattori di picco sono restituiti dalla funzione ma scartati dal flusso di training. L'output è quindi una PSF normalizzata al picco, non una predizione calibrata in flusso assoluto. Non esiste un vincolo esplicito di somma unitaria; la sigmoid vincola l'intervallo del generatore, non la conservazione del flusso.

Per inferenza occorre applicare gli stessi scaler X, la stessa selezione e ordinamento dei modi, eventuale pad/trim e le stesse convenzioni fisiche. Non si può invertire la normalizzazione Y per recuperare il flusso assoluto senza un fattore esterno. Il progetto non include uno script di inferenza: queste sono condizioni operative, non un'interfaccia già implementata.

## Integrità e memoria

Il loader aggiunge le PSF alla lista prima di validare `commands.fits`. Se una cartella ha PSF valide ma comandi di forma errata, lascia PSF già accumulate: può creare lunghezze X/Y diverse e rendere errato l'allineamento. Verificare tutte le coppie prima di un training; la correzione futura dovrebbe accumulare X/Y solo dopo la validazione congiunta.

Non ci sono controlli espliciti su NaN, infiniti, negatività delle PSF, unità, forma comune tra cartelle o uguaglianza dei timestamp. Una PSF negativa può rendere non definita la loss logaritmica. File illeggibili possono interrompere l'intero caricamento.

Con 20 cartelle valide si hanno 9000 esempi: il solo Y float32 occupa 147456000 byte (circa 140.6 MiB); X con 702 modi circa 24.1 MiB. Liste intermedie, copie dello split, tensori e modelli aumentano il consumo. I dati sono caricati in memoria, non letti in streaming da FITS.
