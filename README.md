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

### _Teaching AI Agents to Think Like Database Experts_

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

## 🏗️ Environment Specification

### Observation Space

Each observation includes:

- `task_type`: Current task (index-advisor, query-rewriter, schema-normalizer)
- `query`: Original SQL query to optimize
- `database_schema`: CREATE TABLE statements defining the schema
- `current_execution_time_ms`: Baseline execution time in milliseconds
- `explain_plan`: EXPLAIN QUERY PLAN output from SQLite
- `sample_data_preview`: Sample rows from relevant tables
- `hint`: Optional optimization hint
- `metadata`: Additional context (row counts, index info, costs)

### Action Space

Each action must include:

- `optimized_query`: The optimized SQL (CREATE INDEX, rewritten query, or schema DDL)
- `explanation`: Human-readable explanation of optimization strategy
- `suggested_changes`: List of specific changes made
- `confidence`: Agent's confidence in this optimization (0.0-1.0)

### Reward Signal

- **Grade Score**: Objective evaluation of optimization quality
- **Performance Bonus**: Extra reward for significant speedups (1.5x+)
- **Cost Reduction**: Reward for lower estimated cloud compute costs
- **Correctness Penalty**: Severe penalty if results don't match original query

## 🛠️ Setup Instructions

### Local Setup

```bash
# Clone the repository
git clone https://huggingface.co/spaces/maryu0/my-env
cd sql-cost-optimizer-env

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run baseline inference
python inference.py

# Or start the API server
python -m src.main
```

### Environment Variables

Set these in a `.env` file:

```
OPENAI_API_KEY=your-key-here
MODEL_NAME=gpt-4o-mini
API_BASE_URL=https://api.openai.com/v1
```

## 📄 License

MIT License - See LICENSE file for details
