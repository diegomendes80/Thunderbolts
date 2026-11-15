import "./header.scss";
import {
  Box,
  Typography,
  List,
  ListItemButton,
} from "@mui/material";
import logo from "../../assets/flamescope-logo-transparente.png";

export const Header = () => {


  return (
    <Box component={"div"} className="header-root">
      <Box component={"img"} className="header__logo" src={logo}></Box>

      <List component={"nav"} className="header__menu-nav">
        <ListItemButton component="a" href="#story" className="nav-item">
          The story
        </ListItemButton>
        <ListItemButton component="a" href="#science" className="nav-item">
          The science
        </ListItemButton>
        <ListItemButton
          component="a"
          href="https://psi.nasa.gov/physci/repo/search?q=combustion&data_source=psi&data_type=investigation"
          target="_blank"
          rel="noopener noreferrer"
          className="nav-item"
        >
          Sources ↗
        </ListItemButton>
      </List>

      <Box component={"div"} className="header__nasa-display">
        <Box component={"span"} className="display-circle"></Box>
        <Typography variant="body1" className="nasa-display__title">Nasa open science</Typography>
      </Box>
    </Box>
  );
};
