# Fact-Check Agent

A web app that reads a PDF, extracts verifiable claims, cross-references them against live web data, and flags each claim as **Verified**, **Inaccurate**, or **False**.

## Live Demo

> https://fact-agent.streamlit.app/

## How It Works

```
PDF Upload → Extract Text (pdfplumber)
          → Extract Claims (Groq / Llama 3.1 8B)
          → Web Search each claim (DuckDuckGo)
          → Verify claim vs. search results (Groq / Llama 3.1 8B)
          → Display Verified / Inaccurate / False with correct facts
```

## Free Stack

| Component   | Tool                                                    | Cost         |
| ----------- | ------------------------------------------------------- | ------------ |
| LLM         | [Groq](https://console.groq.com) (Llama 3.1 8B Instant) | Free         |
| Web Search  | DuckDuckGo (`duckduckgo-search`)                        | Free, no key |
| PDF Parsing | `pdfplumber`                                            | Free         |
| Frontend    | Streamlit                                               | Free         |
| Hosting     | Streamlit Cloud                                         | Free         |

## Local Setup

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd fact-check-agent

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
export GROQ_API_KEY=your_key
streamlit run app.py
```

## Deploy to Streamlit Cloud (Free)

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and click **New app**.
3. Select your repo → `app.py` as the entry point.
4. Under **Advanced settings → Secrets**, add:
   ```toml
   GROQ_API_KEY = "gsk_your_key_here"
   ```
5. Click **Deploy**

Free tier limits: 14,400 requests/day, 30 requests/minute.
