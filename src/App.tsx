import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { AuthProvider, ProtectedRoute } from "@/auth/AuthContext";
import Home from "@/pages/Home";
import History from "@/pages/History";
import Analysis from "@/pages/Analysis";
import Alerts from "@/pages/Alerts";
import Login from "@/pages/Login";
import AdminSources from "@/pages/AdminSources";

export default function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/history" element={<History />} />
          <Route path="/analysis" element={<Analysis />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/login" element={<Login />} />
          <Route
            path="/admin/sources"
            element={
              <ProtectedRoute roles={["admin", "ops"]}>
                <AdminSources />
              </ProtectedRoute>
            }
          />
        </Routes>
      </Router>
    </AuthProvider>
  );
}
