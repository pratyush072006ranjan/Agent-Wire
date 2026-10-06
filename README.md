# Agent Wire — Autonomous Research Desk

A multi-agent research pipeline that takes a topic, searches the web, reads the
most relevant source in depth, drafts a structured report, and critiques its
own work — all wrapped in a newsroom-styled Streamlit UI.

```
Search Agent → Reader Agent → Writer Chain → Critic Chain
```

## How it works

| Stage | Component | What it does |
|---|---|---|
| 1. Search | `build_search_agent()` (LangChain agent + `web_search` tool) | Queries Tavily for recent, reliable sources on the topic. |
| 2. Read | `build_reader_agent()` (LangChain agent + `scrape_url` tool) | Picks the most relevant URL from the search results and scrapes its full text. Falls back to other search-result URLs automatically if the first scrape fails (e.g. a 404). |
| 3. Write | `writer_chain` | Synthesizes the search + scraped research into a structured report (Introduction, Key Findings, Conclusion, Sources). |
| 4. Critique | `critic_chain` | Scores the report out of 10 and lists strengths, areas to improve, and a one-line verdict. |

All four stages are orchestrated by `run_research_pipeline()` in `pipeline.py`,
which `app.py` calls to drive a live-updating UI.

## Project structure

```
project/
├── .venv/              # virtual environment (not committed)
├── .env                # API keys (not committed)
├── app.py              # Streamlit UI
├── agents.py           # Agent + chain definitions (search, reader, writer, critic)
├── pipeline.py         # Orchestrates the 4-stage pipeline end to end
├── tools.py             # web_search and scrape_url tools used by the agents
├── requirements.txt     # Python dependencies
└── README.md
```

## Setup

### 1. Clone and create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API keys

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_google_generative_ai_key
TAVILY_API_KEY=your_tavily_api_key
```

- **Google API key** — powers the Gemini model (`gemini-3.1-flash-lite-preview`) used by all agents and chains. Get one from [Google AI Studio](https://aistudio.google.com/).
- **Tavily API key** — powers the `web_search` tool. Get one from [tavily.com](https://tavily.com/).

## Running it

### Streamlit UI (recommended)

```bash
streamlit run app.py
```

Opens a browser dashboard where you enter a topic, watch the four-stage
pipeline run live, and get back a formatted report with a critic scorecard.

### Command line

```bash
python pipeline.py
```

Prompts for a topic in the terminal and prints each stage's output as it runs.

## Notes on reliability

- `scrape_url` raises on non-2xx HTTP responses (e.g. 404s) so failed scrapes
  are always detected rather than silently returning a broken page's HTML as
  if it were content.
- `pipeline.py` reads URLs from the **raw tool output** of the search step
  (not the agent's paraphrased summary), so real source links reliably reach
  the writer chain instead of being dropped during summarization.
- If the reader agent's first chosen URL fails to scrape, the pipeline
  automatically retries the other URLs returned by the search step before
  giving up.

## Customization

- **Model**: change `model="gemini-3.1-flash-lite-preview"` in `agents.py` to
  use a different Gemini model.
- **Number of search results**: adjust `max_results=5` in `tools.py`'s
  `web_search`.
- **Report structure**: edit `writer_prompt` in `agents.py`.
- **Critic scoring format**: edit `critic_prompt` in `agents.py` — the UI's
  scorecard parses the `Score: X/10`, `Strengths:`, `Areas to Improve:`, and
  `One line verdict:` sections, so keep that structure if you want the
  gauge/columns in `app.py` to keep working.
