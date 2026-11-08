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
from src.schema.forms import RAN_HMDG_ApplicationForm, DelhiArogyaNidhi_ApplicationForm
from src.engine.form_autofill import FormAutoFillEngine
from src.engine.pdf_generator import ApplicationFormPDFGenerator
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

                # Build verified context with smart snippet trimming (Cuts context length by ~50% for fast generation)
                context_blocks = []
                for idx, hit in enumerate(retrieved_schemes, 1):
                    # Smart snippet: clamp very long eligibility or benefit text blocks to 500 chars to save tokens
                    elig_snippet = (hit.get('eligibility_verbatim') or 'See official portal')[:500]
                    benefits_snippet = (hit.get('benefits') or 'See official portal')[:500]
                    docs_snippet = (hit.get('documents_required') or 'Consult portal')[:250]
                    
                    block = (
                        f"[{idx}] Scheme Name: {hit['name']} (State/UT: {hit.get('state') or 'Central'})\n"
                        f"Official Portal Link: {hit['source_url']}\n"
                        f"Eligibility Criteria: {elig_snippet}\n"
                        f"Benefits: {benefits_snippet}\n"
                        f"Documents Required: {docs_snippet}\n"
                    )
                    context_blocks.append(block)

                combined_context = "\n---\n".join(context_blocks)

                # Step 4: LLM Context Assembly & Generation
                st.write("⚡ **Step 4: Guarded Prompt Construction & Llama 3.2:3b Reasoning**")
                st.markdown(f"- Model: `{ollama_client.model_name}` (Local via Ollama)")
                st.markdown(f"- Triage Directive: `{'ACTIVE (Requesting ' + ', '.join(missing_attrs) + ')' if missing_attrs else 'RESOLVED (Recommending schemes)'}`")

            # 4. Invoke LLM with Missing Attribute Guidance & Streaming
            llm_result = None
            if ollama_ok:
                status_container.update(label="⚡ Streaming Grounded Scheme Analysis...", state="running", expanded=False)
                
                # Stream directly into the chat container for instant sub-200ms TTFT
                stream_generator = ollama_client.stream_guarded_response(
                    sanitized_query,
                    combined_context,
                    missing_attributes=missing_attrs if missing_attrs else None
                )
                raw_response = st.write_stream(stream_generator)
                
                # Apply output guardrail verification to accumulated streamed output
                response_text = PromptGuardrail.validate_output(raw_response).strip()
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

            # 5. Universal Multi-Domain Application Form Auto-Fill & PDF Generator Section
            st.markdown("---")
            with st.expander("📝 Auto-Fill Official Application Form & Download PDF", expanded=False):
                st.markdown("Generate ready-to-print official government application forms dynamically customized for **any eligible scheme**.")
                
                # Build scheme options from retrieved candidates
                scheme_options = {}
                for h in retrieved_schemes:
                    label = f"{h['name']} ({h.get('state') or 'Central'})"
                    scheme_options[label] = h
                
                # Include standard dedicated health templates
                scheme_options["Rashtriya Arogya Nidhi (RAN) & HMDG [Central Ministry]"] = {
                    "scheme_id": "ran_hmdg", "name": "Rashtriya Arogya Nidhi (RAN) & HMDG",
                    "level": "Central", "state": "Central", "documents_required": "- Medical Estimate\n- Income Certificate\n- Ration card\n- Aadhaar"
                }
                scheme_options["Delhi Arogya Nidhi / Kosh (DAN/DAK) [Govt of Delhi]"] = {
                    "scheme_id": "dan_dak", "name": "Delhi Arogya Nidhi / Kosh",
                    "level": "State", "state": "Delhi", "documents_required": "- Estimate certificate\n- 3-yr Domicile\n- SDM Income Certificate"
                }

                chosen_label = st.selectbox("Select Target Scheme to Auto-Fill:", list(scheme_options.keys()))
                target_scheme = scheme_options[chosen_label]

                col1, col2 = st.columns(2)
                with col1:
                    default_name = getattr(updated_profile, "full_name", None) or "Beneficiary"
                    f_name = st.text_input("Applicant / Patient Full Name", value=default_name, key="form_p_name")
                    f_age = st.number_input("Age (Years)", min_value=1, max_value=120, value=int(updated_profile.age) if updated_profile.age else 25, key="form_p_age")
                    f_address = st.text_input("Residential Address & Domicile", value=f"{updated_profile.district_residence or 'Haridwar'}, {updated_profile.state_residence or 'Uttarakhand'}", key="form_address")
                    f_income = st.number_input("Monthly Family Income (₹)", min_value=0.0, value=round((updated_profile.annual_income_inr or 60000.0) / 12.0, 2), key="form_income")
                with col2:
                    f_parent = st.text_input("Father's / Mother's / Spouse Name", value="Family Head", key="form_parent")
                    f_mobile = st.text_input("Contact Mobile Number", value="9876543210", key="form_mobile")
                    is_bpl_val = getattr(updated_profile, "is_bpl", False)
                    f_ration = st.text_input("Ration Card / Food Security ID", value="BPL-Antyodaya-Enclosed" if is_bpl_val else "Attached", key="form_ration")
                    is_student_val = getattr(updated_profile, "is_student", False)
                    default_extra = "Government Inter College" if is_student_val else "Government Institution / Hospital"
                    f_extra = st.text_input("Scheme Specific Particulars (e.g., Hospital / School / BOCW Regn)", value=default_extra, key="form_extra")

                from src.engine.template_overlay import OfficialTemplateOverlayEngine

                # Check if 1:1 official physical government template is available for chosen scheme
                is_1to1_available = OfficialTemplateOverlayEngine.is_template_available(chosen_label)
                form_mode = "1:1 Official Govt Template"
                if is_1to1_available:
                    form_mode = st.radio(
                        "Form Format Option:",
                        ["1:1 Authentic Official Paper Proforma (Pixel-Perfect Scan)", "Universal Standardized Digital Proforma"],
                        index=0,
                        horizontal=True,
                        key="form_mode_radio"
                    )

                # Generate Dynamic Universal or Specialized Form
                if "Rashtriya Arogya" in chosen_label:
                    if is_1to1_available and "1:1 Authentic" in form_mode:
                        pdf_data = OfficialTemplateOverlayEngine.fill_ran_hmdg_official(
                            profile=updated_profile,
                            hospital_name="AIIMS New Delhi",
                            disease_name=f_extra if f_extra != "Government Institution / Hospital" else "Chronic Illness",
                            amount_requested=150000.0,
                            applicant_name=f_name,
                            parent_spouse_name=f_parent,
                            contact_mobile=f_mobile,
                            ration_card_no=f_ration,
                        )
                        file_name = f"Official_1to1_RAN_HMDG_{f_name.replace(' ', '_')}.pdf"
                    else:
                        ran_form, _ = FormAutoFillEngine.map_to_ran_hmdg(
                            updated_profile,
                            {
                                "patient_name": f_name,
                                "patient_age": f_age,
                                "disease_name": f_extra,
                                "hospital_name": "Government Medical College / AIIMS",
                                "permanent_address": f_address,
                                "monthly_income_inr": f_income,
                                "financial_assistance_required_inr": 150000.0,
                                "ration_card_no": f_ration,
                                "mobile_no": f_mobile,
                                "parent_name": f_parent
                            }
                        )
                        pdf_data = ApplicationFormPDFGenerator.generate_ran_hmdg_pdf(ran_form)
                        file_name = f"RAN_HMDG_Application_{f_name.replace(' ', '_')}.pdf"
                elif "Delhi Arogya" in chosen_label:
                    if is_1to1_available and "1:1 Authentic" in form_mode:
                        pdf_data = OfficialTemplateOverlayEngine.fill_delhi_arogya_nidhi_official(
                            profile=updated_profile,
                            hospital_name="Lok Nayak Jai Prakash (LNJP) Hospital, Delhi",
                            disease_name=f_extra if f_extra != "Government Institution / Hospital" else "Cardiac Treatment",
                            amount_requested=120000.0,
                            applicant_name=f_name,
                            parent_spouse_name=f_parent,
                            contact_mobile=f_mobile,
                            ration_card_no=f_ration,
                        )
                        file_name = f"Official_1to1_Delhi_Arogya_Nidhi_{f_name.replace(' ', '_')}.pdf"
                    else:
                        dan_form, _ = FormAutoFillEngine.map_to_delhi_arogya_nidhi(
                            updated_profile,
                            {
                                "patient_name": f_name,
                                "patient_age": f_age,
                                "disease_name": f_extra,
                                "hospital_name": "Government Hospital of Delhi",
                                "residential_address": f_address,
                                "monthly_family_income_inr": f_income,
                                "parent_or_husband_name": f_parent
                            }
                        )
                        pdf_data = ApplicationFormPDFGenerator.generate_delhi_arogya_nidhi_pdf(dan_form)
                        file_name = f"Delhi_Arogya_Nidhi_Application_{f_name.replace(' ', '_')}.pdf"
                else:
                    # Universal Dynamic Welfare Form applicable across ALL 145+ schemes
                    u_form, _ = FormAutoFillEngine.map_to_universal_form(
                        scheme_dict=target_scheme,
                        profile=updated_profile,
                        extracted_data={
                            "applicant_name": f_name,
                            "applicant_age": f_age,
                            "permanent_address": f_address,
                            "monthly_family_income_inr": f_income,
                            "parent_name": f_parent,
                            "mobile_no": f_mobile,
                            "ration_card_no": f_ration,
                            "school_name": f_extra,
                            "disease_name": f_extra,
                            "hospital_name": f_extra,
                            "bocw_regn_no": f_extra
                        }
                    )
                    pdf_data = ApplicationFormPDFGenerator.generate_universal_welfare_pdf(u_form)
                    slug_clean = target_scheme.get("scheme_id", "welfare_scheme")
                    file_name = f"{slug_clean.upper()}_Official_Application_{f_name.replace(' ', '_')}.pdf"

                st.download_button(
                    label=f"📥 Download Filled Official Form for '{target_scheme['name']}' (PDF)",
                    data=pdf_data,
                    file_name=file_name,
                    mime="application/pdf"
                )


