import './main.scss';
import { Box } from '@mui/material';
import { MainHome } from '../MainHome/MainHome';

export const Main = () => {
    return(
        <Box component={"div"} className='main-root'>
            <MainHome/>
        </Box>
    )
}