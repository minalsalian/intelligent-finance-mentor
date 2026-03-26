import { BrowserRouter, Routes, Route } from "react-router-dom";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import TradingMentor from "./pages/TradingMentor";
import Layout from "./components/Layout";

function App() {
  return (
    <BrowserRouter>
      <Routes>

        <Route path="/" element={<Login />} />

        <Route element={<Layout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/trading" element={<TradingMentor />} />
        </Route>

      </Routes>
    </BrowserRouter>
  );
}

export default App;
