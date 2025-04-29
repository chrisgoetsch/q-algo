import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Logs from "./pages/Logs";
import "./index.css";

function App() {
  return (
    <BrowserRouter>
      <nav className="flex justify-between p-4 bg-zinc-900 text-white">
        <div className="space-x-4">
          <Link to="/" className="hover:underline">Dashboard</Link>
          <Link to="/logs" className="hover:underline">Logs</Link>
        </div>
        <div className="text-zinc-500 text-sm">Q-ALGO v2</div>
      </nav>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/logs" element={<Logs />} />
      </Routes>
    </BrowserRouter>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
