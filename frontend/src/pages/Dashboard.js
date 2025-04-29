import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/Card";
import { Switch } from "@/components/ui/Switch";
import { Slider } from "@/components/ui/Slider";
export default function Dashboard() {
    const [killSwitch, setKillSwitch] = useState(false);
    const [capitalAllocation, setCapitalAllocation] = useState(0.2);
    const [runtimeState, setRuntimeState] = useState({});
    const [openTrades, setOpenTrades] = useState([]);
    useEffect(() => {
        const interval = setInterval(() => {
            fetch("/logs/status.json")
                .then((res) => res.json())
                .then((data) => {
                setKillSwitch(data.kill_switch);
                setCapitalAllocation(data.capital_allocation);
            });
            fetch("/logs/runtime_state.json")
                .then((res) => res.json())
                .then((data) => setRuntimeState(data));
            fetch("/logs/open_trades.jsonl")
                .then((res) => res.text())
                .then((text) => {
                const lines = text.trim().split("\n");
                const trades = lines.map((line) => JSON.parse(line));
                setOpenTrades(trades);
            });
        }, 3000);
        return () => clearInterval(interval);
    }, []);
    const handleKillSwitchToggle = async () => {
        const newStatus = !killSwitch;
        setKillSwitch(newStatus);
        await fetch("/logs/status.json", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ kill_switch: newStatus, capital_allocation: capitalAllocation }),
        });
    };
    const handleCapitalChange = async (val) => {
        const allocation = val[0] / 100;
        setCapitalAllocation(allocation);
        await fetch("/logs/status.json", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ kill_switch: killSwitch, capital_allocation: allocation }),
        });
    };
    return (_jsxs("div", { className: "grid grid-cols-1 gap-6 p-4 md:grid-cols-2 lg:grid-cols-3", children: [_jsx(Card, { children: _jsxs(CardContent, { className: "p-4", children: [_jsx("h2", { className: "text-xl font-bold", children: "Kill Switch" }), _jsx(Switch, { checked: killSwitch, onCheckedChange: handleKillSwitchToggle })] }) }), _jsx(Card, { children: _jsxs(CardContent, { className: "p-4", children: [_jsx("h2", { className: "text-xl font-bold", children: "Capital Allocation" }), _jsx(Slider, { defaultValue: [capitalAllocation * 100], max: 100, step: 1, onValueChange: handleCapitalChange }), _jsxs("p", { children: [(capitalAllocation * 100).toFixed(0), "%"] })] }) }), _jsx(Card, { className: "col-span-2", children: _jsxs(CardContent, { className: "p-4", children: [_jsx("h2", { className: "text-xl font-bold mb-2", children: "Runtime State" }), _jsx("pre", { className: "text-sm bg-black text-white p-2 rounded overflow-x-auto", children: JSON.stringify(runtimeState, null, 2) })] }) }), _jsx(Card, { className: "col-span-3", children: _jsxs(CardContent, { className: "p-4", children: [_jsx("h2", { className: "text-xl font-bold mb-2", children: "Open Trades" }), _jsx("div", { className: "space-y-2 max-h-96 overflow-y-auto", children: openTrades.map((trade, idx) => (_jsx("div", { className: "border p-2 rounded bg-gray-900 text-white", children: _jsx("pre", { children: JSON.stringify(trade, null, 2) }) }, idx))) })] }) })] }));
}
