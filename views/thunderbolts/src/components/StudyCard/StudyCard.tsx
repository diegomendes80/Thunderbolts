import "./StudyCard.scss";
import type { KeyboardEvent } from "react";
import { Box, Typography } from "@mui/material";
import type { Study } from "../../services/studies";

type Props = {
  study: Study;
  chartCount: number;
  onSelect: (study: Study) => void;
};

export const StudyCard = ({ study, chartCount, onSelect }: Props) => {
  const tags = [
    study.subarea,
    study.tipo_projeto,
    ...study.palavras_chave.slice(0, 3),
  ].filter(Boolean);

  const handleKeyDown = (e: KeyboardEvent<HTMLElement>) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onSelect(study);
    }
  };

  return (
    <Box
      component={"article"}
      className="study-card-root"
      role="button"
      tabIndex={0}
      aria-label={`Open ${study.id}: ${study.titulo}`}
      onClick={() => onSelect(study)}
      onKeyDown={handleKeyDown}
      sx={{
        cursor: "pointer",
        "&:focus-visible": { outline: "2px solid #F07A3C", outlineOffset: 2 },
      }}
    >
      <Box component={"div"} className="study-card__top">
        <Typography variant="body2" className="study-card__id">
          {study.id}
        </Typography>
        {study.sigla && (
          <Typography variant="body2" className="study-card__acronym">
            {study.sigla}
          </Typography>
        )}
      </Box>

      <Typography variant="h3" className="study-card__title">
        {study.titulo}
      </Typography>

      <Typography variant="body2" className="study-card__text">
        {study.objetivo}
      </Typography>

      <Box component={"div"} className="study-card__tags">
        {tags.map((tag, i) => (
          <span className="tag" key={`${tag}-${i}`}>
            {tag}
          </span>
        ))}
      </Box>

      <Typography
        variant="body2"
        className="study-card__footer"
        sx={{
          marginTop: "auto",
          paddingTop: "12px",
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: "0.72rem",
          letterSpacing: "0.06em",
          textTransform: "uppercase",
          color: chartCount > 0 ? "#F07A3C" : "#96989B",
        }}
      >
        {chartCount > 0
          ? `${chartCount} ${chartCount === 1 ? "chart" : "charts"} · View dashboard →`
          : "Details · No processed data yet"}
      </Typography>
    </Box>
  );
};