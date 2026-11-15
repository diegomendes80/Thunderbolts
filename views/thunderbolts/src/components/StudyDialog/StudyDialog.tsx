import { useEffect, useState } from "react";
import { Box, Dialog, DialogContent, IconButton, Typography, useMediaQuery, useTheme } from "@mui/material";
import type { Study } from "../../services/studies";
import { loadStudyDashboard } from "../../services/graficos";
import type { StudyDashboard } from "../../services/graficos";
import ChartRenderer from "../ChartRenderer/ChartRenderer";
import StudyAbout from "../StudyAbout/StudyAbout";
import "./StudyDialog.scss";

type Props = {
  study: Study | null;
  onClose: () => void;
};

function toText(value: unknown): string {
  if (Array.isArray(value)) return value.map(String).join("\n\n");
  return typeof value === "string" ? value : "";
}

export default function StudyDialog({ study, onClose }: Props) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down("sm"));
  // undefined = carregando, null = estudo sem dashboard
  const [dash, setDash] = useState<StudyDashboard | null | undefined>(undefined);

  useEffect(() => {
    if (!study) return;
    let alive = true;
    setDash(undefined);
    loadStudyDashboard(study.id).then((result) => {
      if (alive) setDash(result);
    });
    return () => {
      alive = false;
    };
  }, [study]);

  return (
    <Dialog
      open={Boolean(study)}
      onClose={onClose}
      fullScreen={fullScreen}
      fullWidth
      maxWidth="lg"
      scroll="paper"
      className="study-dialog-root"
    >
      {study && (
        <>
          <Box component={"div"} className="study-dialog__header">
            <Box component={"div"} className="study-dialog__heading">
              <Typography className="study-dialog__id">
                {study.id}
                {study.sigla ? ` · ${study.sigla}` : ""}
              </Typography>
              <Typography component={"h2"} className="study-dialog__title">
                {study.titulo}
              </Typography>
              {dash?.headline && <Typography className="study-dialog__headline">{dash.headline}</Typography>}
            </Box>
            <IconButton aria-label="Close" onClick={onClose} className="study-dialog__close">
              ×
            </IconButton>
          </Box>

          <DialogContent className="study-dialog__content">
            {dash === undefined && <Typography className="study-dialog__text">Loading dashboard…</Typography>}

            {dash === null && (
              <Box component={"div"} className="study-dialog__empty">
                Charts are not available for this study yet. Its data has not been processed.
              </Box>
            )}

            {dash && dash.kpis.length > 0 && (
              <Box component={"div"} className="study-dialog__kpis">
                {dash.kpis.map((kpi) => (
                  <Box component={"div"} className="study-dialog__kpi" key={kpi.label}>
                    <Typography className="study-dialog__kpi-label">{kpi.label}</Typography>
                    <Typography className="study-dialog__kpi-value">
                      {kpi.value}
                      {kpi.unit && <span className="study-dialog__kpi-unit"> {kpi.unit}</span>}
                    </Typography>
                  </Box>
                ))}
              </Box>
            )}

            {dash && (
              <Box component={"div"} className="study-dialog__charts">
                {dash.charts.map((chart) => (
                  <Box
                    component={"div"}
                    key={chart.id}
                    className={`study-dialog__cell${chart.span === 2 ? " study-dialog__cell--wide" : ""}`}
                  >
                    <ChartRenderer chart={chart} />
                  </Box>
                ))}
              </Box>
            )}

            <StudyAbout
              key={study.id}
              sections={[
                { key: "objective", label: "Objective", text: toText(study.objetivo) },
                { key: "approach", label: "Approach", text: toText(study.abordagem) },
                { key: "earth", label: "Benefits on Earth", text: toText(study.impactos_terra) },
              ]}
            />
          </DialogContent>
        </>
      )}
    </Dialog>
  );
}