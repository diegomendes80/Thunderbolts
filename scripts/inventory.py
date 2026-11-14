import json
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
OUT = BASE / "perfis"
OUT.mkdir(exist_ok=True)


def perfil_df(df):
    return {
        "linhas": int(df.shape[0]),
        "colunas": int(df.shape[1]),
        "cabecalhos": [str(c) for c in df.columns],
        "pct_nulos": {str(c): round(float(df[c].isna().mean()), 2) for c in df.columns},
        "amostra": df.head(12).fillna("").astype(str).values.tolist(),
    }


def ler(arq):
    ext = arq.suffix.lower()
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(arq, sheet_name=None, header=None, dtype=str)
    if ext in (".csv", ".txt"):
        return {"csv": pd.read_csv(arq, header=None, dtype=str, sep=None, engine="python")}
    return None


for estudo in sorted(p for p in DATA.iterdir() if p.is_dir()):
    resultado = {"estudo": estudo.name, "arquivos": []}
    for arq in sorted(estudo.rglob("*")):
        if not arq.is_file() or arq.name.startswith("~$"):
            continue
        item = {
            "arquivo": arq.name,
            "caminho": str(arq.relative_to(DATA)),
            "extensao": arq.suffix.lower(),
        }
        try:
            abas = ler(arq)
            if abas is None:
                item["obs"] = "nao tabular (video/imagem/binario)"
            else:
                item["abas"] = {nome: perfil_df(df) for nome, df in abas.items()}
        except Exception as e:
            item["erro"] = str(e)
        resultado["arquivos"].append(item)
    (OUT / f"{estudo.name}.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("ok:", estudo.name, "-", len(resultado["arquivos"]), "arquivo(s)")