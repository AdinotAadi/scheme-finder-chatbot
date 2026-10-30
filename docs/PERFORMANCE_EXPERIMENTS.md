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
| **Iter 1** | Responsiveness | Streamlit Resource Caching (`@st.cache_resource`) | Instant UI reruns, single client lifecycle | ✅ **Completed** |
| **Iter 2** | Responsiveness | Token Streaming (`st.write_stream` + HTTPX stream) | TTFT drops from ~2,800ms to **< 200ms** | ✅ **Completed** |
| **Iter 3** | Test Robustness | In-Memory Qdrant Mode for Unit Tests (`:memory:`) | 100% concurrent test execution without disk locks | ✅ **Completed** |
| **Iter 4** | Accuracy & Speed | Context Trimming & Smart Snippet Extraction | Cuts prompt tokens from ~2,500 to ~900; speeds generation by 35% | ⏳ In Progress |
| **Iter 5** | Accuracy | Enhanced FastEmbed / ONNX Semantic Dense Vectors | Native synonym matching ("stipend" $\leftrightarrow$ "scholarship") | ⏳ Next |

---

## 3. Iteration Records

### 📌 Iteration 1 & 2: Streamlit Resource Caching & Token Streaming

* **Objective**: Eliminate blocking UI generation delays and reduce Time-To-First-Token (TTFT).
* **Changes Applied**:
  1. **HTTP Streaming Generator**: Added `LocalOllamaClient.stream_guarded_response()` in `src/llm/ollama_client.py` using `client.stream("POST", ...)`. Tokens are parsed from chunked JSON lines and yielded as soon as emitted by Llama 3.2:3b.
  2. **Reactive UI Streaming**: Updated `src/app.py` to pipe the stream generator into `st.write_stream()`.
  3. **Output Guardrail on Stream**: Applied `PromptGuardrail.validate_output()` on the complete text accumulated from the stream to ensure anti-guarantee safety.
  4. **Component Lifecycle**: Maintained `@st.cache_resource` for `SchemeVectorStore` and `LocalOllamaClient`, ensuring zero re-initialization overhead across conversational turns.
* **Measured Result**:
  - **Before**: 2,450 ms - 3,200 ms wait before user saw the first character.
  - **After**: **~160 ms TTFT** (Tokens stream in real-time).
  - **Subjective Experience**: High responsiveness; user reads output continuously.

---

### 📌 Iteration 3: In-Memory Qdrant Mode for Concurrent Test Execution

* **Objective**: Prevent `RuntimeError: Storage folder data/qdrant_db is already accessed by another instance of Qdrant client` during automated testing when the Streamlit app is active.
* **Changes Applied**:
  1. Updated `SchemeVectorStore.__init__(db_path)` in `src/engine/vector_store.py` to recognize `:memory:`. When `:memory:` is specified, Qdrant initializes an in-memory client without acquiring POSIX file locks on `data/qdrant_db/.lock`.
  2. Updated `tests/test_vector_store.py` to use a module-scoped pytest fixture `memory_vector_store` with `SchemeVectorStore(":memory:")`.
* **Measured Result**:
  - **Before**: Tests crashed with `BlockingIOError` / `RuntimeError` if Streamlit was running.
  - **After**: **22 passed in 0.50s** (100% of tests pass cleanly, even with active Streamlit dev server running).
