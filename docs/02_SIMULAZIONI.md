# 2. Generazione delle simulazioni

## CLI completa

| Opzione | Default | Comportamento effettivo |
|---|---|---|
| `--n` | 10 | Numero di combinazioni estratte senza ripetizione |
| `--seed` | None | Seed per `random.Random` e `numpy.random.default_rng` |
| `--run-id` | automatico | Etichetta usata nel messaggio; non suddivide gli output |
| `--template` | template.yml | Percorso risolto rispetto alla directory dello script; ammesso anche assoluto |
| `--specula-exe` | specula | Un singolo eseguibile, non una stringa shell con argomenti |
| `--dry-run` | false | Genera i YAML e termina, ma applica prima il cleanup |
| `--help` | — | Mostra opzioni e termina tramite argparse |

Un'etichetta automatica con seed è `run_seed42_n10`; senza seed è `run_XXXXXXXX_n10`. Nessuna delle due viene aggiunta al percorso delle directory. Il docstring iniziale che mostra `configs/<run_id>/` non descrive l'implementazione attuale.

## Griglia dei parametri

| Quantità | Valori |
|---|---|
| Angolo zenitale [deg] | 40, 50, 70, 80 |
| Seeing [arcsec, come commentato nel template] | 0.2, 0.4, 0.8, 1.0 |
| Magnitudine delle due sorgenti | 4, 5, 6, 7, 8 |
| Outer scale L0 [m] | 25, 30 |
| Modi del DM | 702 |

Il prodotto cartesiano contiene 4×4×5×2×1 = **160 combinazioni**. `random.sample` ne sceglie `n` senza ripetizione all'interno di una chiamata. Il codice rifiuta esplicitamente `n>160`; un valore negativo fallisce nel campionamento, mentre `n=0` produce zero configurazioni e può comunque aver cancellato output preesistenti. Non c'è un controllo preventivo di tutti gli argomenti prima del cleanup.

La magnitudine di `source_on_axis` e `source_ngs` è sempre la stessa nel YAML generato. Non viene randomizzata la posizione delle sorgenti. Il numero di modi modifica solo `dm.nmodes`: se si amplia la griglia, anche `integrator.n_modes` e le calibrazioni devono essere rivisti, perché non sono aggiornati automaticamente.

## Vento e riproducibilità

Ogni configurazione riceve 35 velocità e 35 direzioni. Per i primi 30 strati la velocità è una variabile Poisson con λ=5 più uniforme tra 0 e 1; per gli ultimi 5 viene sommata una uniforme tra 2 e 3. Il risultato viene limitato all'intervallo [5,20] e arrotondato a una cifra decimale. Il clipping introduce accumuli ai bordi: non è una distribuzione uniforme di velocità né il profilo verticale fisso del template.

Le direzioni sono scelte indipendentemente da `[0, 90, -90, 180, -180]`. I valori ±180 sono due etichette campionate separatamente pur rappresentando una direzione geometrica equivalente. Il vento non viene calcolato a partire dalle altezze degli strati.

Un seed controlla estrazione dei parametri e vento nel generatore. Non imposta esplicitamente i generatori casuali di SPECULA, rumore del detector o TensorFlow. La riproducibilità dei YAML non implica riproducibilità bit per bit dei FITS o del training. Conservare ambiente, YAML effettivi e dati per poter ricostruire un esperimento.

## File prodotti e subprocess

Un nome tipico, illustrativo, è `config_0000_za40_s0.8_mag5_L0025_n702.yml`. L'indice parte da zero. La sigla `L0` è concatenata al valore a tre cifre: il risultato può sembrare ridondante, ma corrisponde al formato reale.

Le configurazioni vengono scritte in `data/configs/`, i log in `data/logs/`, e viene creata `data/sims/`. Nel template incluso `data_store.store_dir` punta proprio a `./data/sims`; i nomi delle sottocartelle e la serializzazione effettiva dipendono da SPECULA. Il wrapper non impone un nome di cartella per ogni YAML e non salva una tabella esplicita YAML → cartella FITS.

I run vengono lanciati sequenzialmente, in ordine lessicografico dei percorsi generati. `subprocess.run` riceve una lista `[eseguibile, config]`, senza shell e senza timeout. stdout e stderr confluiscono nel log dedicato, aperto in append. Vengono registrati comando ed exit code. Un exit code non nullo viene contato e il ciclo prosegue; un eseguibile inesistente può invece sollevare un'eccezione non catturata dal wrapper.

| Esito del main | Exit code |
|---|---|
| Template non trovato | 2 |
| Dry-run completato | 0 |
| Tutti i subprocess completati con successo | 0 |
| Almeno un subprocess con return code non nullo | 1 |
| Eccezione non gestita | Terminazione Python con traceback |

## Cleanup e copie YAML

Quando almeno una delle tre directory standard è non vuota, tutte e tre vengono rimosse ricorsivamente e ricreate. Questo accade prima di leggere il template e generare le configurazioni. Un errore successivo può quindi lasciare i dati precedenti già rimossi. Non vengono cancellati output esterni a queste directory se un template personalizzato punta altrove.

`CommentedMap(template)` esegue una copia superficiale: le strutture annidate restano condivise con il template in memoria. Ogni YAML viene scritto immediatamente, quindi i file già scritti non cambiano alle iterazioni successive; l'oggetto template resta però modificato. Riutilizzarlo in altre funzioni come se fosse intatto è scorretto. Una futura correzione può adottare una copia profonda, ma questa consegna preserva il sorgente.
