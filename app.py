import re
import streamlit as st
import pdfplumber
import json
import os
import time
import io
from groq import Groq
from duckduckgo_search import DDGS


# ── SVG helpers (Heroicons 2 outline, MIT licence) ────────────────────────────
def _svg(paths, color="currentColor", size=20, mr=6):
    inner = "".join(
        f'<path stroke-linecap="round" stroke-linejoin="round" d="{d}"/>'
        for d in paths
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" '
        f'stroke-width="1.5" stroke="{color}" width="{size}" height="{size}" '
        f'style="vertical-align:middle;display:inline-block;margin-right:{mr}px">'
        f"{inner}</svg>"
    )

def ic_search(s=24):    return _svg(["m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z"], size=s)
def ic_gear(s=20):      return _svg(["M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z", "M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"], size=s)
def ic_check(s=20):     return _svg(["M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"], "#28a745", s)
def ic_warn(s=20):      return _svg(["M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"], "#ffc107", s)
def ic_xmark(s=20):     return _svg(["m9.75 9.75 4.5 4.5m0-4.5-4.5 4.5M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"], "#dc3545", s)
def ic_doc(s=20):       return _svg(["M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z"], size=s)
def ic_bolt(s=20):      return _svg(["m3.75 13.5 10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75Z"], size=s)
def ic_cpu(s=20):       return _svg(["M8.25 3v1.5M4.5 8.25H3m18 0h-1.5M4.5 12H3m18 0h-1.5m-15 3.75H3m18 0h-1.5M8.25 19.5V21M12 3v1.5m0 15V21m3.75-18v1.5m0 15V21m-9-1.5h10.5a2.25 2.25 0 0 0 2.25-2.25V6.75a2.25 2.25 0 0 0-2.25-2.25H6.75A2.25 2.25 0 0 0 4.5 6.75v10.5a2.25 2.25 0 0 0 2.25 2.25Zm.75-12h9v9h-9v-9Z"], size=s)
def ic_chart(s=20):     return _svg(["M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z"], size=s)
def ic_download(s=20):  return _svg(["M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3"], size=s)
def ic_lock(s=20):      return _svg(["M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z"], size=s)
def ic_globe(s=20):     return _svg(["M12 21a9.004 9.004 0 0 0 8.716-6.747M12 21a9.004 9.004 0 0 1-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 0 1 7.843 4.582M12 3a8.997 8.997 0 0 0-7.843 4.582m15.686 0A11.953 11.953 0 0 1 12 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0 1 21 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0 1 12 16.5a17.92 17.92 0 0 1-8.716-2.247m0 0A9.015 9.015 0 0 1 3 12c0-1.605.42-3.113 1.157-4.418"], size=s)
def ic_upload(s=20):    return _svg(["M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5"], size=s)
def ic_stack(s=20):     return _svg(["M6.429 9.75 2.25 12l4.179 2.25m0-4.5 5.571 3 5.571-3m-11.142 0L2.25 7.5 12 2.25l9.75 5.25-4.179 2.25m0 0L21.75 12l-4.179 2.25m0 0 4.179 2.25L12 21.75 2.25 16.5l4.179-2.25m11.142 0-5.571 3-5.571-3"], size=s)


