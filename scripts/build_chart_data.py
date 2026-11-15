"""
Gera os JSON leves do dashboard de cada estudo (KPIs + gráficos) a partir dos JSON pesados em data/.

Uso (na raiz do projeto):
    python scripts/build_chart_data.py

Saída: views/thunderbolts/public/data/charts/<PSI>.json  (+ index.json)
Cada série tem no máximo ~300 pontos.
"""
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
OUT = BASE / "views" / "thunderbolts" / "public" / "data" / "charts"
MAX_POINTS = 300

ISS = "ISS experiment"
SAFFIRE = "Spaceflight (Cygnus, free-flying)"
SIM = "CFD simulation vs. experiment"

# ---------------------------------------------------------------------------
# Configuração: um dashboard por estudo
#   headline: frase curta que resume o estudo
#   kpis: indicadores calculados dos dados. op = rows | unique | max | min | mean | sum | range
#   charts: ordem = ordem de exibição. span 2 = largura total, span 1 = meia largura
#     type: line | scatter (series com x/y), bar (count / sum_cat+sum_val), hist (col)
#     where: {coluna: valor}; x_min / y_min descartam pontos abaixo do limite
# ---------------------------------------------------------------------------
STUDIES = {
    "PSI-117": {
        "headline": "Computer simulation (OpenFOAM) of burning fuel droplets, including cool flames, checked against flight data.",
        "kpis": [
            {"label": "Pressures simulated", "file": "C12_Extinction_Diameter_vs_pressure",
             "op": "range", "col": "P (atm)", "unit": "atm"},
            {"label": "Peak temperature (cool-flame run)", "file": "Oscillatory_Cool_Flame",
             "op": "max", "col": "T_max(K)", "unit": "K"},
            {"label": "Time steps in cool-flame run", "file": "Oscillatory_Cool_Flame",
             "op": "rows", "col": "Time(sec)"},
        ],
        "charts": [
            {"id": "dext", "title": "Extinction diameter vs. pressure", "type": "scatter", "span": 1,
             "file": "C12_Extinction_Diameter_vs_pressure", "origin": SIM,
             "xLabel": "Pressure (atm)", "yLabel": "Extinction diameter (mm)",
             "series": [
                 {"name": "Hot flame (experiment)", "x": "P (atm)", "y": "Dext_HF_EXPT"},
                 {"name": "Hot flame (model)", "x": "P (atm)_2", "y": "Dext_HF_model"},
                 {"name": "Cool flame (experiment)", "x": "P (atm)_3", "y": "Dext_CF_EXPT"},
                 {"name": "Cool flame (model)", "x": "P (atm)_4", "y": "Dext_CF_Model"},
             ]},
            {"id": "d2", "title": "Droplet burning history (d² vs. time)", "type": "scatter", "span": 1,
             "file": "Burning_history", "origin": SIM,
             "xLabel": "Time (s)", "yLabel": "d² (mm²)",
             "series": [
                 {"name": "Experiment", "x": "t", "y": "d^2 (mm^2)"},
                 {"name": "Model (1 atm)", "x": "t_3", "y": "d^2 (mm^2)_2"},
             ]},
            {"id": "tmax", "title": "Oscillatory cool flame: peak temperature", "type": "line", "span": 2,
             "file": "Oscillatory_Cool_Flame", "origin": SIM,
             "xLabel": "Time (s)", "yLabel": "T max (K)",
             "series": [{"name": "T max", "x": "Time(sec)", "y": "T_max(K)"}]},
        ],
    },
    "PSI-98": {
        "headline": "SAFFIRE-I: a large fire set inside an unmanned Cygnus spacecraft, tracked by onboard telemetry.",
        "kpis": [
            {"label": "Samples", "file": "Experimental table", "op": "rows", "col": "Material"},
            {"label": "Longest burn", "file": "Experimental table", "op": "max",
             "col": "Burn Time (s)", "unit": "s"},
            {"label": "Cabin temperature", "file": "CygnusTemperatureData", "op": "range",
             "col": "PCM Air Temp (degC)", "unit": "°C"},
            {"label": "Telemetry records", "file": "SaffireData", "op": "rows", "col": "SaffireTimestamp"},
        ],
        "charts": [
            {"id": "rad", "title": "Radiometers (raw telemetry)", "type": "line", "span": 2,
             "file": "SaffireData", "origin": SAFFIRE,
             "xLabel": "Time (s)", "yLabel": "Raw value (uncalibrated)",
             "note": "Raw telemetry, not calibrated.",
             "series": [{"name": f"Radiometer {i}", "x": "Relative Time (s)",
                         "y": f"Radiometer{i}Value"} for i in (1, 2, 3, 4)]},
            {"id": "temp", "title": "Cabin air temperature", "type": "line", "span": 1,
             "file": "CygnusTemperatureData", "origin": SAFFIRE,
             "xLabel": "Time (s)", "yLabel": "Temperature (°C)",
             "series": [{"name": "PCM air", "x": "Relative Time (s)", "y": "PCM Air Temp (degC)"}]},
            {"id": "press", "title": "Cabin pressure", "type": "line", "span": 1,
             "file": "CygnusPressureData", "origin": SAFFIRE,
             "xLabel": "Time (s)", "yLabel": "Pressure (psi)",
             "series": [{"name": "PCM", "x": "Relative Time (s)", "y": "PCM Press (psi)"}]},
            {"id": "samples", "title": "Samples by material", "type": "bar", "span": 2,
             "file": "Experimental table", "origin": SAFFIRE, "count": "Material", "top": 8},
        ],
    },
    "PSI-99": {
        "headline": "SAFFIRE-II: spacecraft fire experiment with calibrated sensor data for each burned sample.",
        "kpis": [
            {"label": "Samples", "file": "Experimental table", "op": "rows", "col": "Material"},
            {"label": "Materials", "file": "Experimental table", "op": "unique", "col": "Material"},
            {"label": "Peak plume temperature ({sample})", "file": "Calibrated_Data", "pick_max": ["Plume Temp 1 (TC1)", "Plume Temp 4 (TC4)", "Sample Temp 1 (TC7)"],
             "op": "max", "col": "Plume Temp 1 (TC1)", "unit": "°C"},
            {"label": "Sensor readings ({sample})", "file": "Calibrated_Data", "pick_max": ["Plume Temp 1 (TC1)", "Plume Temp 4 (TC4)", "Sample Temp 1 (TC7)"],
             "op": "rows", "col": "Elapsed Time (s)"},
        ],
        "charts": [
            {"id": "temp", "title": "Plume and sample temperature ({sample})", "type": "line", "span": 1,
             "file": "Calibrated_Data", "pick_max": ["Plume Temp 1 (TC1)", "Plume Temp 4 (TC4)", "Sample Temp 1 (TC7)"], "origin": SAFFIRE,
             "xLabel": "Elapsed time (s)", "yLabel": "Temperature (°C)",
             "series": [
                 {"name": "Plume TC1", "x": "Elapsed Time (s)", "y": "Plume Temp 1 (TC1)"},
                 {"name": "Plume TC4", "x": "Elapsed Time (s)", "y": "Plume Temp 4 (TC4)"},
                 {"name": "Sample TC7", "x": "Elapsed Time (s)", "y": "Sample Temp 1 (TC7)"},
             ]},
            {"id": "rad", "title": "Radiometer 1 ({sample})", "type": "line", "span": 1,
             "file": "Calibrated_Data", "pick_max": ["Plume Temp 1 (TC1)", "Plume Temp 4 (TC4)", "Sample Temp 1 (TC7)"], "origin": SAFFIRE,
             "xLabel": "Elapsed time (s)", "yLabel": "mW/cm²",
             "series": [{"name": "Radiometer 1", "x": "Elapsed Time (s)", "y": "Radiometer 1"}]},
            {"id": "samples", "title": "Samples by material", "type": "bar", "span": 2,
             "file": "Experimental table", "origin": SAFFIRE, "count": "Material", "top": 8},
        ],
    },
    "PSI-100": {
        "headline": "SAFFIRE-III: third spacecraft fire experiment, with telemetry and the sample matrix.",
        "kpis": [
            {"label": "Samples", "file": "Experimental table", "op": "rows", "col": "Sample Number"},
            {"label": "Peak cabin temperature", "file": "CygnusTemperatureData", "op": "max",
             "col": "PCM Air Temp (degC)", "unit": "°C", "min_value": 1},
            {"label": "Telemetry records", "file": "SaffireData", "op": "rows", "col": "SaffireTimestamp"},
        ],
        "charts": [
            {"id": "temp", "title": "Cabin air temperature", "type": "line", "span": 1,
             "file": "CygnusTemperatureData", "origin": SAFFIRE,
             "xLabel": "Time (s)", "yLabel": "Temperature (°C)",
             "x_min": 0, "y_min": 1,
             "series": [{"name": "PCM air", "x": "Relative Time (s)", "y": "PCM Air Temp (degC)"}]},
            {"id": "rad", "title": "Radiometers (telemetry)", "type": "line", "span": 1,
             "file": "SaffireData", "origin": SAFFIRE,
             "xLabel": "Time (s)", "yLabel": "Reading",
             "series": [{"name": f"Radiometer {i}", "x": "Relative Time (s)",
                         "y": f"Radiometer{i}Value"} for i in (1, 2, 3, 4)]},
            {"id": "samples", "title": "Samples by material", "type": "bar", "span": 2,
             "file": "Experimental table", "origin": SAFFIRE, "count": "Material", "top": 8},
        ],
    },
    "PSI-101": {
        "headline": "Smoke detection in microgravity: how detectors respond to smoke from heated materials.",
        "kpis": [
            {"label": "Test runs", "file": "Experimental table_SAME-R", "op": "rows", "col": "SAME Test #"},
            {"label": "Sample types", "file": "Experimental table_SAME-R", "op": "unique", "col": "Sample Type"},
            {"label": "Particles measured (aged Kapton)", "file": "Results94_post-3", "op": "rows", "col": "Area"},
        ],
        "charts": [
            {"id": "detector", "title": "Smoke detector response", "type": "line", "span": 2,
             "file": "Sheet_used_to_Graph", "origin": ISS,
             "xLabel": "Time (s)", "yLabel": "Detector signal (V)",
             "series": [
                 {"name": "Obscuration", "x": "Time", "y": "ISSDetectorObscurationMeasurement(Volts)"},
                 {"name": "Scatter", "x": "Time", "y": "ISSDetectorScatterMeasurement(Volts)"},
             ]},
            {"id": "particles", "title": "Particle size distribution (aged Kapton)", "type": "hist", "span": 1,
             "file": "Results94_post-3", "origin": ISS, "col": "Area", "bins": 20,
             "xLabel": "Particle area", "yLabel": "Count"},
            {"id": "samples", "title": "Tests by sample type", "type": "bar", "span": 1,
             "file": "Experimental table_SAME-R", "origin": ISS, "count": "Sample Type", "top": 8},
        ],
    },
    "PSI-102": {
        "headline": "Smoke aging and detector response across test materials and air flows.",
        "kpis": [
            {"label": "Test samples", "file": "Experimental table_SAME", "op": "rows", "col": "Sample #"},
            {"label": "Longest aging", "file": "Experimental table_SAME", "op": "max",
             "col": "Aging Duration (minutes)", "unit": "min"},
            {"label": "Housekeeping records", "file": "GMT255hkp", "op": "rows", "col": "Time"},
        ],
        "charts": [
            {"id": "detector", "title": "Smoke detector response (test 2)", "type": "line", "span": 2,
             "file": "GMT255hkp", "origin": ISS, "where": {"TestNumber": 2},
             "xLabel": "Elapsed test time (s)", "yLabel": "Detector signal (V)",
             "series": [
                 {"name": "Obscuration", "x": "ElapsedTestTime(Secs)",
                  "y": "ISSDetectorObscurationMeasurement(Volts)"},
                 {"name": "Scatter", "x": "ElapsedTestTime(Secs)",
                  "y": "ISSDetectorScatterMeasurement(Volts)"},
             ]},
            {"id": "samples", "title": "Tests by sample material", "type": "bar", "span": 2,
             "file": "Experimental table_SAME", "origin": ISS, "count": "Sample Material", "top": 8},
        ],
    },
    "PSI-25": {
        "headline": "BASS-II: how different solid materials burn in microgravity, one test per sample.",
        "kpis": [
            {"label": "Tests", "file": "Experimental table", "op": "rows", "col": "Test #"},
            {"label": "Materials", "file": "Experimental table", "op": "unique", "col": "Fuel Sample Material"},
        ],
        "charts": [
            {"id": "samples", "title": "Tests by material", "type": "bar", "span": 2,
             "file": "Experimental table", "origin": ISS, "count": "Fuel Sample Material", "top": 10},
        ],
    },
    "PSI-26": {
        "headline": "BASS: how different solid materials burn in microgravity, one test per sample.",
        "kpis": [
            {"label": "Tests", "file": "Experimental table", "op": "rows", "col": "As Run Test #"},
            {"label": "Materials", "file": "Experimental table", "op": "unique", "col": "Fuel Sample Material"},
        ],
        "charts": [
            {"id": "samples", "title": "Tests by material", "type": "bar", "span": 2,
             "file": "Experimental table", "origin": ISS, "count": "Fuel Sample Material", "top": 10},
        ],
    },
    "PSI-107": {
        "headline": "Gas-jet flames burned with different fuels and nozzle sizes.",
        "kpis": [
            {"label": "Flames", "file": "Experimental table", "op": "rows", "col": "Fuel"},
            {"label": "Fuels", "file": "Experimental table", "op": "unique", "col": "Fuel"},
            {"label": "Nozzle diameters", "file": "Experimental table", "op": "range",
             "col": "Nozzle (mm)", "unit": "mm"},
        ],
        "charts": [
            {"id": "fuels", "title": "Flames by fuel", "type": "bar", "span": 1,
             "file": "Experimental table", "origin": ISS, "count": "Fuel", "top": 8},
            {"id": "nozzle", "title": "Nozzle diameter vs. fuel rate", "type": "scatter", "span": 1,
             "file": "Experimental table", "origin": ISS,
             "xLabel": "Nozzle (mm)", "yLabel": "HC fuel rate (mg/s)",
             "series": [{"name": "Flames", "x": "Nozzle (mm)", "y": "HC Fuel Rate (mg/s)"}]},
        ],
    },
    "PSI-69": {
        "headline": "Burning fuel droplets: how burn time and extinction depend on droplet size and fuel.",
        "kpis": [
            {"label": "Tests", "file": "Experimental table", "op": "rows", "col": "FLEX Test #"},
            {"label": "Fuels", "file": "Experimental table", "op": "unique", "col": "Fuel"},
            {"label": "Longest burn", "file": "Experimental table", "op": "max",
             "col": "Burn time; s", "unit": "s"},
            {"label": "Largest droplet", "file": "Experimental table", "op": "max",
             "col": "Droplet initial diameter; mm", "unit": "mm"},
        ],
        "charts": [
            {"id": "burn", "title": "Initial droplet diameter vs. burn time", "type": "scatter", "span": 1,
             "file": "Experimental table", "origin": ISS,
             "xLabel": "Initial diameter (mm)", "yLabel": "Burn time (s)",
             "series": [{"name": "Tests", "x": "Droplet initial diameter; mm", "y": "Burn time; s"}]},
            {"id": "ext", "title": "Initial vs. extinction diameter", "type": "scatter", "span": 1,
             "file": "Experimental table", "origin": ISS,
             "xLabel": "Initial diameter (mm)", "yLabel": "Extinction diameter (mm)",
             "series": [{"name": "Tests", "x": "Droplet initial diameter; mm",
                         "y": "Visible flame extinction diameter; mm"}]},
            {"id": "fuels", "title": "Tests by fuel", "type": "bar", "span": 2,
             "file": "Experimental table", "origin": ISS, "count": "Fuel", "top": 8},
        ],
    },
    "PSI-106": {
        "headline": "Gas-jet flame tests across different fuel mixtures.",
        "kpis": [
            {"label": "Tests", "file": "Experimental table", "op": "rows", "col": "Test Date"},
            {"label": "Fuel mixtures", "file": "Experimental table", "op": "unique", "col": "Fuel Type"},
        ],
        "charts": [
            {"id": "fuels", "title": "Tests by fuel", "type": "bar", "span": 2,
             "file": "Experimental table", "origin": ISS, "count": "Fuel Type", "top": 8},
        ],
    },
    "PSI-20": {
        "headline": "Burner experiments: flames ignited at different oxygen concentrations and fuels.",
        "kpis": [
            {"label": "Test runs", "file": "Experimental table", "op": "rows", "col": "Year"},
            {"label": "Flames ignited", "file": "Experimental table", "op": "sum", "col": "Flames Ignited"},
            {"label": "Burner sizes", "file": "Experimental table", "op": "unique", "col": "Burner Size (mm)"},
        ],
        "charts": [
            {"id": "flames", "title": "Flames ignited by fuel bottle", "type": "bar", "span": 2,
             "file": "Experimental table", "origin": ISS,
             "sum_cat": "Fuel Bottle", "sum_val": "Flames Ignited", "top": 8},
        ],
    },
}


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------
def num(v):
    if v is None:
        return None
    s = str(v).strip().replace("%", "")
    if not s:
        return None
    try:
        f = float(s)
    except ValueError:
        return None
    return f if math.isfinite(f) else None


