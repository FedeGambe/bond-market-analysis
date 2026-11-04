# Bond Market Analysis

Andamento dei **bond europei e americani**: rendimenti dei titoli di Stato, inclinazione della curva, spread tra paesi e spread corporate.
Stessa impostazione di [Target Maturity ETF Planner](https://github.com/FedeGambe/Target_Maturity_ETF_Planner), ma niente scraping: i dati arrivano dalle API di BCE, FRED e CNBC.

## Cosa fa

1. **Download** (`src/main.py`): scarica le serie elencate in `src/config.toml` e aggiorna `data/rendimenti.csv` (una colonna per serie). Se una serie fallisce il csv resta quello vecchio.
2. **Foglio riepilogo** `data/riepilogo.xlsx`: per ogni serie (e per le differenze 10Y-2Y, BTP-Bund, ecc.) ultimo valore, variazioni a 1 mese, 3 mesi e 1 anno in punti base, minimo e massimo dal 2000, percentile sugli ultimi 10 anni e su tutto lo storico (calcolato sui valori di fine mese, così gli anni con dati radi pesano come quelli giornalieri).
3. **Pagina web** (`docs/index.html`, GitHub Pages): sintesi con i percentili storici, grafici interattivi (decennali, scadenze per paese, curva, 10Y-2Y, spread sulla Germania, spread delle aziende) con un commento generale per ognuno e una riga "oggi" ricalcolata dai dati, tabella di tutte le serie. `src/pagina.py` riscrive solo il blocco dati della pagina (una riga a settimana dal 2000), a ogni lancio di `main.py`.
4. **Notebook** (`notebooks/Andamento_Bond.ipynb`): gli stessi grafici per esplorare in Python.

## Serie (dal 2000)

| | Fonte | Frequenza |
|---|---|---|
| Treasury USA 3M, 2Y, 5Y, 10Y, 30Y | FRED | giornaliera |
| Curva AAA area euro 3M, 2Y, 5Y, 10Y, 30Y | BCE | giornaliera, dal 2004 |
| Decennali Germania, Italia, Francia, Spagna fino a ottobre 2011 (`BCE xx 10Y` nel csv) | BCE | media mensile |
| Titoli di Stato Germania, Italia, Francia, Spagna a 1 (non Spagna), 2, 5, 10, 30 anni | CNBC | giornaliera dal 2024, settimanale dal 2011, trimestrale prima (Spagna 2Y dal 2014) |
| Spread aziende Baa sul Treasury 10 anni (Moody's) | FRED | giornaliera |
| Spread corporate US IG, US HY, EUR HY (ICE BofA OAS) | FRED | giornaliera, solo ultimi 3 anni |

Per aggiungere una serie basta una riga in `src/config.toml` (codice FRED, chiave BCE o simbolo CNBC).

Lo storico si accumula: CNBC dà il giornaliero solo per gli ultimi 2 anni, i giorni più vecchi restano nel csv. Lanciandolo con regolarità la storia giornaliera cresce.

**Limiti**: i dati per paese vengono dall'API non ufficiale dei grafici di CNBC e possono smettere di funzionare senza preavviso; BCE e FRED sono ufficiali. Prima di novembre 2011 CNBC è solo trimestrale: per i decennali dei paesi `carica()` usa lì la media mensile BCE (il cambio di fonte può spostare gli spread di qualche centesimo); le altre scadenze restano trimestrali. I valori CNBC fuori da -5% / 25% vengono scartati (c'è almeno una barra sballata, 19/09/2014). La curva "EUR" è quella AAA (in pratica Germania e simili), non la media dell'area euro. Gli spread corporate hanno solo 3 anni di storia: il loro percentile non è su 10 anni.

## Uso

```
pip install -r requirements.txt

python src/main.py            # scarica, aggiorna csv, foglio e pagina
python src/main.py --foglio   # ricostruisce foglio e pagina dal csv
```

Poi apri `docs/index.html` nel browser o il notebook in `notebooks/`.

## Avvertenza

Strumento personale a scopo di studio: non è consulenza finanziaria.
