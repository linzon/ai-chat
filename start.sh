#!/bin/bash
# install dependencies
cd./ai-chat-ui && npminstall
cd- && cd./backend-server && pipinstall-rrequirements.txt


# start ui
cd- && cd./ai-chat-ui && npmrundev


# start server
cd- && cd./backend-server && python-muvicornapi.main:app--host0.0.0.0--port8000