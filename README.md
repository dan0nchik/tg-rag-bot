# tg-rag-bot
 
[![Deploy to Server](https://github.com/dan0nchik/tg-rag-bot/actions/workflows/deploy.yml/badge.svg)](https://github.com/dan0nchik/tg-rag-bot/actions/workflows/deploy.yml)

Self-hosted Telegram chat bot based on RAG for friend's group chat. 

## Features

- Self-hosted with Docker
- Long term memory: RAG with QDrant as vector database. Allows bot to remember facts about chat members and previous messages
- Short-term memory: sliding window of N last messages in the chat
- Can look up facts in the Internet using DuckDuckGo
- More LlamaIndex agentic capabilities are coming soon!
