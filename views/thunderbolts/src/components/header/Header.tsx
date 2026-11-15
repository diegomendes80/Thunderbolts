import "./header.scss";
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
} from "@mui/material";
import logo from "../../assets/flamescope-logo-transparente.png";

export const Header = () => {
  const links = [
    { label: "The story", href: "#story" },
    { label: "The science", href: "#science" },
    { label: "Sources ↗", href: "https://psi.nasa.gov", external: true },
  ];

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
          href="https://psi.nasa.gov"
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