st.set_page_config(
    page_title="Fact-Check Agent",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .verdict-verified   { background:#d4edda; border-left:4px solid #28a745; padding:8px 12px; border-radius:4px; }
    .verdict-inaccurate { background:#fff3cd; border-left:4px solid #ffc107; padding:8px 12px; border-radius:4px; }
    .verdict-false      { background:#e77781; border-left:4px solid #dc3545; padding:8px 12px; border-radius:4px; }
    .claim-text { font-size:0.95rem; font-weight:500; margin-bottom:6px; }
    .metric-card {
        border: 1px solid #e0e0e0; border-radius:8px; padding:16px 20px;
        display:flex; align-items:center; gap:12px;
    }
    .metric-num { font-size:2rem; font-weight:700; line-height:1; }
    .metric-lbl { font-size:0.85rem; color:#666; margin-top:2px; }
    .sidebar-row { display:flex; align-items:center; gap:8px; margin:6px 0; font-size:0.9rem; }
    .icon-title  { display:flex; align-items:center; gap:10px; }
    .api-badge   {
        display:flex; align-items:center; gap:6px;
        background:#d4edda; border:1px solid #28a745; border-radius:6px;
        padding:6px 10px; font-size:0.85rem; color:#155724;
    }
</style>
""", unsafe_allow_html=True)


# ── Groq client ───────────────────────────────────────────────────────────────
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
- Statistics and percentages (e.g., "X% of users...")
- Numerical figures (revenue, user counts, growth rates)
- Specific dates or years for events
- Named rankings or positions ("the largest", "first to...")
- Technical specifications or version numbers

Rules:
- Extract up to 12 of the most important checkable claims.
- Ignore vague statements like "AI is growing fast."
- Each claim must quote the exact figure or fact from the text.

Return ONLY a valid JSON array. No markdown, no explanation.
Format:
[
  {{
    "claim": "exact claim text with the specific figure",
    "category": "statistic | date | financial | technical | ranking",
    "search_query": "concise web search query to verify this claim"
  }}
]

TEXT:
{text}"""

def extract_claims(client: Groq, text: str) -> list[dict]:
    prompt = EXTRACT_PROMPT.format(text=text[:5000])
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=2000,
    )
    raw = resp.choices[0].message.content.strip()
    if "```" in raw:
        raw = raw.split("```json")[-1].split("```")[0].strip()
    start, end = raw.find("["), raw.rfind("]")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON array found in response: {raw[:200]}")
    raw = re.sub(r",\s*([\]}])", r"\1", raw[start:end+1])
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
- "Verified"   -> current web data confirms the claim is accurate.
- "Inaccurate" -> the claim was once true but the figure is now outdated, OR the number is slightly wrong.
- "False"      -> the claim contradicts current evidence, OR no credible evidence supports it.

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
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=600,
    )
    raw = resp.choices[0].message.content.strip()
    raw = raw.split("```json")[-1].split("```")[0].strip() if "```" in raw else raw
    return json.loads(raw)


# ── API key resolution (env var → secrets → manual input) ────────────────────
_env_key = os.environ.get("GROQ_API_KEY", "").strip()
if not _env_key:
    try:
        _env_key = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        _env_key = ""

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f'<div class="icon-title" style="margin-bottom:12px">'
        f'{ic_gear(20)}<strong style="font-size:1.05rem">Configuration</strong></div>',
        unsafe_allow_html=True,
    )

    if _env_key:
        st.markdown(
            f'<div class="api-badge">{ic_lock(16)}'
            f'API key configured via environment</div>',
            unsafe_allow_html=True,
        )
        api_key = _env_key
    else:
        api_key = st.text_input(
            "Groq API Key",
            value="",
            type="password",
            help="Free key at console.groq.com — no credit card required",
        )

    st.markdown("---")
    st.markdown("<strong>How it works</strong>", unsafe_allow_html=True)
    for icon, text in [
        (ic_upload(16),  "Upload any PDF"),
        (ic_cpu(16),     "AI extracts all verifiable claims"),
        (ic_globe(16),   "Each claim is searched on the web"),
        (ic_check(16),   "AI flags: Verified / Inaccurate / False"),
    ]:
        st.markdown(
            f'<div class="sidebar-row">{icon}<span>{text}</span></div>',
            unsafe_allow_html=True,
        )
    st.markdown("---")
    st.markdown("<strong>Free stack</strong>", unsafe_allow_html=True)
    for icon, text in [
        (ic_cpu(16),      "LLM: Groq (Llama 3.3 70B)"),
        (ic_globe(16),    "Search: DuckDuckGo"),
        (ic_stack(16),    "Deploy: Streamlit Cloud"),
    ]:
        st.markdown(
            f'<div class="sidebar-row">{icon}<span>{text}</span></div>',
            unsafe_allow_html=True,
        )


# ── Main UI ───────────────────────────────────────────────────────────────────
st.markdown(
    f'<div class="icon-title" style="margin-bottom:4px">'
    f'{ic_search(32)}<h1 style="margin:0;font-size:2rem">Fact-Check Agent</h1></div>',
    unsafe_allow_html=True,
)
st.markdown(
    "Upload a PDF and the agent will **extract claims**, **search the web**, "
    "and **flag inaccuracies** automatically."
)

uploaded_file = st.file_uploader("Upload PDF", type=["pdf"], label_visibility="collapsed")

if uploaded_file:
    if not api_key:
        st.warning("Enter your Groq API key in the sidebar to continue.")
        st.stop()

    if st.button("Run Fact-Check", type="primary", use_container_width=True):
        client = get_client(api_key)

        # ── Step 1: Extract text ──────────────────────────────────────────────
        with st.spinner("Extracting text from PDF..."):
            try:
                pdf_text = extract_pdf_text(uploaded_file)
            except Exception as e:
                st.error(f"Failed to read PDF: {e}")
                st.stop()

        if not pdf_text.strip():
            st.error("No readable text found in this PDF (it may be image-based).")
            st.stop()

        with st.expander("Extracted PDF text (preview)", expanded=False):
            st.text(pdf_text[:1500] + ("..." if len(pdf_text) > 1500 else ""))

        # ── Step 2: Extract claims ────────────────────────────────────────────
        with st.spinner("Identifying verifiable claims..."):
            try:
                claims = extract_claims(client, pdf_text)
            except Exception as e:
                st.error(f"Claim extraction failed: {e}")
                st.stop()

        st.info(f"Found **{len(claims)}** verifiable claims. Starting web verification...")

        # ── Step 3: Verify each claim ─────────────────────────────────────────
        results = []
        progress = st.progress(0, text="Verifying claims...")

        for i, claim in enumerate(claims):
            progress.progress(i / len(claims), text=f"Checking claim {i+1}/{len(claims)}...")
            search_hits = web_search(claim.get("search_query", claim["claim"]))
            time.sleep(0.4)

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
        st.markdown(
            f'<div class="icon-title" style="margin-bottom:12px">'
            f'{ic_chart(22)}<h3 style="margin:0">Results</h3></div>',
            unsafe_allow_html=True,
        )

        verified   = [r for r in results if r["verdict"] == "Verified"]
        inaccurate = [r for r in results if r["verdict"] == "Inaccurate"]
        false_list = [r for r in results if r["verdict"] == "False"]

        c1, c2, c3 = st.columns(3)
        c1.markdown(
            f'<div class="metric-card">{ic_check(28)}'
            f'<div><div class="metric-num">{len(verified)}</div>'
            f'<div class="metric-lbl">Verified</div></div></div>',
            unsafe_allow_html=True,
        )
        c2.markdown(
            f'<div class="metric-card">{ic_warn(28)}'
            f'<div><div class="metric-num">{len(inaccurate)}</div>'
            f'<div class="metric-lbl">Inaccurate</div></div></div>',
            unsafe_allow_html=True,
        )
        c3.markdown(
            f'<div class="metric-card">{ic_xmark(28)}'
            f'<div><div class="metric-num">{len(false_list)}</div>'
            f'<div class="metric-lbl">False</div></div></div>',
            unsafe_allow_html=True,
        )

        st.markdown("---")

        VERDICT_ICON = {"Verified": ic_check, "Inaccurate": ic_warn, "False": ic_xmark}
        CSS_KEYS     = {"Verified": "verified", "Inaccurate": "inaccurate", "False": "false"}
        LABEL_PFX    = {"Verified": "[V]", "Inaccurate": "[!]", "False": "[X]"}

        for r in results:
            verdict = r.get("verdict", "False")
            css     = CSS_KEYS.get(verdict, "false")
            pfx     = LABEL_PFX.get(verdict, "[?]")
            label   = f"{pfx} {verdict} — {r['claim'][:85]}{'...' if len(r['claim']) > 85 else ''}"

            with st.expander(label, expanded=(verdict != "Verified")):
                icon_fn = VERDICT_ICON.get(verdict, ic_xmark)
                st.markdown(
                    f'<div class="verdict-{css}">'
                    f'{icon_fn(18)}'
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
                    st.markdown(
                        f'<div style="margin-top:6px">{ic_globe(14)}'
                        f'<a href="{r["source_url"]}" target="_blank">{r["source_url"]}</a></div>',
                        unsafe_allow_html=True,
                    )

        # ── Download JSON report ──────────────────────────────────────────────
        st.markdown("---")
        report_json = json.dumps(results, indent=2)
        st.download_button(
            label="Download full report (JSON)",
            data=report_json,
            file_name="fact_check_report.json",
            mime="application/json",
        )
