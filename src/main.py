"""Scarica i rendimenti dei titoli di Stato e gli spread corporate, europei e americani (BCE, FRED, grafici CNBC).
Aggiorna lo storico data/rendimenti.csv (una colonna per serie) e il riepilogo data/riepilogo.xlsx.

    python src/main.py             scarica e aggiorna csv e foglio
    python src/main.py --foglio    solo ricostruisce il foglio dal csv"""
import json
import sys
import tomllib
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "data" / "rendimenti.csv"
XLSX = ROOT / "data" / "riepilogo.xlsx"
CONFIG = tomllib.loads((Path(__file__).parent / "config.toml").read_text(encoding="utf-8"))
URL = {"fred": "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}&cosd={}",
       "bce": "https://data-api.ecb.europa.eu/service/data/{}?format=csvdata&startPeriod={}",
       "cnbc": "https://ts-api.cnbc.com/harmony/app/charts/{}.json?symbol={}"}
# differenze tra serie, in punti percentuali
DERIVATE = {"US 10Y-2Y": ("US 10Y", "US 2Y"), "EUR 10Y-2Y": ("EUR 10Y", "EUR 2Y"), "US-EUR 10Y": ("US 10Y", "EUR 10Y"),
            "IT-DE 10Y": ("IT 10Y", "DE 10Y"), "FR-DE 10Y": ("FR 10Y", "DE 10Y"), "ES-DE 10Y": ("ES 10Y", "DE 10Y"),
            "BCE IT-DE 10Y": ("BCE IT 10Y", "BCE DE 10Y"), "BCE FR-DE 10Y": ("BCE FR 10Y", "BCE DE 10Y"),
            "BCE ES-DE 10Y": ("BCE ES 10Y", "BCE DE 10Y")}


def barre(periodo, simbolo):
    """Chiusure dai grafici CNBC, indicizzate per data."""
    req = Request(URL["cnbc"].format(periodo, simbolo), headers={"User-Agent": "Mozilla/5.0"})
    b = json.load(urlopen(req, timeout=30))["barData"]["priceBars"]
    return pd.Series([float(x["close"]) for x in b], pd.to_datetime([x["tradeTime"][:8] for x in b], format="%Y%m%d"))


def unisci(*strati):
    """Strati dal più rado al più fitto: ognuno vale solo prima dell'inizio del successivo."""
    out = strati[-1]
    for s in reversed(strati[:-1]):
        out = pd.concat([s[s.index < out.index[0]], out])
    return out


def cnbc(codice):
    """Trimestrale dal 1999 (ALL), settimanale dal 2011 (10Y), giornaliero sugli ultimi 2 anni (1Y).
    Le barre sono datate all'inizio del periodo ma sono la chiusura: le sposto alla fine (trimestre, venerdì).
    CNBC mette anche una barra il sabato (sessione serale USA): la scarto, vale la chiusura del venerdì."""
    trim, sett, gior = barre("ALL", codice), barre("10Y", codice), barre("1Y", codice)
    trim.index += pd.offsets.BQuarterEnd(0)
    sett.index += pd.Timedelta(days=5)
    return unisci(trim, sett, gior[gior.index.dayofweek < 5])


def scarica(fonte, codice, inizio):
    if fonte == "cnbc":
        s = cnbc(codice)
        return s[(s.index >= inizio) & s.between(-5, 25)]  # CNBC ha qualche barra sballata (es. IT 5Y -31,9% il 19/09/2014)
    df = pd.read_csv(URL[fonte].format(codice, inizio))
    if fonte == "fred":  # observation_date, CODICE (vuoto nei festivi)
        return pd.Series(df.iloc[:, 1].values, pd.to_datetime(df.iloc[:, 0])).dropna()
    return pd.Series(df["OBS_VALUE"].values, pd.to_datetime(df["TIME_PERIOD"]))


def carica():
    """Storico dal csv, con le serie derivate."""
    df = pd.read_csv(CSV, sep=";", decimal=",", index_col=0, parse_dates=True)
    return df.assign(**{k: df[a] - df[b] for k, (a, b) in DERIVATE.items()})


