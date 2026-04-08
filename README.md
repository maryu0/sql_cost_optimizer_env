---
title: SQL Cost Optimizer Environment
emoji: 💎
colorFrom: blue
colorTo: yellow
sdk: docker
sdk_version: "latest"
app_file: src/main.py
pinned: false
---

# 💎 SQL Cost Optimizer Environment

### *Teaching AI Agents to Think Like Database Experts*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenEnv](https://img.shields.io/badge/OpenEnv-Compliant-00d4aa?style=for-the-badge&logo=checkmarx)](https://github.com/openenv/openenv)
[![Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-FFD21E?style=for-the-badge)](https://huggingface.co/spaces)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker)](https://www.docker.com/)

**🏆 Meta OpenEnv Hackathon 2026 Submission**

## 📋 Overview

The **SQL Cost Optimizer Environment** is a reinforcement learning environment designed to teach AI agents how to optimize database queries through three progressive challenges:

1. **Index Advisor** (Easy): Suggest indexes for slow queries
2. **Query Rewriter** (Medium): Rewrite inefficient queries using JOINs
3. **Schema Normalizer** (Hard): Normalize denormalized schemas

## 🎯 Key Features

- ✅ **Real-world SQL optimization tasks** with objective grading
- ✅ **Three difficulty levels** for progressive learning
- ✅ **RESTful API** with /reset, /step, /state, /health endpoints
- ✅ **OpenEnv compliant** environment specification
- ✅ **Docker-ready** for Hugging Face Spaces deployment

## 🚀 Quick Start

### API Endpoints

- `POST /reset` — Initialize environment with optional task selection
- `POST /step` — Execute action and receive observation, reward, done status
- `GET /state` — Retrieve current environment state
- `GET /health` — Health check endpoint
- `GET /tasks` — List all available tasks

### Example Usage

```python
import requests

# Reset environment
response = requests.post("https://maryu0-my-env.hf.space/reset", 
    json={"task_name": "index-advisor"})
observation = response.json()["observation"]

# Execute action
response = requests.post("https://maryu0-my-env.hf.space/step",
    json={"action": {"optimized_query": "CREATE INDEX...", ...}})
```

## 📚 Documentation

See [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) for detailed implementation notes.

## 📄 License

MIT License - See LICENSE file for details
