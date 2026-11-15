export type Study = {
  id: string;
  titulo: string;
  sigla: string;
  area: string;
  subarea: string;
  tipo_projeto: string;
  plataforma: string;
  centro: string;
  inicio: string;
  fim: string;
  liberado_em: string;
  palavras_chave: string[];
  relacionados: string[];
  hardware: string[];
  imagem: string;
  objetivo: string;
  abordagem: string;
  hipotese: string;
  impactos_terra: string;
};

export async function loadStudies(): Promise<Study[]> {
  const res = await fetch("/data/catalogo_base.json");
  if (!res.ok) throw new Error(`Could not load the catalog (${res.status})`);
  return res.json();
}