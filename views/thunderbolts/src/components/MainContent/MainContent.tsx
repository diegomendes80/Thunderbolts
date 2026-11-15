import "./MainContent.scss";
import { Box, Typography } from "@mui/material";
import { SimpleLineChart } from "../UI/LineChart/SimpleLineChart/SimpleLineChart";
import { SimpleAreaChart } from "../UI/AreaChart/SimpleAreaChart/SimpleAreaChart";
import { GradientAreaChart } from "../UI/AreaChart/GradientAreaChart/GradientAreaChart";
import { SimpleBarChart } from "../UI/BarChart/SimpleBarChart/SimpleBarChart";
import { StackedBarChart } from "../UI/BarChart/StackedBarChart/StackedBarChart";

export const MainContent = () => {
  const graphics = [
    { name: "Simple Line Chart", graphic: <SimpleLineChart /> },
    { name: "Simple Area Chart", graphic: <SimpleAreaChart /> },
    { name: "Gradient Area Chart", graphic: <GradientAreaChart /> },
    { name: "Simple Bar Chart", graphic: <SimpleBarChart /> },
    { name: "Stacked Bar Chart", graphic: <StackedBarChart /> },
    {name: ""}
  ];

  return (
    <Box component={"div"} className="main-content-root">
      <Typography variant="h3" className="main-content__title">
        Teste de gráficos
      </Typography>
      <Box component={"div"} className="simple-line-chart grafico-container">
        {graphics.map((g, i) => {
          return (
            <Box component={"div"} className="grafico" key={i}>
              <Typography variant="h3" className="title">
                {g.name}
              </Typography>
              {g.graphic}
            </Box>
          );
        })}
      </Box>
    </Box>
  );
};
