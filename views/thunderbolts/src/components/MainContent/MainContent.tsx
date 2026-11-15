import "./MainContent.scss";
import { Box } from "@mui/material";
import { StudySearch } from "../StudySearch/StudySearch";

export const MainContent = () => {
  return (
    <Box component={"div"} className="main-content-root">
      <StudySearch />
    </Box>
  );
};