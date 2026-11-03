"""Scarica i rendimenti dei titoli di Stato e gli spread corporate, europei e americani, dalle API pubbliche di BCE e FRED.
Riscrive lo storico data/rendimenti.csv (una colonna per serie) e il riepilogo data/riepilogo.xlsx.

    python src/main.py             scarica e aggiorna csv e foglio
    python src/main.py --foglio    solo ricostruisce il foglio dal csv"""
import sys
import tomllib
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "data" / "rendimenti.csv"
XLSX = ROOT / "data" / "riepilogo.xlsx"
CONFIG = tomllib.loads((Path(__file__).parent / "config.toml").read_text(encoding="utf-8"))
URL = {"fred": "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}&cosd={}",
       "bce": "https://data-api.ecb.europa.eu/service/data/{}?format=csvdata&startPeriod={}"}
# differenze tra serie, in punti percentuali
DERIVATE = {"US 10Y-2Y": ("US 10Y", "US 2Y"), "EUR 10Y-2Y": ("EUR 10Y", "EUR 2Y"), "US-EUR 10Y": ("US 10Y", "EUR 10Y"),
            "IT-DE 10Y": ("IT 10Y", "DE 10Y"), "FR-DE 10Y": ("FR 10Y", "DE 10Y"), "ES-DE 10Y": ("ES 10Y", "DE 10Y")}


def scarica(fonte, codice, inizio):
    df = pd.read_csv(URL[fonte].format(codice, inizio))
    if fonte == "fred":  # observation_date, CODICE (vuoto nei festivi)
        return pd.Series(df.iloc[:, 1].values, pd.to_datetime(df.iloc[:, 0])).dropna()
    return pd.Series(df["OBS_VALUE"].values, pd.to_datetime(df["TIME_PERIOD"]))  # mensili: datate al primo del mese


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
        anni10 = s[s.index > s.index[-1] - pd.DateOffset(years=10)]
        rows.append({"Serie": c, "Dati al": s.index[-1].date(), "Ultimo %": s.iloc[-1],
                     **{f"Var {k} (pb)": variazione(s, pd.DateOffset(**v)) for k, v in
                        (("1m", {"months": 1}), ("3m", {"months": 3}), ("1a", {"years": 1}))},
                     "Min 10a": anni10.min(), "Max 10a": anni10.max(),
                     "Percentile 10a": (anni10 <= s.iloc[-1]).mean()})  # 1 = massimo degli ultimi 10 anni
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
    for fonte in ("fred", "bce"):
        for nome, codice in CONFIG[fonte].items():
            try:
                serie[nome] = scarica(fonte, codice, CONFIG["inizio"])
            except Exception as e:
                errori.append(f"{nome} ({codice}): {e}")
    if errori:  # storico intero riscaricato ogni volta: meglio tenere il vecchio csv che uno con colonne mancanti
        sys.exit("ERRORE, csv non aggiornato:\n" + "\n".join(errori))
    df = pd.concat(serie, axis=1).sort_index()
    df.to_csv(CSV, sep=";", decimal=",", index_label="Data")
    print(f"{datetime.now():%Y-%m-%d %H:%M} - {len(serie)} serie, {len(df)} date fino al {df.index[-1]:%d/%m/%Y}")


def selfcheck():
    s = pd.Series([1.0, 1.5, 2.0], pd.to_datetime(["2026-01-01", "2026-02-01", "2026-03-01"]))
    assert variazione(s, pd.DateOffset(months=1)) == 50
    assert variazione(s, pd.DateOffset(months=2)) == 100
    assert pd.isna(variazione(s, pd.DateOffset(years=1)))  # prima dell'inizio: niente variazione


if __name__ == "__main__":
    selfcheck()
    if "--foglio" not in sys.argv:
        main()
    riepilogo()
