import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
SAIDA = BASE / "dados" / "colunas_candidatos.txt"

# (estudo, trecho do nome do arquivo): usa o primeiro arquivo que combinar
CANDIDATOS = [
    ("PSI-117", "Dext.json"),
    ("PSI-117", "Kavg.json"),
    ("PSI-117", "Burning_history"),
    ("PSI-117", "Oscillatory_Cool_Flame"),
    ("PSI-117", "C12_Extinction_Diameter_vs_pressure"),
    ("PSI-117", "Radiance_Flame"),
    ("PSI-98", "SaffireData.json"),
    ("PSI-98", "CygnusTemperatureData"),
    ("PSI-98", "CygnusPressureData"),
    ("PSI-98", "Experimental table"),
    ("PSI-99", "Sample 1__Calibrated_Data"),
    ("PSI-99", "Experimental table"),
    ("PSI-100", "SaffireData.json"),
    ("PSI-100", "CygnusTemperatureData"),
    ("PSI-100", "Experimental table"),
    ("PSI-101", "Sheet_used_to_Graph"),
    ("PSI-101", "Kapton aged- results__Results94"),
    ("PSI-101", "HKPData_gmt242_1"),
    ("PSI-101", "Experimental table"),
    ("PSI-102", "GMT255hkp"),
    ("PSI-102", "Experimental table"),
    ("PSI-25", "Experimental table"),
    ("PSI-25", "Test.Matrices__Olson"),
    ("PSI-26", "Experimental table"),
    ("PSI-26", "TP_without_Data"),
    ("PSI-107", "Experimental table"),
    ("PSI-69", "Experimental table"),
    ("PSI-69", "_Mixture.json"),
    ("PSI-69", "Test 002 Results"),
    ("PSI-68", "Experimental table"),
    ("PSI-68", "Radiometer_Readings__RDTST01"),
    ("PSI-68", "_Mixture.json"),
    ("PSI-106", "Experimental table"),
    ("PSI-20", "Experimental table"),
]


def exemplos(v):
    if not isinstance(v, list):
        return []
    return [str(x)[:12] for x in v if x not in (None, "")][:2]


linhas = []
for estudo, trecho in CANDIDATOS:
    achados = [
        a for a in sorted((DATA / estudo).rglob("*.json"))
        if trecho in a.name and "metadata" not in a.parts
    ]
    if not achados:
        linhas.append(f"### {estudo} | {trecho}: NAO ENCONTRADO\n")
        continue
    arq = achados[0]
    try:
        obj = json.loads(arq.read_text(encoding="utf-8-sig"))
        if not isinstance(obj, dict):
            raise ValueError("JSON nao e um objeto")
    except Exception as e:
        linhas.append(f"### {estudo} | {arq.name}: erro {e}\n")
        continue
    colunas = [k for k in obj if k != "columns"]
    n = max((len(v) for v in obj.values() if isinstance(v, list)), default=0)
    linhas.append(f"### {estudo} | {arq.name} | {n} linhas, {len(colunas)} colunas")
    for k in colunas[:70]:
        linhas.append(f"  {k!r}: {exemplos(obj[k])}")
    if len(colunas) > 70:
        linhas.append(f"  ... mais {len(colunas) - 70} colunas")
    linhas.append("")

SAIDA.parent.mkdir(exist_ok=True)
SAIDA.write_text("\n".join(linhas), encoding="utf-8")
print(f"Pronto: {SAIDA}")