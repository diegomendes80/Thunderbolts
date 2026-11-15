import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DADOS = BASE / "data"
FRONT_DATA = BASE / "views" / "thunderbolts" / "public" / "data"
ENTRADA = DADOS / "busca.json"
SAIDA = DADOS / "catalogo_base.json"
IDS = DADOS / "accessions.txt"
HOST = "https://psi.nasa.gov"

# grafias diferentes da mesma subarea
SUBAREA = {
    "flames of gaseous fuel": "Flames of gaseous fuels",
    "flames of gaseous fuels": "Flames of gaseous fuels",
    "droplet": "Droplets",
    "droplets": "Droplets",
}


def lista(texto, sep=3):
    """O PSI separa itens com varios espacos seguidos."""
    return [t.strip() for t in re.split(rf"\s{{{sep},}}", texto or "") if t.strip()]


def data_iso(ts):
    if not ts:
        return ""
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")


def limpar(src):
    sub = (src.get("SubResearch Area") or "").strip()
    thumb = src.get("Thumbnail") or ""
    return {
        "id": src["Accession"],
        "titulo": (src.get("Title") or "").strip(),
        "sigla": (src.get("Acronym") or "").strip(),
        "area": (src.get("Research Area") or "").strip(),
        "subarea": SUBAREA.get(sub.lower(), sub),
        "tipo_projeto": (src.get("Project Type") or "").strip(),
        "plataforma": (src.get("Flight Platform") or "").strip(),
        "centro": (src.get("Monitoring Center") or "").strip(),
        "inicio": src.get("Investigation Start Date") or "",
        "fim": src.get("Investigation End Date") or "",
        "liberado_em": data_iso(src.get("Public Release Date")),
        "palavras_chave": lista(src.get("Keywords")),
        "relacionados": lista(src.get("Related Investigations")),
        "hardware": lista((src.get("Experiment Hardware") or {}).get("Name"), sep=2),
        "imagem": HOST + thumb if thumb else "",
        "objetivo": (src.get("Objectives") or "").strip(),
        "abordagem": (src.get("Approach") or "").strip(),
        "hipotese": (src.get("Hypothesis") or "").strip(),
        "impactos_terra": (src.get("Research Impacts/Earth Benefits") or "").strip(),
    }


def achar_hits(obj):
    """Procura o bloco {"hits": {"hits": [...]}} em qualquer nivel do JSON."""
    if isinstance(obj, dict):
        h = obj.get("hits")
        if isinstance(h, dict) and isinstance(h.get("hits"), list):
            return h
        for v in obj.values():
            r = achar_hits(v)
            if r:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = achar_hits(v)
            if r:
                return r
    return None


if not ENTRADA.exists():
    sys.exit(f"Arquivo nao encontrado: {ENTRADA}\nSalve a resposta da busca do PSI nele e rode de novo.")

texto_busca = ENTRADA.read_text(encoding="utf-8-sig").strip()
if not texto_busca:
    sys.exit(f"{ENTRADA} esta vazio. Cole a resposta da busca nele e salve (Ctrl+S).")

try:
    dados = json.loads(texto_busca)
except json.JSONDecodeError as e:
    sys.exit(f"{ENTRADA} nao e um JSON valido ({e}).\nComeco do arquivo: {texto_busca[:120]!r}")

bloco = achar_hits(dados)
if bloco is None:
    chaves = list(dados.keys())[:15] if isinstance(dados, dict) else type(dados).__name__
    sys.exit(
        "Nao achei a lista de estudos (chave 'hits') no busca.json.\n"
        f"Chaves do topo: {chaves}\n"
        "Provavel causa: a resposta copiada e de outra requisicao."
    )

hits = bloco["hits"]
total = bloco.get("total", len(hits))
total = total["value"] if isinstance(total, dict) else total

estudos = [limpar(h["_source"]) for h in hits]

DADOS.mkdir(exist_ok=True)
FRONT_DATA.mkdir(parents=True, exist_ok=True)

texto = json.dumps(estudos, ensure_ascii=False, indent=2)
SAIDA.write_text(texto, encoding="utf-8")
(FRONT_DATA / "catalogo_base.json").write_text(texto, encoding="utf-8")
IDS.write_text("\n".join(e["id"] for e in estudos) + "\n", encoding="utf-8")

print(f"{len(estudos)} estudo(s) lidos; a busca informa total = {total}")
if len(estudos) < total:
    print(f"ATENCAO: faltam {total - len(estudos)} (resposta paginada)")
nao_comb = [e["id"] for e in estudos if e["area"] != "Combustion Science"]
if nao_comb:
    print("Fora de Combustion Science:", ", ".join(nao_comb))