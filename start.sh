#!/bin/bash
# install dependencies
cd ./ai-chat-ui && npm install
cd - && cd ./backend-server && pip install-rrequirements.txt


# start ui
cd - && cd ./ai-chat-ui && npm run dev


# start server
cd - && cd ./backend-server && python -m uvicorn api.main:app --host 0.0.0.0 --port 8000