import { BrowserRouter, Routes, Route } from 'react-router-dom';
import './App.css';
import Landing from './pages/Landing';
import Survey from './pages/Survey';
import Result from './pages/Result';
import Privacy from './pages/Privacy';
import Admin from './pages/Admin';
import Gameplay from './pages/Gameplay';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/survey" element={<Survey />} />
        <Route path="/result" element={<Result />} />
        <Route path="/gameplay" element={<Gameplay />} />
        <Route path="/privacy" element={<Privacy />} />
        <Route path="/admin/*" element={<Admin />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

