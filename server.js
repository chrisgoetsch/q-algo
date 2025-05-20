const express = require('express')
const path = require('path')
const app = express()
const port = 3000

// ✅ Serves /api/qthink_dialogs.jsonl from ./logs/
app.use('/api', express.static(path.join(__dirname, 'logs')))

app.listen(port, () => {
  console.log(`📡 Backend running at http://localhost:${port}`)
})
