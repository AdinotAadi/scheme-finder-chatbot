# 🚀 Performance & Accuracy Optimization Experiments Log

> **Standard**: Simplified Technical English (ASD-STE100 aligned)  
> **Branch**: `perf/responsiveness-accuracy-optimizations`  
> **Status**: Active Work in Progress  

---

## 1. Baseline Metrics (Before Optimization)

Recorded on October 30, 2026.

| Metric Area | Benchmark Item | Baseline Value | Source / Measurement |
|---|---|---|---|
| **Responsiveness** | Time-To-First-Token (TTFT) | **2,450 ms - 3,200 ms** | UI blocked until complete response generated (`stream=False`) |
| **Responsiveness** | Qdrant Client Init | Re-verified on script rerun | Redundant schema checks per turn |
| **Accuracy** | Precision @ 5 | 83.3% | `data/gold_standard/gold_rules_uttarakhand.py` test harness |
| **Accuracy** | Recall @ 5 | 87.5% | `data/gold_standard/gold_rules_uttarakhand.py` test harness |
| **Accuracy** | Semantic Retrieval Quality | Feature-hashing (lexical) | Word overlap only; misses true synonyms without manual keyword boosts |
| **Testing** | Vector Store Test Concurrency | File lock collision (`RuntimeError`) | Local Qdrant disk locked during concurrent Streamlit sessions |

---

## 2. Optimization Roadmap & Iteration Tracker

| Iteration | Category | Proposed Optimization | Target Impact | Status |
|---|---|---|---|---|
| **Iter 1** | Responsiveness | Streamlit Resource Caching (`@st.cache_resource`) | Instant UI reruns, single client lifecycle | ⏳ Pending |
| **Iter 2** | Responsiveness | Token Streaming (`st.write_stream` + HTTPX stream) | TTFT drops from ~2,800ms to **< 200ms** | ⏳ Pending |
| **Iter 3** | Test Robustness | In-Memory Qdrant Mode for Unit Tests (`:memory:`) | 100% concurrent test execution without disk locks | ⏳ Pending |
| **Iter 4** | Accuracy & Speed | Context Trimming & Smart Snippet Extraction | Cuts prompt tokens from ~2,500 to ~900; speeds generation by 35% | ⏳ Pending |
| **Iter 5** | Accuracy | Enhanced FastEmbed / ONNX Semantic Dense Vectors | Native synonym matching ("stipend" $\leftrightarrow$ "scholarship") | ⏳ Pending |

---

## 3. Iteration Records

*(Each completed iteration will be recorded below with its implementation diff, before/after measurements, and verification evidence.)*
