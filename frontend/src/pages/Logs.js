import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/Card";
export default function Logs() {
    const [tradeLogs, setTradeLogs] = useState([]);
    useEffect(() => {
        const fetchLogs = async () => {
            try {
                const response = await fetch("/logs/trade_flow/trades.jsonl");
                const text = await response.text();
                const lines = text.trim().split("\n");
                const parsed = lines.map((line) => JSON.parse(line));
                setTradeLogs(parsed.reverse()); // show most recent first
            }
            catch (error) {
                console.error("Failed to load trade logs:", error);
            }
        };
        fetchLogs();
        const interval = setInterval(fetchLogs, 5000);
        return () => clearInterval(interval);
    }, []);
    return (_jsxs("div", { className: "p-6 space-y-4", children: [_jsx("h1", { className: "text-2xl font-bold", children: "Trade Flow Log" }), tradeLogs.length === 0 ? (_jsx("p", { className: "text-zinc-400", children: "No trade logs found." })) : (tradeLogs.map((log, idx) => (_jsx(Card, { children: _jsx(CardContent, { className: "p-4 text-white bg-zinc-900 overflow-x-auto", children: _jsx("pre", { children: JSON.stringify(log, null, 2) }) }) }, idx))))] }));
}
