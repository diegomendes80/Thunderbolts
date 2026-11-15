import requests

URL = "https://psi.nasa.gov/geode-py/ws/studies/PSI-117/download"
params = {"file": "6a28273ad9d7246402cb43e3", "version": 1,
          "studyVersion": 2, "redirect": "false"}

r = requests.get(URL, params=params, timeout=(10, 60))
link = r.text.strip()
print("link ok:", link.startswith("https://"))

r2 = requests.get(link, timeout=(10, 120))
print("status:", r2.status_code, "| bytes:", len(r2.content), "(esperado 11059)")
open("teste.xlsx", "wb").write(r2.content)