def clean(f):
    return float(f"{f:.6g}")


def fmt_value(v):
    if abs(v) >= 100:
        return f"{v:,.0f}"
    if float(v).is_integer():
        return str(int(v))
    return f"{v:.3g}"


def load_cols(path):
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    cols = {}
    for k, v in raw.items():
        if k == "columns" or not isinstance(v, list):
            continue
        cols.setdefault(k.strip(), v)
    return cols


def find_file(psi, part):
    pasta = DATA / psi
    if not pasta.exists():
        raise FileNotFoundError(f"pasta {pasta} não existe")
    found = [p for p in pasta.rglob("*.json") if part in p.name]
    if len(found) != 1:
        nomes = ", ".join(p.name[:60] for p in found) or "nenhum"
        raise FileNotFoundError(f"'{part}' em {psi}: {len(found)} arquivos ({nomes})")
    return found[0]


_PICK_CACHE = {}


def resolve_file(psi, spec):
    """Devolve (caminho, rótulo). Com pick_max, escolhe entre vários arquivos o que tem o maior pico."""
    colunas = spec.get("pick_max")
    if not colunas:
        return find_file(psi, spec["file"]), ""
    chave = (psi, spec["file"], tuple(colunas))
    if chave not in _PICK_CACHE:
        candidatos = sorted(p for p in (DATA / psi).rglob("*.json") if spec["file"] in p.name)
        if not candidatos:
            raise FileNotFoundError(f"'{spec['file']}' em {psi}: nenhum arquivo")
        melhor, melhor_v = None, None
        for p in candidatos:
            c = load_cols(p)
            vals = [n for nome in colunas for n in (num(v) for v in col(c, nome)) if n is not None]
            if vals and (melhor_v is None or max(vals) > melhor_v):
                melhor, melhor_v = p, max(vals)
        if melhor is None:
            raise ValueError("nenhum candidato com valores numéricos")
        m = re.search(r"Sample (\d+)", melhor.name)
        tag = f"sample {m.group(1)}" if m else melhor.stem[:30]
        print(f"INFO {psi}: '{spec['file']}' -> {tag} (pico {melhor_v:.1f}, entre {len(candidatos)} arquivos)")
        _PICK_CACHE[chave] = (melhor, tag)
    return _PICK_CACHE[chave]


