# Contribuire

Separare modifiche documentali, correzioni operative e cambiamenti scientifici. Descrivere sempre quali risultati o procedure possono cambiare. Conservare le calibrazioni e i dati fuori dal repository, allegando identificatori e hash quando necessari alla riproducibilità.

Eseguire `python tools/verify_repository.py`. Il controllo degli originali è pensato per questa consegna: se si modifica consapevolmente un sorgente, documentare il cambiamento e adattare la strategia di verifica della nuova revisione senza riscrivere retroattivamente la provenienza.

Le priorità tecniche sono in `docs/06_LIMITI_DIAGNOSI.md`. Prima di dichiarare risolto un problema di training verificare il comportamento con FITS rappresentativi e ambiente TensorFlow/SPECULA registrato. Non sono presenti test end-to-end già certificati.
