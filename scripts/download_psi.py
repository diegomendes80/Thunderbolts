import csv
import json
import sys
import time
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent.parent
DADOS = BASE / "dados"
DATA = BASE / "data"
META = DADOS / "metadata"

URL_META = "https://psi.nasa.gov/geode-py/ws/repo/investigations/{estudo}"
URL_TREE = "https://psi.nasa.gov/geode-py/ws/files/v2"
URL_DOWNLOAD = "https://psi.nasa.gov/geode-py/ws/studies/{estudo}/download"

EXT = {".csv", ".xlsx", ".xls", ".txt"}
MAX_ERROS_SEGUIDOS = 3
MAX_ARQUIVOS = 40
HEADERS = {"Referer": "https://psi.nasa.gov/", "Origin": "https://psi.nasa.gov"}


def obter_cadastro(estudo):
    META.mkdir(parents=True, exist_ok=True)
    cache = META / f"{estudo}.json"
    if cache.exists() and cache.stat().st_size > 0:
        return json.loads(cache.read_text(encoding="utf-8"))
    r = requests.get(URL_META.format(estudo=estudo), headers=HEADERS, timeout=(10, 60))
    r.raise_for_status()
    dados = r.json()
    cache.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    return dados


def obter_arvore(estudo, versao_estudo):
    payload = {
        "folder": f"{estudo}/",
        "fileType": "study",
        "studyId": estudo,
        "version": versao_estudo,
        "obfuscationcode": "",
    }
    r = requests.post(URL_TREE, json=payload, headers=HEADERS, timeout=(10, 60))
    r.raise_for_status()
    return r.json()


def listar_arquivos(no, estudo, saida=None):
    saida = [] if saida is None else saida
    for item in no.get("files", []):
        if item.get("id") and "bytes_size" in item and not item.get("files"):
            if item.get("restricted") or item.get("restrictedAccess"):
                continue
            rel = item["key"].split(f"psi-data/{estudo}/", 1)[-1]
            if Path(rel).suffix.lower() in EXT:
                saida.append({
                    "id": item["id"],
                    "rel": rel,
                    "versao": item.get("version", 1),
                    "bytes": item["bytes_size"],
                })
        else:
            listar_arquivos(item, estudo, saida)
    return saida


def baixar(estudo, arq, versao_estudo, destino: Path):
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists() and destino.stat().st_size == arq["bytes"]:
        return "ja_existia"

    # etapa 1: link assinado do S3 (expira, então pede um novo a cada arquivo)
    r = requests.get(
        URL_DOWNLOAD.format(estudo=estudo),
        params={"file": arq["id"], "version": arq["versao"],
                "studyVersion": versao_estudo, "redirect": "false"},
        headers=HEADERS, timeout=(10, 60),
    )
    r.raise_for_status()
    link = r.text.strip()
    if not link.startswith("https://"):
        raise ValueError(f"resposta inesperada: {link[:120]}")

    # etapa 2: baixa do S3, sem os cabeçalhos do PSI
    tmp = destino.with_suffix(destino.suffix + ".part")
    with requests.get(link, stream=True, timeout=(10, 120)) as r2:
        r2.raise_for_status()
        with open(tmp, "wb") as f:
            for pedaco in r2.iter_content(65536):
                f.write(pedaco)
    if tmp.stat().st_size != arq["bytes"]:
        tmp.unlink(missing_ok=True)
        raise ValueError("tamanho diferente do esperado")
    tmp.replace(destino)
    time.sleep(0.3)
    return "baixado"


def eh_comentario(rel):
    r = rel.lower()
    return r.endswith("_comments.txt") or "readme" in Path(r).name and r.endswith(".txt")


def processar_estudo(estudo, linhas):
    cad = obter_cadastro(estudo)
    versao_estudo = cad.get("version", 1)
    arvore = obter_arvore(estudo, versao_estudo)
    arquivos = listar_arquivos(arvore, estudo)
    print(f"{estudo}: {len(arquivos)} arquivos tabulares (studyVersion={versao_estudo})")

    # comentários e readmes em .txt não são dados
    for arq in [a for a in arquivos if eh_comentario(a["rel"])]:
        linhas.append([estudo, arq["rel"], arq["bytes"], "comentario_ignorado"])
    arquivos = [a for a in arquivos if not eh_comentario(a["rel"])]

    if len(arquivos) > MAX_ARQUIVOS:
        # prioridade: csv/xlsx/xls primeiro, depois txt; em cada grupo, os menores
        def chave(a):
            ext = Path(a["rel"]).suffix.lower()
            return (0 if ext in {".csv", ".xlsx", ".xls"} else 1, a["bytes"])
        ordenados = sorted(arquivos, key=chave)
        for arq in ordenados[MAX_ARQUIVOS:]:
            linhas.append([estudo, arq["rel"], arq["bytes"], "fora_do_limite"])
        arquivos = ordenados[:MAX_ARQUIVOS]
        print(f"  ATENCAO: limitado a {MAX_ARQUIVOS} arquivos (dados primeiro)")

    erros = 0
    for arq in arquivos:
        destino = DATA / estudo / arq["rel"]
        if erros >= MAX_ERROS_SEGUIDOS:
            status = "ignorado"
        else:
            try:
                status = baixar(estudo, arq, versao_estudo, destino)
                erros = 0
            except Exception as e:
                erros += 1
                status = f"erro: {e}"
        print(f"  [{status}] {arq['rel']}")
        linhas.append([estudo, arq["rel"], arq["bytes"], status])


def main():
    if len(sys.argv) > 1:
        estudos = sys.argv[1:]
    else:
        txt = (DADOS / "accessions.txt").read_text(encoding="utf-8")
        estudos = [l.strip() for l in txt.splitlines() if l.strip()]

    linhas = []
    for estudo in estudos:
        try:
            processar_estudo(estudo, linhas)
        except Exception as e:
            print(f"{estudo}: falhou ({e})")
            linhas.append([estudo, "", 0, f"erro: {e}"])

    saida = DADOS / "resumo_download.csv"
    with open(saida, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["estudo", "arquivo", "bytes_esperados", "status"])
        w.writerows(linhas)
    print(f"Resumo em {saida}")


if __name__ == "__main__":
    main()