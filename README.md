# ✨ AI Local Chat Bot

- Founder: [Abdullah Khawer - LinkedIn](https://www.linkedin.com/in/abdullah-khawer)

# Introduction

AI Local Chat Bot is an AI-powered chat assistant like ChatGPT running locally, safely and privately using n8n for workflow orchestration, Qdrant for vector storage, and Ollama for running local LLMs. It also includes helper scripts for downloading and processing Confluence pages as PDFs.

Purpose: To ingest it with your private data in `.PDF` format (for now) and then use it to ask questions and get answered like any AI chat bot.

## Features

- **n8n**: Orchestrates chat and data ingestion workflows (http://localhost:5678)
- **Qdrant**: Vector database for storing document embeddings (http://localhost:6333)
- **Ollama**: Local LLM inference (http://localhost:11434)
- **Confluence PDF Downloader**: Download all pages from a Confluence space as PDFs for ingestion

### Demo

![Demo](demos/ai-local-chat-bot.gif)

## System Requirements

| Resource   | Minimum                | Recommended            | Best/Production         |
|------------|------------------------|------------------------|-------------------------|
| CPU        | 2 cores                | 4+ cores               | 8+ cores (modern x86_64)|
| Memory     | 4 GB                   | 8 GB                   | 16+ GB                  |
| Disk Space | 10 GB (free)           | 30 GB (free)           | 100+ GB SSD/NVMe        |

**Notes:**

- Running large LLMs with Ollama may require more memory and CPU for optimal performance.
- SSD/NVMe storage is highly recommended for best performance, especially for vector DB and model files.
- For production, consider dedicated resources and regular backups for Qdrant data.

## Official Documentation

### n8n

- [n8n Documentation](https://docs.n8n.io/)
- [n8n Community](https://community.n8n.io/)
- [n8n Foundational Template](https://n8n.io/workflows/5148-local-chatbot-with-retrieval-augmented-generation-rag/)

### Qdrant

- [Qdrant Documentation](https://qdrant.tech/documentation/)

### Ollama

- [Ollama Documentation](https://ollama.com/library)

### Confluence PDF Downloader

- See `helper-scripts/confluence_pdf_downloader.py` for script usage and configuration details (also documented below in this README).

## Quick Start

1. **Start the stack:**
	```bash
	./start.sh
	```

2. **Access n8n UI:**
	- Open [http://localhost:5678](http://localhost:5678) in your browser.
	- Sign up for the first time.

3. **n8n Workflows:**
	- The workflow in `n8n-workflows/ai-chat-assistant.json` handles PDF ingestion and chat bot. Import it via UI to make use of it.

4. **Download Confluence PDFs (optional):**
	```bash
	cd helper-scripts
    pip install -r requirements.txt
	python confluence_pdf_downloader.py
	```
	Follow the prompts or set these environment variables:
	- `CONFLUENCE_URL`
	- `CONFLUENCE_USERNAME`
	- `CONFLUENCE_API_TOKEN`
	- `CONFLUENCE_SPACE_KEY`

	PDFs will be saved in `helper-scripts/data/confluence_<SPACE_KEY>/`.

5. **Data Ingestion:**
	- Upload PDFs via the n8n form trigger from the n8n UI appeared after workflow import.

6. **Ask:**
	- Ask your question to the chat bot and wait for the answer.

## Requirements

- Docker & Docker Compose
- Python 3.8+
- For helper scripts: `pip install -r helper-scripts/requirements.txt`

## Helper Scripts

### Confluence PDF Downloader

Script: `helper-scripts/confluence_pdf_downloader.py`

Downloads all pages from a Confluence space as PDFs. Uses the Confluence REST API and can convert HTML to PDF if direct export is unavailable.

#### Usage

```bash
cd helper-scripts
python3 confluence_pdf_downloader.py
```

You will be prompted for credentials or can set them as environment variables.

## Project Structure

- `docker-compose.yml` — Service definitions for n8n, Qdrant, Ollama
- `n8n-workflows/` — n8n workflow JSON files
- `helper-scripts/` — Python scripts and requirements for data ingestion
- `start.sh` — Launches the stack and sets up helper scripts

## AI Models

The following models are required and will be pulled automatically by the start script:
- `llama3.2` (for chat)
- `mxbai-embed-large` (for embeddings)

## Stopping and Logs

To stop the application:
```bash
docker-compose down
```

To view logs for all services:
```bash
docker-compose logs -f
```

# 🤝 Contributing

Contributions are welcome!

To contribute:

- Fork this repository and create a new branch for your feature or fix.
- Make your changes and ensure code quality and documentation are updated.
- Submit a pull request with a clear explanation of your changes.

For major changes, please open an issue first to discuss what you would like to change.

# 📝 License

This project is licensed under the Apache License - see the [LICENSE](LICENSE) file for details.

---

###### 😊 Any contributions, improvements and suggestions will be highly appreciated.

###### 🌟 Star this repository to know about the latest updates.