def variazione(s, off):
    """Ultimo valore meno quello a 'off' prima (l'ultimo disponibile a quella data), in punti base."""
    return (s.iloc[-1] - s.asof(s.index[-1] - off)) * 100


def riepilogo():
    df = carica()
    rows = []
    for c in df:
        s = df[c].dropna()
        m = s.resample("ME").last().dropna()  # fine mese: stesso peso agli anni con dati trimestrali e a quelli giornalieri
        m10 = m[m.index > s.index[-1] - pd.DateOffset(years=10)]
        rows.append({"Serie": c, "Dati al": s.index[-1].date(), "Ultimo %": s.iloc[-1],
                     **{f"Var {k} (pb)": variazione(s, pd.DateOffset(**v)) for k, v in
                        (("1m", {"months": 1}), ("3m", {"months": 3}), ("1a", {"years": 1}))},
                     "Dal": s.index[0].year, "Min": s.min(), "Max": s.max(),
                     # 1 = mai stato così alto, 0 = mai così basso
                     "Percentile 10a": (m10 <= s.iloc[-1]).mean(), "Percentile storico": (m <= s.iloc[-1]).mean()})
    out = pd.DataFrame(rows).round(3)
    try:
        path = XLSX
        out.to_excel(path, index=False, sheet_name="Riepilogo")
    except PermissionError:  # aperto in Excel
        path = XLSX.with_name(f"riepilogo_{datetime.now():%Y-%m-%d_%H%M}.xlsx")
        out.to_excel(path, index=False, sheet_name="Riepilogo")
    print(out.to_string(index=False))
    print(f"\nFoglio aggiornato: {path.name}")


def main():
    serie, errori = {}, []
    for fonte in ("fred", "bce", "cnbc"):
        for nome, codice in CONFIG[fonte].items():
            try:
                serie[nome] = scarica(fonte, codice, CONFIG["inizio"])
            except Exception as e:
                errori.append(f"{nome} ({codice}): {e}")
    if errori:  # meglio tenere il vecchio csv che uno con colonne mancanti
        sys.exit("ERRORE, csv non aggiornato:\n" + "\n".join(errori))
    df = pd.concat(serie, axis=1).sort_index()
    if CSV.exists():  # CNBC dà il giornaliero solo per 2 anni: i giorni più vecchi restano dallo storico
        vecchio = pd.read_csv(CSV, sep=";", decimal=",", index_col=0, parse_dates=True)
        df = df.combine_first(vecchio[vecchio.columns.intersection(df.columns)])
    df.to_csv(CSV, sep=";", decimal=",", index_label="Data")
    print(f"{datetime.now():%Y-%m-%d %H:%M} - {len(serie)} serie, {len(df)} date fino al {df.index[-1]:%d/%m/%Y}")


def selfcheck():
    s = pd.Series([1.0, 1.5, 2.0], pd.to_datetime(["2026-01-01", "2026-02-01", "2026-03-01"]))
    assert variazione(s, pd.DateOffset(months=1)) == 50
    assert variazione(s, pd.DateOffset(months=2)) == 100
    assert pd.isna(variazione(s, pd.DateOffset(years=1)))  # prima dell'inizio: niente variazione
    trim = pd.Series([0.5, 0.7], pd.to_datetime(["2026-07-31", "2026-09-30"]))
    sett = pd.Series([1.0, 2.0], pd.to_datetime(["2026-10-09", "2026-10-16"]))
    gior = pd.Series([3.0, 4.0], pd.to_datetime(["2026-10-15", "2026-10-16"]))
    u = unisci(trim, sett, gior)
    assert list(u.index.strftime("%d/%m")) == ["31/07", "30/09", "09/10", "15/10", "16/10"] and list(u) == [0.5, 0.7, 1.0, 3.0, 4.0]
    assert pd.Timestamp("1999-01-01") + pd.offsets.BQuarterEnd(0) == pd.Timestamp("1999-03-31")


if __name__ == "__main__":
    selfcheck()
    if "--foglio" not in sys.argv:
        main()
    riepilogo()
