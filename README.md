# Bond Market Analysis

Andamento dei **bond europei e americani**: rendimenti dei titoli di Stato, inclinazione della curva, spread tra paesi e spread corporate.
Stessa impostazione di [Target Maturity ETF Planner](https://github.com/FedeGambe/Target_Maturity_ETF_Planner), ma niente scraping: i dati arrivano dalle API di BCE, FRED e CNBC.

## Cosa fa

1. **Download** (`src/main.py`): scarica le serie elencate in `src/config.toml` e aggiorna `data/rendimenti.csv` (una colonna per serie). Se una serie fallisce il csv resta quello vecchio.
2. **Foglio riepilogo** `data/riepilogo.xlsx`: per ogni serie (e per le differenze 10Y-2Y, BTP-Bund, ecc.) ultimo valore, variazioni a 1 mese, 3 mesi e 1 anno in punti base, minimo, massimo e percentile degli ultimi 10 anni.
3. **Notebook** (`notebooks/Andamento_Bond.ipynb`): grafici dei decennali, breve (2 anni) contro lungo (30 anni) per paese, curva oggi vs 1 e 3 anni fa, 10Y-2Y, spread verso il Bund, spread corporate.

## Serie

| | Fonte | Frequenza |
|---|---|---|
| Treasury USA 3M, 2Y, 5Y, 10Y, 30Y | FRED | giornaliera |
| Curva AAA area euro 3M, 2Y, 5Y, 10Y, 30Y | BCE | giornaliera |
| Titoli di Stato Germania, Italia, Francia, Spagna a 1 (non Spagna), 2, 5, 10, 30 anni | CNBC | giornaliera dal 2024, settimanale fino al 2016 |
| Spread corporate US IG, US HY, EUR HY (ICE BofA OAS) | FRED | giornaliera, solo ultimi 3 anni |

Per aggiungere una serie basta una riga in `src/config.toml` (codice FRED, chiave BCE o simbolo CNBC).

Lo storico si accumula: CNBC dà il giornaliero solo per gli ultimi 2 anni, i giorni più vecchi restano nel csv. Lanciandolo con regolarità la storia giornaliera cresce.

**Limiti**: i dati per paese vengono dall'API non ufficiale dei grafici di CNBC e possono smettere di funzionare senza preavviso; BCE e FRED sono ufficiali. La curva "EUR" è quella AAA (in pratica Germania e simili), non la media dell'area euro. Gli spread corporate hanno solo 3 anni di storia: il loro percentile non è su 10 anni.

## Uso

```
pip install -r requirements.txt

python src/main.py            # scarica, aggiorna csv e foglio
python src/main.py --foglio   # ricostruisce solo il foglio dal csv
```

Poi apri il notebook in `notebooks/`.

## Avvertenza

Strumento personale a scopo di studio: non è consulenza finanziaria.
