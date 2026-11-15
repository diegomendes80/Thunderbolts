import "./mainHome.scss";
import { Box, Typography } from "@mui/material";
import SouthIcon from "@mui/icons-material/South";

export const MainHome = () => {
  return (
    <Box component={"div"} className="main-home-root">
      <Box component={"div"} className="main-home__background"></Box>

      <Box component={"div"} className="main-home__content">
        <Typography variant={"h2"} className="content__subtitle">
          MICROGRAVITY COMBUSTION RESEARCH
        </Typography>
        <Typography variant={"h1"} className="content__title">
          Understanding Fire <span className="highlight">Beyond Earth.</span> 
        </Typography>
        <Typography variant="body1" className="content_text">
          Without gravity, fire follows different rules. A journey through the
          discoveries that are making space exploration safer.
        </Typography>

        <Box component={"div"} className="content__action">
          <Box component={"span"} className="action__down">
            <SouthIcon className="down-icon"/>
          </Box>

          <Typography variant="body1" className="action__explore">Explore the story</Typography>
          <Typography variant="body1" className="action__interval">1967 - TODAY</Typography>

        </Box>
      </Box>
    </Box>
  );
};