def col(cols, name):
    key = name.strip()
    if key not in cols:
        parecidos = [c for c in cols if key.lower()[:6] in c.lower()][:5]
        raise KeyError(f"coluna '{name}' não existe. Parecidas: {parecidos}")
    return cols[key]


def downsample(pts, n=MAX_POINTS):
    if len(pts) <= n:
        return pts
    step = (len(pts) - 1) / (n - 1)
    idx = sorted({round(i * step) for i in range(n)})
    return [pts[i] for i in idx]


def row_ok(cols, i, where):
    for c, target in (where or {}).items():
        vals = col(cols, c)
        if i >= len(vals) or num(vals[i]) != target:
            return False
    return True


def build_series(cols, spec, chart):
    xs, ys = col(cols, spec["x"]), col(cols, spec["y"])
    where = chart.get("where")
    x_min, y_min = chart.get("x_min"), chart.get("y_min")
    pts = []
    for i in range(min(len(xs), len(ys))):
        x, y = num(xs[i]), num(ys[i])
        if x is None or y is None:
            continue
        if x_min is not None and x < x_min:
            continue
        if y_min is not None and y < y_min:
            continue
        if where and not row_ok(cols, i, where):
            continue
        pts.append((x, y))
    total = len(pts)
    pts = downsample(pts)
    pontos = [{"x": clean(x), "y": clean(y)} for x, y in pts]
    return {"name": spec["name"], "points": pontos}, f"{total} de {min(len(xs), len(ys))} linhas"


