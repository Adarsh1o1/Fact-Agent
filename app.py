import streamlit as st
import pdfplumber
import json
import os
import time
import io
from groq import Groq
from duckduckgo_search import DDGS

st.set_page_config(
    page_title="Fact-Check Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .verdict-verified  { background:#d4edda; border-left:4px solid #28a745; padding:8px 12px; border-radius:4px; }
    .verdict-inaccurate{ background:#fff3cd; border-left:4px solid #ffc107; padding:8px 12px; border-radius:4px; }
    .verdict-false     { background:#f8d7da; border-left:4px solid #dc3545; padding:8px 12px; border-radius:4px; }
    .claim-text { font-size:0.95rem; font-weight:500; margin-bottom:6px; }
</style>
""", unsafe_allow_html=True)


# ── Groq client ──────────────────────────────────────────────────────────────
def get_client(api_key: str) -> Groq:
    return Groq(api_key=api_key)


# ── PDF ───────────────────────────────────────────────────────────────────────
def extract_pdf_text(uploaded_file) -> str:
    text_parts = []
    with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n\n".join(text_parts)


# ── LLM: extract claims ───────────────────────────────────────────────────────
EXTRACT_PROMPT = """You are a professional fact-checker. Read the following text and extract all specific, verifiable claims.

Focus ONLY on claims that contain concrete, checkable data:
- Statistics and percentages (e.g., "X% of users…")
- Numerical figures (revenue, user counts, growth rates)
- Specific dates or years for events
- Named rankings or positions ("the largest", "first to…")
- Technical specifications or version numbers

Rules:
- Extract up to 12 of the most important checkable claims.
- Ignore vague statements like "AI is growing fast."
- Each claim must quote the exact figure or fact from the text.

Return ONLY a valid JSON array. No markdown, no explanation.
Format:
[
  {
    "claim": "exact claim text with the specific figure",
    "category": "statistic | date | financial | technical | ranking",
    "search_query": "concise web search query to verify this claim"
  }
]

TEXT:
{text}"""

def extract_claims(client: Groq, text: str) -> list[dict]:
    prompt = EXTRACT_PROMPT.format(text=text[:5000])
    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=2000,
    )
    raw = resp.choices[0].message.content.strip()
    raw = raw.split("```json")[-1].split("```")[0].strip() if "```" in raw else raw
    return json.loads(raw)


# ── Web search ────────────────────────────────────────────────────────────────
def web_search(query: str, max_results: int = 5) -> list[dict]:
    try:
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max_results))
    except Exception:
        return []


# ── LLM: verify claim ─────────────────────────────────────────────────────────
VERIFY_PROMPT = """You are a rigorous fact-checker. Verify the claim below using ONLY the provided web search results.

CLAIM: "{claim}"

SEARCH RESULTS:
{search_results}

Verdict rules:
- "Verified"   → current web data confirms the claim is accurate.
- "Inaccurate" → the claim was once true but the figure is now outdated, OR the number is slightly wrong.
- "False"      → the claim contradicts current evidence, OR no credible evidence supports it.

Return ONLY a valid JSON object. No markdown, no explanation outside the JSON.
{{
  "verdict": "Verified | Inaccurate | False",
  "confidence": "High | Medium | Low",
  "explanation": "1-2 sentence explanation citing evidence",
  "correct_fact": "The accurate current fact (only if Inaccurate or False, else null)",
  "source_url": "Most relevant URL from results, or null"
}}"""

def verify_claim(client: Groq, claim: dict, search_results: list[dict]) -> dict:
    search_text = "\n\n".join(
        f"Title: {r.get('title','')}\nURL: {r.get('href','')}\nSnippet: {r.get('body','')}"
        for r in search_results
    )
    prompt = VERIFY_PROMPT.format(
        claim=claim["claim"],
        search_results=search_text[:3500],
    )
    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=600,
    )
    raw = resp.choices[0].message.content.strip()
    raw = raw.split("```json")[-1].split("```")[0].strip() if "```" in raw else raw
    return json.loads(raw)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuration")

    # Try Streamlit secrets first (for deployed app), then manual input
    default_key = st.secrets.get("GROQ_API_KEY", "") if hasattr(st, "secrets") else ""
    api_key = st.text_input(
        "Groq API Key",
        value=default_key,
        type="password",
        help="Free key at console.groq.com — no credit card required",
    )

    st.markdown("---")
    st.markdown("**How it works**")
    st.markdown("1. Upload any PDF")
    st.markdown("2. AI extracts all verifiable claims")
    st.markdown("3. Each claim is searched on the web")
    st.markdown("4. AI flags: ✅ Verified / ⚠️ Inaccurate / ❌ False")
    st.markdown("---")
    st.markdown("**Free stack**")
    st.markdown("- LLM: Groq (Llama 3.1 8B)")
    st.markdown("- Search: DuckDuckGo")
    st.markdown("- Deploy: Streamlit Cloud")


# ── Main UI ───────────────────────────────────────────────────────────────────
st.title("🔍 Fact-Check Agent")
st.markdown(
    "Upload a PDF and the agent will **extract claims**, **search the web**, "
    "and **flag inaccuracies** automatically."
)

uploaded_file = st.file_uploader("Upload PDF", type=["pdf"], label_visibility="collapsed")

if uploaded_file:
    if not api_key:
        st.warning("Enter your Groq API key in the sidebar to continue.")
        st.stop()

    if st.button("🚀 Run Fact-Check", type="primary", use_container_width=True):
        client = get_client(api_key)

        # ── Step 1: Extract text ──────────────────────────────────────────────
        with st.spinner("📄 Extracting text from PDF…"):
            try:
                pdf_text = extract_pdf_text(uploaded_file)
            except Exception as e:
                st.error(f"Failed to read PDF: {e}")
                st.stop()

        if not pdf_text.strip():
            st.error("No readable text found in this PDF (it may be image-based).")
            st.stop()

        with st.expander("📝 Extracted PDF text (preview)", expanded=False):
            st.text(pdf_text[:1500] + ("…" if len(pdf_text) > 1500 else ""))

        # ── Step 2: Extract claims ────────────────────────────────────────────
        with st.spinner("🤖 Identifying verifiable claims…"):
            try:
                claims = extract_claims(client, pdf_text)
            except Exception as e:
                st.error(f"Claim extraction failed: {e}")
                st.stop()

        st.info(f"Found **{len(claims)}** verifiable claims. Starting web verification…")

        # ── Step 3: Verify each claim ─────────────────────────────────────────
        results = []
        progress = st.progress(0, text="Verifying claims…")

        for i, claim in enumerate(claims):
            progress.progress((i) / len(claims), text=f"Checking claim {i+1}/{len(claims)}…")
            search_hits = web_search(claim.get("search_query", claim["claim"]))
            time.sleep(0.4)  # avoid DuckDuckGo rate-limiting

            try:
                verdict_data = verify_claim(client, claim, search_hits)
            except Exception:
                verdict_data = {
                    "verdict": "False",
                    "confidence": "Low",
                    "explanation": "Could not retrieve or parse verification result.",
                    "correct_fact": None,
                    "source_url": None,
                }

            results.append({**claim, **verdict_data})

        progress.progress(1.0, text="Done!")

        # ── Step 4: Display results ───────────────────────────────────────────
        st.markdown("---")
        st.subheader("📊 Results")

        verified   = [r for r in results if r["verdict"] == "Verified"]
        inaccurate = [r for r in results if r["verdict"] == "Inaccurate"]
        false_list = [r for r in results if r["verdict"] == "False"]

        c1, c2, c3 = st.columns(3)
        c1.metric("✅ Verified",    len(verified))
        c2.metric("⚠️ Inaccurate", len(inaccurate))
        c3.metric("❌ False",       len(false_list))

        st.markdown("---")

        ICONS    = {"Verified": "✅", "Inaccurate": "⚠️", "False": "❌"}
        CSS_KEYS = {"Verified": "verified", "Inaccurate": "inaccurate", "False": "false"}

        for r in results:
            verdict = r.get("verdict", "False")
            icon    = ICONS.get(verdict, "❓")
            css     = CSS_KEYS.get(verdict, "false")
            label   = f"{icon} [{verdict}] {r['claim'][:90]}{'…' if len(r['claim']) > 90 else ''}"

            with st.expander(label, expanded=(verdict != "Verified")):
                st.markdown(
                    f'<div class="verdict-{css}">'
                    f'<span class="claim-text">"{r["claim"]}"</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                col_a, col_b = st.columns([1, 2])
                col_a.markdown(f"**Category:** `{r.get('category','—')}`")
                col_a.markdown(f"**Confidence:** `{r.get('confidence','—')}`")
                col_b.markdown(f"**Explanation:** {r.get('explanation','—')}")

                if r.get("correct_fact"):
                    st.success(f"**Correct fact:** {r['correct_fact']}")
                if r.get("source_url"):
                    st.markdown(f"**Source:** {r['source_url']}")

        # ── Download JSON report ──────────────────────────────────────────────
        st.markdown("---")
        report_json = json.dumps(results, indent=2)
        st.download_button(
            label="⬇️ Download full report (JSON)",
            data=report_json,
            file_name="fact_check_report.json",
            mime="application/json",
        )
