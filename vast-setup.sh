#!/usr/bin/env bash
set -euo pipefail

# Install Ollama. Containers usually lack systemd, so start the server ourselves.
curl -fsSL https://ollama.com/install.sh | sh
nohup ollama serve > /var/log/ollama.log 2>&1 &

# Wait until the server answers.
until curl -s http://localhost:11434/api/tags > /dev/null; do sleep 2; done

# The 9B decision models to compare.
ollama pull clef-flash
ollama pull nimble

echo "Ready. Ollama is listening on localhost:11434 inside the instance."