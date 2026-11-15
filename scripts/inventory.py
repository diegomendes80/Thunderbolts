import argparse
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import csv_to_json as c2j
import excel_to_json as x2j
from openpyxl import load_workbook

try:
    import xlrd
except ImportError:
    xlrd = None

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
DADOS = BASE / "dados"

MAX_MB = 20


# ---------- utilidades ----------

def tornar_unicos(header):
    vistos, saida = {}, []
    for i, h in enumerate(header):
        nome = str(h).strip() if h is not None and str(h).strip() else f"col_{i+1}"
        if nome == "columns":
            nome = "columns_"
        n = vistos.get(nome, 0)
        vistos[nome] = n + 1
        saida.append(nome if n == 0 else f"{nome}_{n+1}")
    return saida


def montar(header, linhas):
    header = tornar_unicos(header)
    data = {"columns": header}
    for h in header:
        data[h] = []
    for row in linhas:
        vals = list(row[:len(header)]) + [None] * (len(header) - len(row))
        if all(v in (None, "") for v in vals):
            continue
        for h, v in zip(header, vals):
            data[h].append(v)
    return data


def gravar(data, destino):
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, default=x2j._json_default)
    n = len(data[data["columns"][0]]) if data["columns"] else 0
    return f"{len(data['columns'])} colunas, {n} linhas"


def destino_aba(path, aba, total_abas):
    if total_abas == 1:
        return path.with_suffix(".json")
    nome = re.sub(r"[^\w\-]+", "_", aba)
    return path.with_name(f"{path.stem}__{nome}.json")


def eh_comentario(nome):
    n = nome.lower()
    return n.endswith("_comments.txt") or ("readme" in n and n.endswith(".txt"))


# ---------- texto (csv / txt) ----------

def detectar_delimitador(path, padrao=None):
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        amostra = f.read(8192)
    try:
        return csv.Sniffer().sniff(amostra, delimiters=",;\t|").delimiter
    except csv.Error:
        return padrao


def csv_tolerante(path, delim):
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
        rows = list(csv.reader(f, delimiter=delim))
    if not rows:
        raise ValueError("arquivo vazio")
    return montar(rows[0], rows[1:])


def txt_espacos(path):
    """Tabela separada por espaços: a maioria das linhas com o mesmo nº de campos (>=2)."""
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        linhas = [l.split() for l in f.read().splitlines() if l.strip()]
    if len(linhas) < 3:
        return None
    contagem = {}
    for l in linhas:
        contagem[len(l)] = contagem.get(len(l), 0) + 1
    ncols, freq = max(contagem.items(), key=lambda kv: kv[1])
    if ncols < 2 or freq / len(linhas) < 0.7:
        return None
    return montar(linhas[0], [l for l in linhas[1:] if len(l) == ncols])


def converter_texto(path, destino):
    padrao = "," if path.suffix.lower() == ".csv" else None
    delim = detectar_delimitador(path, padrao)
    if delim is not None:
        try:
            return "ok", gravar(c2j.csv_to_column_json(path, delimiter=delim), destino)
        except ValueError:
            return "ok_tolerante", gravar(csv_tolerante(path, delim), destino)
    data = txt_espacos(path)
    if data is not None:
        return "ok_espacos", gravar(data, destino)
    return "nao_tabular", ""


# ---------- excel ----------

def excel_tolerante(path, aba):
    wb = load_workbook(path, read_only=True, data_only=True)
    try:
        it = wb[aba].iter_rows(values_only=True)
        header = next((list(r) for r in it if any(c is not None for c in r)), None)
        if header is None:
            raise ValueError("aba vazia")
        while header and header[-1] is None:
            header.pop()
        return montar(header, it)
    finally:
        wb.close()


def converter_excel(path, linhas, estudo, force):
    wb = load_workbook(path, read_only=True, data_only=True)
    abas = list(wb.sheetnames)
    wb.close()
    for aba in abas:
        destino = destino_aba(path, aba, len(abas))
        rotulo = f"{path.name} [{aba}]"
        if destino.exists() and not force:
            linhas.append([estudo, rotulo, "ja_existia", ""])
            continue
        try:
            try:
                data = x2j.excel_to_column_json(path, sheet=aba)
                status = "ok"
            except ValueError as e:
                if "empty" in str(e).lower():
                    raise
                data = excel_tolerante(path, aba)
                status = "ok_tolerante"
            info = gravar(data, destino)
            linhas.append([estudo, rotulo, status, info])
            print(f"  [{status}] {rotulo}: {info}")
        except AttributeError:
            linhas.append([estudo, rotulo, "aba_de_grafico", "sem dados"])
            print(f"  [grafico] {rotulo}")
        except ValueError as e:
            linhas.append([estudo, rotulo, "aba_vazia", str(e)])
            print(f"  [vazia] {rotulo}")
        except Exception as e:
            linhas.append([estudo, rotulo, "erro", str(e)])
            print(f"  [erro] {rotulo}: {e}")


