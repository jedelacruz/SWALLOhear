"""SWALLOHear web app (research use only).  Run from the repo folder:  streamlit run app/streamlit_app.py
Uses the trained noise-augmented Random Forest + learned event-reliability model + signal-quality gate (src/swallohear/final.py).
NOTE: written without Streamlit installed in the build environment; the analysis code is tested, the page layout code is not."""
import sys, pathlib, json, io
ROOT = pathlib.Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import numpy as np, pandas as pd, streamlit as st, plotly.graph_objects as go
from swallohear import io as sio
from swallohear.final import Analyzer

st.set_page_config(page_title="SWALLOHear", layout="wide")
st.title("SWALLOHear")
st.warning("RESEARCH USE ONLY. Detects swallowing-related acoustic events in neck-microphone audio. It is NOT a diagnostic device and does not assess dysphagia, aspiration or pneumonia. Do not upload identifiable patient audio to a public instance.")

@st.cache_resource
def load_analyzer(): return Analyzer(str(ROOT / "models"), str(ROOT / "configs" / "final.json"), str(ROOT / "results" / "reliability_v2.json"))
try: A = load_analyzer()
except Exception as e: st.error(f"Trained models not found in models/ ({e}). Run the training scripts first."); st.stop()

DEMO = ROOT / "data" / "demo"; demos = sorted(DEMO.glob("*.wav")) if DEMO.exists() else []
with st.sidebar:
    st.header("Input")
    src = st.radio("Source", ["Demo recording", "Upload WAV"])
    st.caption("Reliability threshold (Confident tier)"); tau = st.slider("Confident if reliability score >=", 0.2, 0.9, float(A.tau), 0.05)
    A.tau = tau
    st.markdown("**Tiers:** Confident = high reliability score. Low-confidence = detected but not trusted. No event = nothing detected. Inconclusive = recording quality too low; results withheld.")

audio, label, ref = None, "", []
if src == "Upload WAV":
    f = st.file_uploader("WAV file (max 20 MB, 120 s)", type=["wav"])
    if f is not None:
        if f.size > 20 * 1024 * 1024: st.error("File too large (max 20 MB).")
        else:
            try: audio, label = sio.load_audio(f.read()), f.name
            except Exception as e: st.error(f"Could not read this file: {e}")
else:
    if demos:
        d = st.selectbox("Clip", demos, format_func=lambda p: p.name.replace("demo_", "").replace(".wav", ""))
        audio, label = sio.load_audio(str(d)), d.name
        j = d.with_suffix(".json")
        if j.exists(): meta = json.load(open(j)); ref = meta.get("reference_events_s", []); st.caption(f"Source: {meta.get('note','')}. Data: Khalifa et al. (2021), CC BY 4.0.")
    else: st.info("No demo clips yet. Run: python scripts/make_demo_clips.py")

if audio is not None:
    r = A.analyze(audio["signal"], orig_nyquist=audio.get("orig_nyquist", 2000.0))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Record status", r["status"]); c2.metric("Confident events", sum(e["tier"] == "Confident" for e in r["events"]))
    c3.metric("Low-confidence", sum(e["tier"] == "Low-confidence" for e in r["events"])); c4.metric("Latency (s)", f"{r['latency_s']:.2f}")
    if r["reason_codes"]: st.error("Result withheld. Quality issues: " + ", ".join(r["reason_codes"]) + ". Re-record in a quieter setting.")
    show_ref = st.checkbox("Show reference (expert) labels", value=bool(ref)) if ref else False
    x = audio["signal"]; t = np.arange(len(x)) / 4000
    fig = go.Figure(go.Scatter(x=t[::2], y=x[::2], mode="lines", name="waveform", line=dict(width=1, color="#244668")))
    col = {"Confident": "rgba(36,70,104,.30)", "Low-confidence": "rgba(229,133,99,.30)"}
    for e in r["events"]: fig.add_vrect(x0=e["onset_s"], x1=e["offset_s"], fillcolor=col[e["tier"]], line_width=0, annotation_text="C" if e["tier"] == "Confident" else "L")
    if show_ref:
        for s, e in ref: fig.add_vrect(x0=s, x1=e, fillcolor="rgba(0,0,0,0)", line_width=1.5, line_dash="dot", line_color="#2a7f62")
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10), xaxis_title="time (s)", yaxis_title="amplitude", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Filled boxes = detected events (C = Confident, L = Low-confidence). Dotted green outlines = expert reference labels (demo clips only).")
    q = r["quality"]; st.subheader("Signal quality"); st.write(f"Estimated SNR **{q['snr_db']:.1f} dB** (cut-off {A.snr_min:.1f} dB) | clipped {q['clip_frac']:.1%} | flat {q['flat_frac']:.1%} | duration {q['duration_s']:.1f} s | original bandwidth {audio.get('orig_nyquist', 2000):.0f} Hz")
    rows = r["events"] if r["events"] else r["withheld_candidates"]
    if rows:
        df = pd.DataFrame(rows).round(3); st.subheader("Events" if r["events"] else "Candidates (withheld because quality is too low)"); st.dataframe(df)
        n = len(df); dur = float(df.duration_ms.median()) if n else 0
        st.write(f"Session summary: {n} events, {n / max(q['duration_s'] / 60, 1e-9):.1f} per minute, median duration {dur:.0f} ms.")
        if r["events"]:
            st.download_button("Export CSV", df.to_csv(index=False), "swallohear_events.csv", "text/csv")
            st.download_button("Export JSON", json.dumps(dict(input=label, status=r["status"], tau=A.tau, snr_min=A.snr_min, events=r["events"], quality=q), indent=1), "swallohear_session.json", "application/json")
    elif not r["reason_codes"]: st.info("No event detected. This does not prove no swallow occurred.")
