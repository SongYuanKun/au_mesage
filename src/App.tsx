import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "@/pages/Home";
import History from "@/pages/History";
import Analysis from "@/pages/Analysis";
import Alerts from "@/pages/Alerts";

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/history" element={<History />} />
        <Route path="/analysis" element={<Analysis />} />
        <Route path="/alerts" element={<Alerts />} />
      </Routes>
    </Router>
  );
}
