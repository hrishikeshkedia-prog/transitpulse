#!/bin/bash
# Dev mode: Vite dev server (port 5173) + Express API (port 3800)
cd "$(dirname "$0")/server" && node index.js &
SERVER_PID=$!
cd "$(dirname "$0")/client" && npm run dev
kill $SERVER_PID 2>/dev/null
