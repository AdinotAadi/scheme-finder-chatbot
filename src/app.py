"""
app.py - Streamlit Chatbot application for Trustworthy Scheme Discovery with Guardrails & Llama 3.2:3b.
"""

import os
import sys
from pathlib import Path

# Ensure project root directory is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from typing import List, Dict, Any
from src.engine.vector_store import SchemeVectorStore
from src.engine.guardrails import PromptGuardrail
from src.engine.profile_extractor import extract_attributes_from_messages, get_missing_essential_attributes
from src.schema.rules import UserProfile
from src.llm.ollama_client import LocalOllamaClient

st.set_page_config(
    page_title="Scheme Finder - Trustworthy Government Schemes AI",
    page_icon="🇮🇳",
    layout="wide"
)

# Custom header styling
st.markdown("""
<div style="background-color: #0d233a; padding: 22px; border-radius: 10px; color: white; margin-bottom: 25px;">
    <h2 style="margin: 0; color: #ff9933;">🇮🇳 Scheme Finder</h2>
    <p style="margin: 6px 0 0 0; font-size: 1.05em; color: #e0e0e0;">
        Trustworthy, source-grounded scheme eligibility assistant for women in India. Powered by <b>Local Llama 3.2:3b</b>, <b>Qdrant Vector DB</b>, and <b>Strict Guardrails</b>.
    </p>
</div>
""", unsafe_allow_html=True)

# Sidebar with status, guardrail info, and filters
with st.sidebar:
    st.subheader("⚙️ System Status & Controls")
    
    # Initialize components
    @st.cache_resource
    def load_services():
        v_store = SchemeVectorStore()
        llm = LocalOllamaClient()
        return v_store, llm

    vector_store, ollama_client = load_services()
    
    ollama_ok = ollama_client.is_available()
    if ollama_ok:
        st.success("🟢 Local Ollama (llama3.2:3b) Connected")
    else:
        st.error("🔴 Local Ollama Offline. Ensure 'ollama serve' is running.")
        
    st.markdown("---")
    st.subheader("🛡️ Security & Guardrails")
    st.info("""
    - **Prompt Injection Defense**: Input pattern regex + XML boundary sandbox.
    - **No Promised Benefits**: Automated 'may be eligible' enforcement.
    - **Source Provenance**: Every response cites verbatim official passages & links.
    """)
    
    st.markdown("---")
    state_options = ["All", "Uttarakhand", "Chhattisgarh", "Gujarat", "Puducherry", "Rajasthan", "West Bengal", "Central"]
    selected_state = st.selectbox("📍 Optional State Filter", options=state_options, index=0)

    if st.button("🧹 Clear Chat History"):
        st.session_state.messages = []
        st.session_state.user_profile = UserProfile()
        st.rerun()

    # Display real-time profile dashboard in sidebar
    st.markdown("---")
    st.subheader("👤 Profile State")
    current_p = getattr(st.session_state, "user_profile", UserProfile())
    st.markdown(f"- **State:** `{current_p.state_residence or 'Not provided'}`")
    st.markdown(f"- **Gender:** `{current_p.gender or 'Not provided'}`")
    st.markdown(f"- **Age:** `{current_p.age if current_p.age is not None else 'Not provided'}`")
    if current_p.is_pregnant:
        st.markdown(f"- **Status:** `Pregnant`")
    if current_p.is_student:
        st.markdown(f"- **Occupation:** `Student`")

# Initialize message history and user profile
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Namaste! 🙏 I am your Scheme Finder assistant. "
                "I help women and families discover government welfare schemes they **may be eligible** for.\n\n"
                "To give you accurate recommendations without showing irrelevant schemes from other states, "
                "could you share:\n"
                "1. **Your State of residence**\n"
                "2. **Your approximate Age**\n"
                "3. **Your Gender** (and whether you are pregnant or a nursing mother, if applicable)?"
            )
        }
    ]

if "user_profile" not in st.session_state:
    st.session_state.user_profile = UserProfile()

