import "./StudySearch.scss";
import { useDeferredValue, useEffect, useMemo, useState } from "react";
import { Box, GlobalStyles, InputBase, Typography } from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import Fuse from "fuse.js";
import { loadStudies, type Study } from "../../services/studies";
import { loadChartIndex, type ChartIndex } from "../../services/graficos";
import { StudyCard } from "../StudyCard/StudyCard";
import StudyDialog from "../StudyDialog/StudyDialog";

export const StudySearch = () => {
  const [studies, setStudies] = useState<Study[]>([]);
  const [chartIndex, setChartIndex] = useState<ChartIndex>({});
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<Study | null>(null);

  // Mantém a digitação fluida: a lista de cards acompanha a busca sem travar o campo.
  const deferredQuery = useDeferredValue(query);

  useEffect(() => {
    loadStudies()
      .then(setStudies)
      .catch((e: Error) => setError(e.message));
    loadChartIndex().then(setChartIndex);
  }, []);

  const fuse = useMemo(
    () =>
      new Fuse<Study>(studies, {
        keys: [
          { name: "titulo", weight: 3 },
          { name: "sigla", weight: 3 },
          { name: "id", weight: 3 },
          { name: "palavras_chave", weight: 2 },
          { name: "subarea", weight: 2 },
          { name: "tipo_projeto", weight: 1 },
          { name: "plataforma", weight: 1 },
          { name: "hardware", weight: 1 },
        ],
        threshold: 0.3,
        ignoreLocation: true,
        minMatchCharLength: 2,
      }),
    [studies]
  );

  const results = useMemo(() => {
    const q = deferredQuery.trim();
    if (!q) return studies;
    return fuse.search(q).map((r) => r.item);
  }, [deferredQuery, studies, fuse]);

  return (
    <Box component={"section"} id="science" className="study-search-root">
      {/* Reserva o espaço da barra de rolagem: a página não "pula" quando ela aparece ou some. */}
      <GlobalStyles styles={{ html: { scrollbarGutter: "stable" } }} />

      <Box component={"div"} className="study-search__header">
        <Typography variant="body2" className="header__eyebrow">
          THE SCIENCE
        </Typography>
        <Typography variant="h2" className="header__title">
          Explore the investigations
        </Typography>
        <Typography variant="body1" className="header__text">
          Search the NASA PSI combustion studies by title, keyword or acronym.
        </Typography>
      </Box>

      <Box component={"div"} className="study-search__bar">
        <SearchIcon className="bar__icon" />
        <InputBase
          className="bar__input"
          placeholder="Try: cool flames, soot, SAFFIRE, smoke detection"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          fullWidth
          inputProps={{ "aria-label": "Search investigations" }}
        />
      </Box>

      <Typography variant="body2" className="study-search__count">
        {results.length} of {studies.length} investigations
      </Typography>

      {error && (
        <Typography variant="body1" className="study-search__message">
          {error}
        </Typography>
      )}

      {/* Altura mínima fixa: com poucos resultados a página não encolhe de repente. */}
      <Box
        component={"div"}
        className="study-search__grid"
        sx={{
          minHeight: { xs: "60vh", md: "75vh" },
          alignContent: "start",
          overflowAnchor: "none",
        }}
      >
        {!error && studies.length > 0 && results.length === 0 && (
          <Typography variant="body1" className="study-search__message" sx={{ gridColumn: "1 / -1" }}>
            No investigations found for “{deferredQuery}”.
          </Typography>
        )}

        {results.map((s) => (
          <StudyCard
            key={s.id}
            study={s}
            chartCount={chartIndex[s.id]?.length ?? 0}
            onSelect={setSelected}
          />
        ))}
      </Box>

      <StudyDialog study={selected} onClose={() => setSelected(null)} />
    </Box>
  );
};