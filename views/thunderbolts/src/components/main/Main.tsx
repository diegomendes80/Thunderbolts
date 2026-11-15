import './main.scss';
import { Box } from '@mui/material';
import { MainHome } from '../MainHome/MainHome';
import { MainContent } from '../MainContent/MainContent';

export const Main = () => {
    return(
        <Box component={"div"} className='main-root'>
            <MainHome/>
            <MainContent/>
        </Box>
    )
}