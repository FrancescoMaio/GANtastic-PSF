# 10. Verifiche della consegna

## Verifiche eseguite

- Confronto SHA-256 dei tre file in radice con gli allegati: identici.
- Parsing AST di tutti gli script Python: sintassi valida, senza importare TensorFlow o avviare simulazioni.
- Lettura del template YAML e controllo del numero di strati: 35 altezze, 35 pesi Cn2, 35 velocità e 35 direzioni nel template.
- Verifica della griglia predefinita: 160 combinazioni.
- Verifica statica della schedule alpha, della formula di normalizzazione Y e del crop centrale attraverso esecuzione isolata delle funzioni su piccoli array sintetici.
- Verifica dei link locali Markdown e presenza dei file referenziati.
- Verifica del bundle Git e clonazione locale in una directory di prova.
- Controllo CRC dello ZIP e confronto dei sorgenti estratti con il manifest.

Il comando ripetibile `python tools/verify_repository.py` copre integrità, sintassi e link; non include le altre verifiche di confezionamento elencate sopra.

## Cosa non è stato eseguito

Non sono stati eseguiti SPECULA, un dry-run completo del generatore, training TensorFlow, restore di checkpoint reali o inferenza su FITS scientifici. Nell'ambiente di confezionamento non sono presenti TensorFlow, Astropy e ruamel.yaml; non sono stati forniti calibrazioni, FITS o seed. Non è stata tentata l'installazione di un ambiente scientifico non specificato.

La lettura YAML di controllo è stata effettuata con PyYAML disponibile nell'ambiente di confezionamento. Il programma originale usa ruamel.yaml: il controllo non certifica il round-trip del programma né la validazione delle classi SPECULA.

Le prove isolate su funzioni pure non validano il ciclo complessivo, l'accoppiamento temporale, la GPU o la compatibilità HDF5/Keras. Il repository è pronto per essere caricato e studiato; l'esecuzione scientifica deve essere collaudata nel proprio ambiente.

## Procedura di accettazione nell'ambiente scientifico

1. Verificare i tre hash prima di modificare la configurazione locale.
2. Annotare versione Python e tutte le dipendenze, release SPECULA e calibrazioni.
3. Eseguire il generatore in una copia isolata, verificando i YAML ottenuti.
4. Controllare i FITS reali: HDU primaria, 500 frame, dimensioni, unità, tempi, valori finiti e non negatività dei target.
5. Eseguire un piccolo training e controllare loss finite, file prodotti e forma del generatore.
6. Provare PAUSE e Ctrl+C su dati sacrificabili; controllare anche il cleanup.
7. Provare una ripresa e confrontare epoca, pesi, ottimizzatori, scaler e history con lo snapshot precedente.
8. Separare una valutazione scientifica indipendente dal collaudo tecnico.
