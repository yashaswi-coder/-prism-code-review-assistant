"""PRism Streamlit UI. Run with: streamlit run app.py"""

import streamlit as st

from prism.analyzer import analyze_source
from prism.diffs import decode_diff_upload
from prism.feedback import serialize_feedback
from prism.inputs import MAX_BYTES, InputError, decode_upload
from prism.models import SEVERITY_ORDER
from prism.report import LIMITATIONS, to_json, to_markdown

st.set_page_config(page_title="PRism (WIP)", page_icon="🔍", layout="wide")
st.title("PRism: evidence-grounded code review")
st.warning(
    "Work in progress. Python findings come from Ruff and Bandit; Java findings come from "
    "PRism's local Semgrep rules. All findings **require human review**. "
    "An empty result does not mean the code is correct or secure."
)
st.caption(
    "Privacy: code is analyzed locally by static tools in a temporary directory that is deleted "
    "afterwards. It is **never executed**, not sent to any external service, and not saved by PRism. "
    "Feedback stays in this browser session unless you explicitly download its metadata-only export. "
    f"Limit: {MAX_BYTES // 1000} KB per upload. Python and Java source, plus Python unified diffs, are text-only."
)

paste_tab, upload_tab, diff_tab = st.tabs(["Paste code", "Upload source file", "Review Python diff"])
submission = None  # (source, display_name) set when a button is pressed

with paste_tab:
    pasted_language = st.selectbox("Language", ["Python", "Java"], key="paste_language")
    pasted = st.text_area(f"{pasted_language} source", height=260, key="pasted")
    if st.button("Analyze pasted code", type="primary"):
        pasted_name = "pasted_code.java" if pasted_language == "Java" else None
        submission = (pasted, pasted_name)
        st.session_state.pop("diff_review", None)

with upload_tab:
    uploaded = st.file_uploader("Python or Java source file", type=["py", "java"])
    if st.button("Analyze uploaded file", disabled=uploaded is None):
        try:
            submission = decode_upload(uploaded.getvalue(), uploaded.name)
            st.session_state.pop("diff_review", None)
        except InputError as exc:
            st.error(str(exc))

with diff_tab:
    st.caption(
        "Upload a single-file .diff/.patch and the complete updated .py file. "
        "PRism analyzes the full file, then shows findings overlapping added lines."
    )
    diff_file = st.file_uploader(
        "Unified diff (.diff or .patch)", type=["diff", "patch"], key="diff_file"
    )
    changed_source = st.file_uploader(
        "Updated Python source (.py)", type=["py"], key="diff_source"
    )
    if st.button("Analyze changed lines", disabled=diff_file is None or changed_source is None):
        st.session_state.pop("result", None)
        st.session_state.pop("diff_review", None)
        try:
            diff_spec = decode_diff_upload(diff_file.getvalue(), diff_file.name)
            source, source_name = decode_upload(changed_source.getvalue(), changed_source.name)
            if diff_spec.file_path.casefold() != source_name.casefold():
                raise InputError(
                    f"The diff targets '{diff_spec.file_path}', but the uploaded file is "
                    f"'{source_name}'. Upload the matching updated Python file."
                )
            analysis = analyze_source(source, source_name)
            changed_findings = [
                finding for finding in analysis.findings
                if any(finding.line_start <= line <= finding.line_end for line in diff_spec.changed_lines)
            ]
            filtered_runs = [
                run.model_copy(
                    update={"finding_count": sum(item.source_tool == run.tool for item in changed_findings)}
                )
                for run in analysis.tool_runs
            ]
            st.session_state["result"] = analysis.model_copy(
                update={"findings": changed_findings, "tool_runs": filtered_runs}
            )
            st.session_state["diff_review"] = {
                "file": diff_spec.file_path,
                "changed_lines": sorted(diff_spec.changed_lines),
            }
        except InputError as exc:
            st.error(str(exc))

if submission:
    try:
        source_language = "Java" if (submission[1] or "").lower().endswith(".java") else "Python"
        tool_label = "Semgrep Java rules" if source_language == "Java" else "Ruff and Bandit"
        with st.spinner(f"Running {tool_label}..."):
            st.session_state["result"] = analyze_source(*submission)
    except InputError as exc:
        st.session_state.pop("result", None)
        st.error(str(exc))

result = st.session_state.get("result")
if result:
    st.divider()
    st.subheader(f"Results for {result.file_name}")
    feedback_key_prefix = f"feedback_{result.generated_at.timestamp():.6f}"
    diff_review = st.session_state.get("diff_review")
    if diff_review:
        changed = diff_review["changed_lines"]
        st.info(
            f"Showing findings overlapping {len(changed)} added/changed line(s) "
            f"in {diff_review['file']}. Analysis ran on the complete uploaded file."
        )

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
                code_language = "java" if result.file_name.lower().endswith(".java") else "python"
                st.code(f.evidence.snippet, language=code_language, line_numbers=True,
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
            st.radio(
                "Finding feedback",
                ["No feedback", "Useful", "Incorrect", "Not useful"],
                horizontal=True,
                key=f"{feedback_key_prefix}_{f.id}",
            )

    d1, d2 = st.columns(2)
    d1.download_button("Download Markdown report", to_markdown(result),
                       file_name="prism_report.md", mime="text/markdown")
    d2.download_button("Download JSON report", to_json(result),
                       file_name="prism_report.json", mime="application/json")
    feedback_labels = {
        finding.id: label
        for finding in shown
        if (label := st.session_state.get(f"{feedback_key_prefix}_{finding.id}")) in {
            "Useful", "Incorrect", "Not useful"
        }
    }
    if feedback_labels:
        normalized_labels = {
            finding_id: label.lower().replace(" ", "_")
            for finding_id, label in feedback_labels.items()
        }
        st.download_button(
            "Download finding feedback (JSON)",
            serialize_feedback(result, normalized_labels),
            file_name="prism_feedback.json",
            mime="application/json",
            help="Exports labels and rule metadata only. Source code and finding text are excluded.",
        )
    with st.expander("Limitations"):
        st.write(LIMITATIONS)
