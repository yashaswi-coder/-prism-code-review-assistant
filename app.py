"""PRism Streamlit UI. Run with: streamlit run app.py"""

import streamlit as st

from prism.analyzer import analyze_source
from prism.inputs import MAX_BYTES, InputError, decode_upload
from prism.models import SEVERITY_ORDER
from prism.report import LIMITATIONS, to_json, to_markdown

st.set_page_config(page_title="PRism (WIP)", page_icon="🔍", layout="wide")
st.title("PRism: evidence-grounded code review")
st.warning(
    "Work in progress. Findings come from Ruff and Bandit and **require human review**. "
    "An empty result does not mean the code is correct or secure."
)
st.caption(
    "Privacy: code is analyzed locally by static tools in a temporary directory that is deleted "
    "afterwards. It is **never executed**, not sent to any external service, and not saved by PRism. "
    f"Limit: {MAX_BYTES // 1000} KB, `.py` text only."
)

paste_tab, upload_tab = st.tabs(["Paste code", "Upload .py file"])
submission = None  # (source, display_name) set when a button is pressed

with paste_tab:
    pasted = st.text_area("Python source", height=260, key="pasted")
    if st.button("Analyze pasted code", type="primary"):
        submission = (pasted, None)

with upload_tab:
    uploaded = st.file_uploader("Python file", type=["py"])
    if st.button("Analyze uploaded file", disabled=uploaded is None):
        try:
            submission = decode_upload(uploaded.getvalue(), uploaded.name)
        except InputError as exc:
            st.error(str(exc))

if submission:
    try:
        with st.spinner("Running Ruff and Bandit..."):
            st.session_state["result"] = analyze_source(*submission)
    except InputError as exc:
        st.session_state.pop("result", None)
        st.error(str(exc))

result = st.session_state.get("result")
if result:
    st.divider()
    st.subheader(f"Results for {result.file_name}")

    for run in result.tool_runs:
        label = f"{run.tool} {run.tool_version or ''}: {run.status}"
        if run.status == "ok":
            st.success(f"{label} ({run.finding_count} findings, {run.duration_s}s)")
        elif run.status == "partial":
            st.warning(f"{label}. {run.detail}")
        else:
            st.error(f"{label}. {run.detail} Results are incomplete.")

    all_f = result.findings
    c1, c2, c3 = st.columns(3)
    sources = sorted({f.source_tool for f in all_f})
    severities = sorted({f.severity for f in all_f}, key=SEVERITY_ORDER.get)
    categories = sorted({f.category for f in all_f})
    sel_src = c1.multiselect("Source", sources, default=sources)
    sel_sev = c2.multiselect("Severity", severities, default=severities)
    sel_cat = c3.multiselect("Category", categories, default=categories)

    shown = [f for f in all_f if f.source_tool in sel_src and f.severity in sel_sev and f.category in sel_cat]
    st.write(f"Showing {len(shown)} of {len(all_f)} deterministic findings.")
    if not all_f:
        st.info("No findings from the tools that ran. This is not proof the code is correct or secure.")

    for f in shown:
        end = f"-{f.line_end}" if f.line_end != f.line_start else ""
        with st.expander(f"[{f.severity.upper()}] {f.rule_id} · line {f.line_start}{end} · {f.message[:80]}"):
            conf = f" · confidence: {f.confidence}" if f.confidence else ""
            st.markdown(f"**{f.source_tool}** · {f.category}{conf}  \n{f.message}")
            if f.evidence.snippet:
                st.code(f.evidence.snippet, language="python", line_numbers=True,
                        wrap_lines=True)
            if f.suggested_fix:
                st.markdown(f"Tool-suggested fix: {f.suggested_fix}")
            links = []
            if f.evidence.reference_url:
                links.append(f"[reference]({f.evidence.reference_url})")
            if f.evidence.cwe_id:
                links.append(f"CWE-{f.evidence.cwe_id}")
            if links:
                st.caption(" · ".join(links))

    d1, d2 = st.columns(2)
    d1.download_button("Download Markdown report", to_markdown(result),
                       file_name="prism_report.md", mime="text/markdown")
    d2.download_button("Download JSON report", to_json(result),
                       file_name="prism_report.json", mime="application/json")
    with st.expander("Limitations"):
        st.write(LIMITATIONS)
