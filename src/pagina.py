"""Scrive docs/dati.js (window.DATI, caricato da docs/index.html con <script src>: funziona anche aprendo la pagina da disco): un valore per giorno lavorativo dal 2000 e la tabella di riepilogo.
Settimana, mese e anno li calcola la pagina (ultimo valore del periodo)."""
import json
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent.parent / "docs" / "dati.js"


def feriali(df):
    """Sabato e domenica spostati sul venerdì prima (vince l'ultimo valore): tolgono le righe del weekend
    dei tassi Fed/BCE senza perdere i dati mensili BCE datati il primo del mese."""
    venerdi = df.index - pd.to_timedelta((df.index.dayofweek - 4).to_numpy().clip(min=0), unit="D")
    return df.groupby(venerdi).last().dropna(how="all")


def aggiorna(df, tab):
    w = feriali(df)
    num = lambda v, n=3: None if pd.isna(v) else round(float(v), n)
    dati = {"agg": f"{df.index[-1]:%d/%m/%Y}", "d": list(w.index.strftime("%Y-%m-%d")),
            "s": {c: [num(v) for v in w[c]] for c in w},
            "tab": [{k: (str(v) if k == "Dati al" else v if isinstance(v, str) else num(v)) for k, v in r.items()}
                    for r in tab.to_dict("records")]}
    j = lambda x: json.dumps(x, ensure_ascii=False, separators=(",", ":"))
    # una serie per riga: diff piccoli nei commit giornalieri
    righe = [f'"agg":{j(dati["agg"])}', f'"d":{j(dati["d"])}',
             '"s":{\n' + ",\n".join(f"  {j(k)}:{j(v)}" for k, v in dati["s"].items()) + "\n}",
             '"tab":[\n' + ",\n".join("  " + j(r) for r in dati["tab"]) + "\n]"]
    OUT.write_text("window.DATI = {" + ",\n".join(righe) + "};\n", encoding="utf-8")
    print(f"Dati pagina aggiornati: {OUT.name} ({OUT.stat().st_size // 1024} KB)")
