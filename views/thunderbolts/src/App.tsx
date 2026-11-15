import { useState } from 'react'
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/inter/700.css";
import "@fontsource/jetbrains-mono/400.css";
import "@fontsource/jetbrains-mono/500.css";
import "@fontsource/jetbrains-mono/600.css";
import "@fontsource/jetbrains-mono/700.css";
import { Box} from '@mui/material';
import './abstract/_root.scss';
import './app.scss';
import { Header } from './components/header/Header';
import { Main } from './components/main/Main';

function App() {
  const [count, setCount] = useState(0)

  return (
      <Box component={"div"} className='app'>
        <Header/>
        <Main/>
      </Box>
  )
}

export default App
