import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
RAIZ = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / "data"
SAIDA = BASE / "dados" / "inventario_json.txt"


def numerico(v):
    try:
        float(str(v).replace(",", "."))
        return True
    except ValueError:
        return False


def col_numerica(vals):
    vals = [x for x in vals if x not in (None, "")]
    return bool(vals) and all(numerico(x) for x in vals)


def descrever(obj, nivel=0):
    if isinstance(obj, dict) and obj and all(isinstance(v, list) for v in obj.values()):
        n = max(len(v) for v in obj.values())
        num = [k for k, v in obj.items() if col_numerica(v)]
        return f"colunar: {n} linhas, {len(obj)} colunas, {len(num)} numericas | {list(obj)[:6]}"
    if isinstance(obj, list) and obj and isinstance(obj[0], dict):
        cols = list(obj[0])
        num = [k for k in cols if col_numerica([r.get(k) for r in obj])]
        return f"linhas: {len(obj)} linhas, {len(cols)} colunas, {len(num)} numericas | {cols[:6]}"
    if isinstance(obj, dict) and nivel < 1:
        partes = [f"[{k}] " + descrever(v, nivel + 1) for k, v in list(obj.items())[:4]]
        return "aninhado: " + " || ".join(partes)
    return type(obj).__name__


linhas = []
for arq in sorted(RAIZ.rglob("*.json")):
    if "metadata" in arq.parts:
        continue
    try:
        obj = json.loads(arq.read_text(encoding="utf-8-sig"))
        desc = descrever(obj)
    except Exception as e:
        desc = f"erro: {e}"
    linhas.append(f"{arq.relative_to(RAIZ)} ({arq.stat().st_size // 1024} KB) -> {desc}")

SAIDA.parent.mkdir(exist_ok=True)
SAIDA.write_text("\n".join(linhas), encoding="utf-8")
print("\n".join(linhas))
print(f"\n{len(linhas)} arquivo(s). Salvo em {SAIDA}")