def converter_xls(path, linhas, estudo, force):
    if xlrd is None:
        linhas.append([estudo, path.name, "xls_sem_xlrd", "pip install xlrd"])
        print(f"  [xls] {path.name} (instale: pip install xlrd)")
        return
    try:
        wb = xlrd.open_workbook(path)
    except Exception:
        # .xls que na verdade é texto (tab ou espaços)
        destino = path.with_suffix(".json")
        if destino.exists() and not force:
            linhas.append([estudo, path.name, "ja_existia", ""])
            return
        try:
            status, info = converter_texto(path, destino)
        except Exception as e:
            status, info = "erro", str(e)
        linhas.append([estudo, path.name, f"{status}_xls_texto", info])
        print(f"  [{status}] {path.name} (xls em texto) {info}")
        return

    abas = wb.sheet_names()
    for aba in abas:
        destino = destino_aba(path, aba, len(abas))
        rotulo = f"{path.name} [{aba}]"
        if destino.exists() and not force:
            linhas.append([estudo, rotulo, "ja_existia", ""])
            continue
        try:
            sh = wb.sheet_by_name(aba)
            rows = [sh.row_values(i) for i in range(sh.nrows)]
            rows = [[None if c == "" else c for c in r] for r in rows]
            rows = [r for r in rows if any(c is not None for c in r)]
            if not rows:
                raise ValueError("aba vazia")
            header = rows[0]
            while header and header[-1] is None:
                header.pop()
            info = gravar(montar(header, rows[1:]), destino)
            linhas.append([estudo, rotulo, "ok_tolerante", info])
            print(f"  [ok_xls] {rotulo}: {info}")
        except ValueError as e:
            linhas.append([estudo, rotulo, "aba_vazia", str(e)])
        except Exception as e:
            linhas.append([estudo, rotulo, "erro", str(e)])
            print(f"  [erro] {rotulo}: {e}")


# ---------- principal ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("estudos", nargs="*", help="ex.: PSI-117 (padrão: todos)")
    ap.add_argument("--force", action="store_true", help="refaz JSON já existentes")
    args = ap.parse_args()

    pastas = [DATA / e for e in args.estudos] if args.estudos else \
        sorted(p for p in DATA.iterdir() if p.is_dir())

    linhas = []
    for pasta in pastas:
        estudo = pasta.name
        arquivos = sorted(p for p in pasta.rglob("*")
                          if p.suffix.lower() in {".csv", ".txt", ".xlsx", ".xlsm", ".xls"})
        print(f"{estudo}: {len(arquivos)} arquivos")
        for path in arquivos:
            rel = str(path.relative_to(pasta))
            ext = path.suffix.lower()

            if eh_comentario(path.name):
                linhas.append([estudo, rel, "comentario", ""])
                continue
            if path.stat().st_size > MAX_MB * 1024 * 1024:
                linhas.append([estudo, rel, "grande_demais", f"> {MAX_MB} MB"])
                print(f"  [grande] {rel}")
                continue

            if ext in {".xlsx", ".xlsm"}:
                try:
                    converter_excel(path, linhas, estudo, args.force)
                except Exception as e:
                    linhas.append([estudo, rel, "erro", str(e)])
                    print(f"  [erro] {rel}: {e}")
                continue
            if ext == ".xls":
                try:
                    converter_xls(path, linhas, estudo, args.force)
                except Exception as e:
                    linhas.append([estudo, rel, "erro", str(e)])
                    print(f"  [erro] {rel}: {e}")
                continue

            destino = path.with_suffix(".json")
            if destino.exists() and not args.force:
                linhas.append([estudo, rel, "ja_existia", ""])
                continue
            try:
                status, info = converter_texto(path, destino)
            except Exception as e:
                status, info = "erro", str(e)
            linhas.append([estudo, rel, status, info])
            print(f"  [{status}] {rel} {info}")

    DADOS.mkdir(exist_ok=True)
    saida = DADOS / "resumo_conversao.csv"
    with open(saida, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["estudo", "arquivo", "status", "detalhe"])
        w.writerows(linhas)
    print(f"\nResumo em {saida}")


if __name__ == "__main__":
    main()