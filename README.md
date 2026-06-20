# RouteMaster
 A local, grounded guest-review ops desk for **Mini Homestay Bak** (Pontian, Johor).

RouteMaster ingests customer reviews, cross-references operational facts from a local knowledge file, drafts zero-hallucination replies, and files structured issues to the **Produck** API when action is needed.

---

## Track 2 — Required Sponsor Stack

| Requirement | Implementation |
|-------------|----------------|
| **Produck issue filing** | `POST https://api.produck.dev/v1/issues` via `routemaster/integration_hub.py` |
| **Structured payload** | `title`, `description`, `priority`, `labels` |
| **Local grounding** | Replies cite only `property_data/local_knowledge.txt` |

---

## Quick start

### Prerequisites

- Python 3.10+
- pip

### Install & run

```bash
git clone https://github.com/nuraliahatikah/RouteMaster.git
cd RouteMaster
pip install -r requirements.txt
streamlit run app.py
```

On Windows, if `streamlit` is not on PATH:

```powershell
py -3 -m pip install -r requirements.txt
py -3 -m streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## How it works

```
Guest review  →  reply_engine.py  →  sentiment + topics + grounded draft
                      ↓
              knowledge.py  →  matches facts from local_knowledge.txt
                      ↓
              integration_hub.py  →  Produck issue JSON + API push
```

- **No external LLM** — replies are assembled from matched knowledge facts only  
- **Session persistence** — evaluation survives Produck button clicks (`st.session_state`)  
- **Network fallback** — if Produck is unreachable (SSL/local), payload is captured locally for demo  

---

## Project structure

```
RouteMaster/
├── app.py                          # Streamlit dashboard (modular UI functions)
├── requirements.txt                # streamlit, requests
├── property_data/
│   └── local_knowledge.txt         # Ground-truth ops facts (parking, trash, checkout)
└── routemaster/
    ├── knowledge.py                # Load & section-parse knowledge file
    ├── reply_engine.py             # Sentiment, topic detection, grounded replies
    └── integration_hub.py          # Produck payload builder + API push
```

---

## Property knowledge (Mini Homestay Bak)

Operational facts baked into `local_knowledge.txt`:

- **Parking** — max 2 cars inside the gate; extra vehicles on the curb  
- **Trash** — double-bag kitchen waste; seal both knots to prevent leaks  
- **Checkout** — 11:00 AM standard departure  
- **Wi-Fi** — `HomestayBak_Guest`  

---

## Engineering notes

1. **Modular Python packages** — UI in `app.py`, logic in `routemaster/`  
2. **Ground-truth constraint** — `relevant_facts()` only returns lines from the knowledge file  
3. **Track 2 compliance** — Produck integration is a first-class UI step, not an afterthought  
4. **AI-assisted, engineer-owned** — Cursor used for iteration; architecture and integration written for explainability  

---

