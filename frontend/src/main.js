import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Logs from "./pages/Logs";
import "./index.css";
function App() {
    return (_jsxs(BrowserRouter, { children: [_jsxs("nav", { className: "flex justify-between p-4 bg-zinc-900 text-white", children: [_jsxs("div", { className: "space-x-4", children: [_jsx(Link, { to: "/", className: "hover:underline", children: "Dashboard" }), _jsx(Link, { to: "/logs", className: "hover:underline", children: "Logs" })] }), _jsx("div", { className: "text-zinc-500 text-sm", children: "Q-ALGO v2" })] }), _jsxs(Routes, { children: [_jsx(Route, { path: "/", element: _jsx(Dashboard, {}) }), _jsx(Route, { path: "/logs", element: _jsx(Logs, {}) })] })] }));
}
ReactDOM.createRoot(document.getElementById("root")).render(_jsx(React.StrictMode, { children: _jsx(App, {}) }));
