import { Box, Typography } from "@mui/material";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ChartSeries, StudyChart } from "../../services/graficos";
import "./ChartRenderer.scss";

const COLORS = ["#F07A3C", "#E8BC73", "#96989B", "#D9534F", "#6FA8DC", "#9BC53D"];
const AXIS = "#96989B";
const GRID = "#343538";

const tooltipStyle = {
  contentStyle: {
    background: "#222426",
    border: "1px solid #343538",
    borderRadius: 8,
    color: "#EFEEEC",
    fontSize: 12,
  },
  labelStyle: { color: "#96989B" },
  itemStyle: { color: "#EFEEEC" },
};

const fmt = (v: number) => Number(Number(v).toPrecision(3)).toString();

function mergeSeries(series: ChartSeries[]) {
  const map = new Map<number, Record<string, number>>();
  for (const s of series) {
    for (const p of s.points) {
      const row = map.get(p.x) ?? { x: p.x };
      row[s.name] = p.y;
      map.set(p.x, row);
    }
  }
  return [...map.values()].sort((a, b) => a.x - b.x);
}

function xAxisLabel(text?: string) {
  return text
    ? { value: text, position: "insideBottom" as const, offset: 0, fill: AXIS, fontSize: 12 }
    : undefined;
}

function yAxisLabel(text?: string) {
  return text
    ? { value: text, angle: -90, position: "insideLeft" as const, fill: AXIS, fontSize: 12 }
    : undefined;
}

function Plot({ chart }: { chart: StudyChart }) {
  const series = chart.series ?? [];
  const data = chart.data ?? [];
  const multi = series.length > 1;

  if (chart.type === "line") {
    return (
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={mergeSeries(series)} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
          <CartesianGrid stroke={GRID} strokeDasharray="3 3" />
          <XAxis
            height={50}
            dataKey="x"
            type="number"
            domain={["auto", "auto"]}
            tickFormatter={fmt}
            stroke={AXIS}
            tick={{ fill: AXIS, fontSize: 12 }}
            label={xAxisLabel(chart.xLabel)}
          />
          <YAxis
            type="number"
            domain={["auto", "auto"]}
            tickFormatter={fmt}
            stroke={AXIS}
            tick={{ fill: AXIS, fontSize: 12 }}
            label={yAxisLabel(chart.yLabel)}
            width={64}
          />
          <Tooltip {...tooltipStyle} formatter={(v) => fmt(Number(v))} labelFormatter={(l) => fmt(Number(l))} />
          {multi && <Legend verticalAlign="top" height={32} wrapperStyle={{ fontSize: 12, color: AXIS }} />}
          {series.map((s, i) => (
            <Line
              key={s.name}
              dataKey={s.name}
              stroke={COLORS[i % COLORS.length]}
              strokeWidth={2}
              dot={false}
              connectNulls
              isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    );
  }

  if (chart.type === "scatter") {
    return (
      <ResponsiveContainer width="100%" height={300}>
        <ScatterChart margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
          <CartesianGrid stroke={GRID} strokeDasharray="3 3" />
          <XAxis
            height={50}
            dataKey="x"
            type="number"
            domain={["auto", "auto"]}
            tickFormatter={fmt}
            stroke={AXIS}
            tick={{ fill: AXIS, fontSize: 12 }}
            label={xAxisLabel(chart.xLabel)}
          />
          <YAxis
            dataKey="y"
            type="number"
            domain={["auto", "auto"]}
            tickFormatter={fmt}
            stroke={AXIS}
            tick={{ fill: AXIS, fontSize: 12 }}
            label={yAxisLabel(chart.yLabel)}
            width={64}
          />
          <Tooltip {...tooltipStyle} cursor={{ strokeDasharray: "3 3" }} formatter={(v) => fmt(Number(v))} />
          {multi && <Legend verticalAlign="top" height={32} wrapperStyle={{ fontSize: 12, color: AXIS }} />}
          {series.map((s, i) => (
            <Scatter
              key={s.name}
              name={s.name}
              data={s.points}
              fill={COLORS[i % COLORS.length]}
              isAnimationActive={false}
            />
          ))}
        </ScatterChart>
      </ResponsiveContainer>
    );
  }

  if (chart.type === "bar") {
    const height = Math.max(220, data.length * 36 + 40);
    return (
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data} layout="vertical" margin={{ top: 8, right: 24, left: 8, bottom: 8 }}>
          <CartesianGrid stroke={GRID} strokeDasharray="3 3" horizontal={false} />
          <XAxis type="number" stroke={AXIS} tick={{ fill: AXIS, fontSize: 12 }} allowDecimals={false} />
          <YAxis
            type="category"
            dataKey="name"
            width={130}
            stroke={AXIS}
            tick={{ fill: AXIS, fontSize: 12 }}
          />
          <Tooltip {...tooltipStyle} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
          <Bar dataKey="value" fill={COLORS[0]} radius={[0, 4, 4, 0]} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={{ top: 8, right: 16, left: 8, bottom: 8 }} barCategoryGap={2}>
        <CartesianGrid stroke={GRID} strokeDasharray="3 3" vertical={false} />
        <XAxis
          height={50}
          dataKey="name"
          stroke={AXIS}
          tick={{ fill: AXIS, fontSize: 11 }}
          label={xAxisLabel(chart.xLabel)}
        />
        <YAxis
          stroke={AXIS}
          tick={{ fill: AXIS, fontSize: 12 }}
          allowDecimals={false}
          label={yAxisLabel(chart.yLabel)}
          width={56}
        />
        <Tooltip {...tooltipStyle} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
        <Bar dataKey="value" fill={COLORS[0]} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export default function ChartRenderer({ chart }: { chart: StudyChart }) {
  return (
    <Box component={"div"} className="chart-root">
      <Box component={"div"} className="chart__head">
        <Typography className="chart__title">{chart.title}</Typography>
        <Box component={"span"} className="chart__origin">
          {chart.origin}
        </Box>
      </Box>
      <Plot chart={chart} />
      {chart.note && <Typography className="chart__note">{chart.note}</Typography>}
    </Box>
  );
}