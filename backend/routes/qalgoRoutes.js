// File: backend/routes/qalgoRoutes.js
// Minimal Express backend for Q-ALGO dashboard endpoints

const express = require('express');
const fs = require('fs');
const path = require('path');
const router = express.Router();

const readJSON = (filePath) => {
  try {
    return JSON.parse(fs.readFileSync(filePath));
  } catch {
    return {};
  }
};

// ✅ /api/models/entry/latest
router.get('/api/models/entry/latest', (req, res) => {
  const file = path.resolve('logs/qthink_score_breakdown.jsonl');
  const lines = fs.existsSync(file) ? fs.readFileSync(file, 'utf-8').trim().split('\n') : [];
  const last = lines.length ? JSON.parse(lines.at(-1)) : {};
  res.json({ ...last, timestamp: new Date().toISOString() });
});

// ✅ /api/mesh/status
router.get('/api/mesh/status', (req, res) => {
  const file = path.resolve('logs/mesh_logger.jsonl');
  const lines = fs.existsSync(file) ? fs.readFileSync(file, 'utf-8').trim().split('\n') : [];
  const last = lines.length ? JSON.parse(lines.at(-1)) : {};
  res.json(last);
});

// ✅ /api/chart/spy
router.get('/api/chart/spy', (req, res) => {
  const file = path.resolve('logs/chart_data.json');
  const data = readJSON(file);
  res.json(data);
});

// ✅ /api/trades/recent
router.get('/api/trades/recent', (req, res) => {
  const file = path.resolve('logs/open_trades.jsonl');
  const lines = fs.existsSync(file) ? fs.readFileSync(file, 'utf-8').trim().split('\n') : [];
  const recent = lines.slice(-10).map((l) => JSON.parse(l));
  res.json(recent);
});

// ✅ /api/status (GET + POST)
router.get('/api/status', (req, res) => {
  res.json(readJSON('logs/status.json'));
});

router.post('/api/status', (req, res) => {
  fs.writeFileSync('logs/status.json', JSON.stringify(req.body, null, 2));
  res.json({ ok: true });
});

// ✅ /api/account/summary
router.get('/api/account/summary', (req, res) => {
  res.json(readJSON('logs/account_summary.json'));
});

// ✅ /api/system/runtime
router.get('/api/system/runtime', (req, res) => {
  res.json(readJSON('logs/runtime_state.json'));
});

// ✅ /api/gpt/reinforcement
router.get('/api/gpt/reinforcement', (req, res) => {
  const file = path.resolve('assistants/reinforcement_profile.json');
  const profile = readJSON(file);
  const formatted = Object.entries(profile)
    .map(([label, count]) => ({ label, count }))
    .sort((a, b) => b.count - a.count);
  res.json(formatted);
});

module.exports = router;
