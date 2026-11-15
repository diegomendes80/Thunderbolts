// Lê os JSON leves gerados por scripts/build_chart_data.py (public/data/charts/).

export type ChartPoint = { x: number; y: number };
export type ChartSeries = { name: string; points: ChartPoint[] };
export type ChartDatum = { name: string; value: number };

export type StudyChart = {
  id: string;
  title: string;
  type: "line" | "scatter" | "bar" | "hist";
  origin: string;
  span?: 1 | 2;
  xLabel?: string;
  yLabel?: string;
  note?: string;
  series?: ChartSeries[];
  data?: ChartDatum[];
};

export type StudyKpi = { label: string; value: string; unit?: string };

export type StudyDashboard = {
  study: string;
  headline: string;
  kpis: StudyKpi[];
  charts: StudyChart[];
};

export type ChartIndex = Record<string, string[]>;

let indexPromise: Promise<ChartIndex> | null = null;

export function loadChartIndex(): Promise<ChartIndex> {
  if (!indexPromise) {
    indexPromise = fetch("/data/charts/index.json")
      .then((res) => (res.ok ? (res.json() as Promise<ChartIndex>) : {}))
      .catch(() => ({}));
  }
  return indexPromise;
}

export async function loadStudyDashboard(studyId: string): Promise<StudyDashboard | null> {
  const index = await loadChartIndex();
  if (!index[studyId]?.length) return null;
  try {
    const res = await fetch(`/data/charts/${studyId}.json`);
    if (!res.ok) return null;
    return (await res.json()) as StudyDashboard;
  } catch {
    return null;
  }
}