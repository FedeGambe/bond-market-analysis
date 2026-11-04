"""Aggiorna i dati di docs/index.html: il JSON dentro <script id="dati">, una riga a settimana dal 2000.
Il testo e i grafici della pagina restano come sono; si leggono i dati nuovi a ogni apertura."""
import json
import re
from pathlib import Path

import pandas as pd

PAGINA = Path(__file__).resolve().parent.parent / "docs" / "index.html"


def aggiorna(df, tab):
    if not PAGINA.exists():
        return
    w = df.resample("W-FRI").last()  # ultimo dato di ogni settimana: pagina leggera
    w.index = w.index.where(w.index <= df.index[-1], df.index[-1])  # la settimana in corso porta la data vera, non il venerdì futuro
    num = lambda v, n=3: None if pd.isna(v) else round(float(v), n)
    dati = {"agg": f"{df.index[-1]:%d/%m/%Y}", "d": list(w.index.strftime("%Y-%m-%d")),
            "s": {c: [num(v) for v in w[c]] for c in w},
            "tab": [{k: (str(v) if k == "Dati al" else v if isinstance(v, str) else num(v)) for k, v in r.items()}
                    for r in tab.to_dict("records")]}
    testo = json.dumps(dati, ensure_ascii=False, separators=(",", ":"))
    html = PAGINA.read_text(encoding="utf-8")
    html, n = re.subn(r'(<script id="dati" type="application/json">).*?(</script>)', lambda m: m[1] + testo + m[2], html, flags=re.S)
    if n != 1:
        raise SystemExit(f"{PAGINA.name}: blocco dati non trovato, pagina non aggiornata")
    PAGINA.write_text(html, encoding="utf-8")
    print(f"Pagina aggiornata: {PAGINA.name} ({len(testo) // 1024} KB di dati)")
