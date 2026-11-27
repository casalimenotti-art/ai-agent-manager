# Analisi della dashboard Guardian

1. In `app.py`, il feed generale si apre dentro una sezione chiusa: per vedere gli eventi occorre un clic.
2. La griglia di riepilogo precede la diretta: l’ultimo evento non è il primo contenuto visibile nello spazio Agenti.
3. La diretta si aggiorna ogni otto secondi: una sequenza di azioni può arrivare tutta insieme nel pannello.
4. `theme.py` segnala gli eventi nuovi con un bordo: il cambiamento si distingue poco in un elenco denso.
5. Il feed ha un proprio scroll: la cronologia può scorrere senza che il resto della pagina faccia capire dove guardare.
6. `plancia.py` raggruppa gli eventi per agente: il riepilogo è utile per lo stato, mentre la sequenza trasversale richiede il feed.
7. Le tessere di riepilogo mostrano valori già aggiornati, senza evidenziare quale numero è cambiato.
8. Alcune interazioni hanno già una transizione in `theme.py`, ma le viste condividono forme e densità simili.
9. Il reattore ha animazioni di stato; il suo ruolo è soprattutto quello di un indicatore astratto.
10. I comandi locali riconosciuti in `app.py` agiscono sull’interfaccia; manca il collegamento a gesti e direzione dello sguardo.
