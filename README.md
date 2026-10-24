# SWALLOHear — research prototype (NOT a diagnostic device)

Reliability-aware acoustic swallowing-event analysis from neck-microphone audio. Team RIPARION, PJDSC 2026.
It detects swallowing-related acoustic events, localizes onset/offset, and says **how far to trust each result**
(Confident / Low-confidence / No event / Inconclusive). It does not diagnose dysphagia, aspiration or pneumonia.

![SWALLOHear web app demo](docs/demo.gif)

**Web app guide:** [`docs/APP_GUIDE.md`](docs/APP_GUIDE.md) covers every feature with screenshots, how it works, exports and
troubleshooting. Full video walkthrough: [`docs/demo.webm`](docs/demo.webm).

**Mobile app (Android & iOS, Expo):** [`docs/MOBILE_GUIDE.md`](docs/MOBILE_GUIDE.md) covers running it on your phone with
Expo Go, the analysis API it talks to (`api/server.py`) and every screen.

## Data
Khalifa, Donohue, Coyle & Sejdić (2021), *Swallowing High Resolution Cervical Auscultation Signals*, Zenodo, https://doi.org/10.5281/zenodo.4539695 (CC BY 4.0).
Not stored in this repo. The files we received contain **1,285 recordings; 1,092 have labelled swallows (1,876 swallows, 174 participants)**; labels are video-fluoroscopy frame numbers at 60 fps; signals are 4 kHz, 4 channels (we use the microphone, channel 0).
This is fewer than the headline numbers on the dataset page (248 patients, 3,144 swallows); we report what the files contain. The file prefixes `ns` / `s` (139 / 35 participants) are kept as unlabelled groups: their meaning (e.g. stroke) is **not verified**, so no stroke claims are made.

## Quick start (Windows or Mac)
Use **Python 3.13**. On Windows 11 with Smart App Control on, brand-new Python versions and package wheels can be blocked
(`DLL load failed … Application Control policy`); `requirements.txt` pins established releases that load (see the
[guide](docs/APP_GUIDE.md#troubleshooting)).
```
python -m venv .venv
.venv\Scripts\activate          # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python tests/test_core.py       # 8 tests, no dataset needed
streamlit run app/streamlit_app.py   # needs models/ (see below) and data/demo/
```
## Reproduce the experiments (order matters)
1. Download `signals.zip` and `labels.zip` from the DOI above into `data/raw/`.
2. `python scripts/prepare_data.py --dir data/raw`   (checksums + unpack to data/interim)
3. `python scripts/build_index.py`                   (sanity checks + participant-disjoint 70/15/15 split -> data/interim/splits.json)
4. `python scripts/evaluate_baselines.py`            (E1: energy baseline vs Random Forest)
5. `python scripts/run_experiments.py`               (calibration, confidence, noise, sensor ablation; saves models/rf_mic.joblib)
6. `python scripts/run_reliability_v2.py`            (noise-augmented RF, learned reliability model, quality gate; saves models/*.joblib)
7. `python scripts/bootstrap_ci.py`                  (participant-level 95% confidence intervals)
8. `python scripts/make_demo_clips.py`               (demo clips from TEST participants only)
Random seeds are fixed. All thresholds are fit on training or validation participants; the test participants (27 people, 171 recordings, 288 swallows) are used only for reporting.

## What we found (single participant-disjoint split; test participants only; 95% CI = participant-level bootstrap)
All numbers below come from `results/*.json`; the bootstrap script checks itself against the main run and prints OK/MISMATCH.

| Question | Result |
|---|---|
| Event detection, clean audio (match at overlap >= 0.5) | Energy baseline F1 0.28 (0.23-0.34); Random Forest F1 0.47-0.49 (CI about 0.39-0.59). Noise-augmented and clean-trained RF are tied on clean audio (F1 0.492 vs 0.494; difference -0.001, CI -0.027 to +0.021). |
| Robustness to white noise | Clean-trained RF collapses (F1 0.16 at 20 dB, 0.00 at 10 and 5 dB). Noise-augmented RF keeps F1 0.47 / 0.40 / 0.31 at 20 / 10 / 5 dB (gain over clean-trained at 20 dB +0.31, CI 0.23-0.39). |
| Is the model's own confidence trustworthy? | No. Event-level AUROC for "is this detection correct": 0.53 (0.47-0.60) from raw confidence vs 0.79 (0.73-0.84) from the learned reliability model on clean audio (difference CI 0.17-0.34). The learned score is also better at 20, 10 and 5 dB (all difference CIs exclude 0). Temperature scaling did not fix calibration (RF ECE 0.224 -> 0.219). |
| Reliability-aware vs ordinary output (clean) | Precision 0.41 -> 0.68 (0.58-0.77), false detections 9.5 -> 1.6 per minute, at the cost of recall 0.62 -> 0.33 (F1 0.49 -> 0.45). At 20 dB: precision 0.38 -> 0.61, recall 0.61 -> 0.23. |
| Quality gate under noise | The gate flags 2% of clean, 30% of 20 dB, 82% of 10 dB and 94% of 5 dB recordings as Inconclusive, so almost nothing is reported at 10 dB or worse; no precision claim is made there. |
| Microphone vs neck accelerometer | No advantage for the accelerometer in our RF pipeline (F1 0.47 vs 0.47). |

## Limitations
Modest absolute accuracy (F1 about 0.5). The reliability-aware output buys precision with a large loss of recall; it is a trade-off, not a free improvement. Some "false detections" may be real swallows that were not labelled (the dataset authors report this); no manual audit was done yet. Noise tests use synthetic white noise only, not real household noise. No CNN was built (a Random Forest was used instead). One split, one run, 27 test participants. Group labels `ns`/`s` are unverified, so no stroke-specific claims. Not validated on any smartphone or low-cost stethoscope. Research use only; no clinical or Philippine validation.

## Layout
`src/swallohear/` core package (io, preprocess, features, detectors, reliability, final) · `scripts/` experiments · `app/streamlit_app.py` + `app/views/` web app (guide: `docs/APP_GUIDE.md`) · `api/server.py` HTTP API + `mobile/` Expo app (guide: `docs/MOBILE_GUIDE.md`) · `configs/final.json` selected thresholds · `models/` trained models · `data/demo/` demo clips (CC BY 4.0) · `results/` experiment outputs · `tests/`.
