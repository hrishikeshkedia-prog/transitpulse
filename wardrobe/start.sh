#!/bin/bash
# Start the wardrobe app (server serves the built client)
cd "$(dirname "$0")/server"
echo "Starting wardrobe server on http://localhost:3800"
node index.js