# Display conversation messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Chat Input
if user_prompt := st.chat_input("Ask about schemes (e.g., 'I am a 16yo girl in Uttarakhand looking for health schemes')"):
    # Display user query
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # 1. Run Input Guardrails
    is_safe, sanitized_query, warning = PromptGuardrail.validate_user_input(user_prompt)

    # Incrementally extract profile attributes from updated conversation history
    updated_profile = extract_attributes_from_messages(st.session_state.messages, st.session_state.user_profile)
    st.session_state.user_profile = updated_profile
    missing_attrs = get_missing_essential_attributes(updated_profile)

    with st.chat_message("assistant"):
        if not is_safe:
            st.error(warning)
            st.session_state.messages.append({"role": "assistant", "content": warning})
        else:
            # Container for progressive real-time status
            status_container = st.status("🧠 Processing request through Trustworthy AI Pipeline...", expanded=True)
            
            with status_container:
                # Step 1: Guardrail Inspection
                st.write("🛡️ **Step 1: Security & Injection Inspection**")
                st.markdown(f"- Input status: `SAFE`")
                st.markdown(f"- Sanitized query: *\"{sanitized_query}\"*")
                
                # Step 2: Profile Extraction & Triage Check
                st.write("👤 **Step 2: Profile State & Triage Verification**")
                st.markdown(f"- Extracted Profile: State=`{updated_profile.state_residence or 'None'}`, Gender=`{updated_profile.gender or 'None'}`, Age=`{updated_profile.age or 'None'}`")
                if missing_attrs:
                    st.warning(f"⚠️ Missing Essential Attributes: `{', '.join(missing_attrs)}`. Prompting user to specify details before recommending state schemes.")
                else:
                    st.success("✅ Essential profile attributes present. Proceeding with targeted scheme retrieval.")

                # Step 3: Hybrid Retrieval in Qdrant
                st.write("🔍 **Step 3: Qdrant Vector & Lexical Hybrid Retrieval**")
                effective_state = updated_profile.state_residence if updated_profile.state_residence else (None if selected_state == "All" else selected_state)
                retrieved_schemes = vector_store.search_schemes(sanitized_query, state_filter=effective_state, top_k=5)
                st.markdown(f"- Retrieved **{len(retrieved_schemes)} candidate schemes** (Jurisdiction Filter: `{effective_state or 'Nationwide'}`):")
                for idx, r in enumerate(retrieved_schemes, 1):
                    st.markdown(f"  {idx}. **{r['name']}** (Score: `{r['score']:.3f}`, State: `{r.get('state') or 'Central'}`)")

                # Build verified context
                context_blocks = []
                for idx, hit in enumerate(retrieved_schemes, 1):
                    block = (
                        f"[{idx}] Scheme Name: {hit['name']} (State/UT: {hit.get('state') or 'Central'})\n"
                        f"Official Portal Link: {hit['source_url']}\n"
                        f"Eligibility Criteria (Verbatim): {hit.get('eligibility_verbatim') or 'See official portal'}\n"
                        f"Benefits (Verbatim): {hit.get('benefits') or 'See official portal'}\n"
                        f"Documents Required: {hit.get('documents_required') or 'Consult portal'}\n"
                    )
                    context_blocks.append(block)

                combined_context = "\n---\n".join(context_blocks)

                # Step 4: LLM Context Assembly & Generation
                st.write("⚡ **Step 4: Guarded Prompt Construction & Llama 3.2:3b Reasoning**")
                st.markdown(f"- Model: `{ollama_client.model_name}` (Local via Ollama)")
                st.markdown(f"- Triage Directive: `{'ACTIVE (Requesting ' + ', '.join(missing_attrs) + ')' if missing_attrs else 'RESOLVED (Recommending schemes)'}`")

            # 4. Invoke LLM with Missing Attribute Guidance
            llm_result = None
            if ollama_ok:
                llm_result = ollama_client.generate_guarded_response(
                    sanitized_query,
                    combined_context,
                    missing_attributes=missing_attrs if missing_attrs else None
                )
                response_text = llm_result["response"]
                status_container.update(label="✅ Verified Scheme Evaluation Complete", state="complete", expanded=False)
            else:
                top_scheme = retrieved_schemes[0] if retrieved_schemes else None
                if top_scheme:
                    response_text = (
                        f"Based on official records, you may be eligible for **{top_scheme['name']}**.\n\n"
                        f"**Eligibility Details:**\n{top_scheme['eligibility_verbatim']}\n\n"
                        f"🔗 **Official Portal:** {top_scheme['source_url']}"
                    )
                else:
                    response_text = "I could not find schemes matching your criteria. Please verify on https://www.myscheme.gov.in."
                status_container.update(label="⚠️ Ollama offline - showed vector match fallback", state="complete", expanded=False)

            # Display the final structured response
            st.markdown(response_text)

            # Expandable Step-by-Step LLM Reasoning & Prompt Inspector
            if llm_result and llm_result.get("guarded_prompt"):
                with st.expander("🔬 Live LLM Execution Inspector (Prompt, Sandboxing & Model Details)"):
                    st.markdown("#### 1. Delimited Prompt Sent to Llama 3.2:3b")
                    st.code(llm_result["guarded_prompt"], language="markdown")
                    st.markdown("#### 2. Raw Generation vs Output-Guarded Verification")
                    st.text(f"Raw Model Characters: {len(llm_result.get('raw_output', ''))} chars")
                    st.text(f"Guardrail Post-processing: Enforced 'may be eligible' and stripped hallucinated guarantees.")

            # Expandable Verified Source Inspection (PhD Transparency Requirement)
            if not missing_attrs:
                with st.expander("🔍 View Official Source Citations & Verbatim Passages"):
                    for hit in retrieved_schemes:
                        st.markdown(f"**[{hit['name']}]({hit['source_url']})** (`State: {hit.get('state') or 'Central'}`)")
                        st.markdown(f"- **Verbatim Eligibility:** {hit.get('eligibility_verbatim')}")
                        st.markdown(f"- **Benefits:** {hit.get('benefits')}")
                        if hit.get("documents_required"):
                            st.markdown(f"- **Documents:** {hit.get('documents_required')}")
                        st.markdown("---")

            st.session_state.messages.append({"role": "assistant", "content": response_text})

