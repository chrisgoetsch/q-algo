// File: server.js
// Q-ALGO Dashboard Express API Server

const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const bodyParser = require('body-parser');
const qalgoRoutes = require('./backend/routes/qalgoRoutes');

const app = express();
const PORT = process.env.PORT || 4000;

app.use(cors());
app.use(bodyParser.json());
app.use(qalgoRoutes);

app.get('/', (_, res) => {
  res.send('Q-ALGO API running');
});

// Ensure log dirs exist
fs.mkdirSync(path.resolve('logs'), { recursive: true });
fs.mkdirSync(path.resolve('assistants'), { recursive: true });

app.listen(PORT, () => {
  console.log(`🚀 Q-ALGO API server running on http://localhost:${PORT}`);
});