def top_with_other(counter, names, top):
    items = counter.most_common()
    head = items[:top]
    rest = sum(v for _, v in items[top:])
    data = [{"name": names[k], "value": clean(v)} for k, v in head]
    if rest:
        data.append({"name": "Other", "value": clean(rest)})
    return data


def build_bar(cols, chart):
    names = {}
    counter = Counter()
    if "count" in chart:
        for v in col(cols, chart["count"]):
            s = str(v).strip()
            if not s or s.lower() in ("n/a", "none"):
                continue
            k = s.lower()
            names.setdefault(k, s)
            counter[k] += 1
    else:
        cats, vals = col(cols, chart["sum_cat"]), col(cols, chart["sum_val"])
        for c, v in zip(cats, vals):
            s, f = str(c).strip(), num(v)
            if not s or f is None:
                continue
            k = s.lower()
            names.setdefault(k, s)
            counter[k] += f
    return top_with_other(counter, names, chart.get("top", 8))


def build_hist(cols, chart):
    vals = sorted(v for v in (num(x) for x in col(cols, chart["col"])) if v is not None and v >= 0)
    if not vals:
        raise ValueError("sem valores numéricos")
    hi = vals[min(len(vals) - 1, int(len(vals) * 0.99))]
    lo = vals[0]
    bins = chart.get("bins", 20)
    width = (hi - lo) / bins or 1
    counts = [0] * bins
    for v in vals:
        if v > hi:
            continue
        counts[min(int((v - lo) / width), bins - 1)] += 1
    return [{"name": f"{lo + i * width:.3g}", "value": c} for i, c in enumerate(counts)]


def build_chart(psi, chart):
    caminho, tag = resolve_file(psi, chart)
    cols = load_cols(caminho)
    keys = ("id", "title", "type", "origin", "xLabel", "yLabel", "note", "span")
    out = {k: chart[k] for k in keys if k in chart}
    out["title"] = chart["title"].replace("{sample}", tag)
    if chart["type"] in ("line", "scatter"):
        series, info = [], []
        for spec in chart["series"]:
            s, detalhe = build_series(cols, spec, chart)
            if s["points"]:
                series.append(s)
            info.append(f"{spec['name']}: {detalhe}")
        if not series:
            raise ValueError("nenhum ponto numérico encontrado")
        out["series"] = series
        return out, "; ".join(info)
    if chart["type"] == "bar":
        out["data"] = build_bar(cols, chart)
        return out, f"{len(out['data'])} barras"
    if chart["type"] == "hist":
        out["data"] = build_hist(cols, chart)
        return out, f"{len(out['data'])} faixas"
    raise ValueError(f"tipo desconhecido: {chart['type']}")


def build_kpi(psi, spec):
    caminho, tag = resolve_file(psi, spec)
    cols = load_cols(caminho)
    raw = col(cols, spec["col"])
    op = spec["op"]
    if op == "rows":
        valor = fmt_value(sum(1 for v in raw if str(v).strip()))
    elif op == "unique":
        valor = fmt_value(len({str(v).strip().lower() for v in raw if str(v).strip()}))
    else:
        minimo = spec.get("min_value")
        nums = [n for n in (num(v) for v in raw) if n is not None and (minimo is None or n >= minimo)]
        if not nums:
            raise ValueError("sem valores numéricos")
        if op == "max":
            valor = fmt_value(max(nums))
        elif op == "min":
            valor = fmt_value(min(nums))
        elif op == "mean":
            valor = fmt_value(sum(nums) / len(nums))
        elif op == "sum":
            valor = fmt_value(sum(nums))
        elif op == "range":
            valor = f"{fmt_value(min(nums))}–{fmt_value(max(nums))}"
        else:
            raise ValueError(f"op desconhecida: {op}")
    kpi = {"label": spec["label"].replace("{sample}", tag), "value": valor}
    if spec.get("unit"):
        kpi["unit"] = spec["unit"]
    return kpi


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    erros = 0
    index = {}
    for psi, cfg in STUDIES.items():
        kpis, charts = [], []
        for spec in cfg.get("kpis", []):
            try:
                kpi = build_kpi(psi, spec)
                kpis.append(kpi)
                print(f"OK   {psi} / KPI {kpi['label']}: {kpi['value']} {kpi.get('unit', '')}".rstrip())
            except Exception as e:  # noqa: BLE001
                erros += 1
                print(f"ERRO {psi} / KPI {spec['label']}: {e}")
        for chart in cfg["charts"]:
            try:
                res, info = build_chart(psi, chart)
                charts.append(res)
                print(f"OK   {psi} / {chart['id']}: {info}")
            except Exception as e:  # noqa: BLE001
                erros += 1
                print(f"ERRO {psi} / {chart['id']}: {e}")
        if charts:
            doc = {"study": psi, "headline": cfg.get("headline", ""), "kpis": kpis, "charts": charts}
            with open(OUT / f"{psi}.json", "w", encoding="utf-8") as fh:
                json.dump(doc, fh, ensure_ascii=False, separators=(",", ":"))
            index[psi] = [c["id"] for c in charts]
    with open(OUT / "index.json", "w", encoding="utf-8") as fh:
        json.dump(index, fh, ensure_ascii=False)
    print(f"\n{len(index)} estudos com dashboard, {erros} erro(s). Saída: {OUT}")
    sys.exit(1 if erros else 0)


if __name__ == "__main__":
    main()