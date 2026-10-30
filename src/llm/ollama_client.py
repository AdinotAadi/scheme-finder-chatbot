"""
ollama_client.py - Local Ollama client interface for Llama 3.2:3b with guardrails and timeouts.
"""

import os
from typing import Dict, Any, Optional
import httpx
from src.engine.guardrails import PromptGuardrail

OLLAMA_BASE_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

SYSTEM_DIRECTIVE = """You are 'Scheme Finder AI', a trusted, comprehensive, and empathetic expert on government welfare schemes in India.
Your mission is to provide thorough, detailed, and practically useful guidance to citizens and women seeking welfare support.

DETAILED STRUCTURED RESPONSE GUIDELINES:
For EVERY scheme mentioned in the verified records that may match the user's needs, organize your answer with comprehensive, clearly labeled sections:

1. **Scheme Overview**: Name of the scheme, administering department/state, and its core purpose.
2. **Why You May Be Eligible (Detailed Breakdown)**:
   - Walk through each criterion (age range, residential domicile, marital/pregnancy status, worker/student category, income limit).
   - Explicitly compare the user's stated background against each criterion.
3. **Comprehensive Benefits & Financial Support**:
   - Provide full details of all financial aid, medical treatments, nutritional allowances, kits, or subsidies.
   - Mention payment mode (e.g. DBT / Direct Bank Transfer) or service delivery locations.
4. **Documents & Records Required**:
   - Give an itemized checklist of identity, address, income, and medical certificates needed.
5. **How & Where to Apply (Step-by-Step)**:
   - Official portal URL, application steps, offline centers (Anganwadi, government hospitals, CSC centers), and forms.

MANDATORY BEHAVIORAL CONSTRAINTS:
1. ALWAYS use cautious phrasing: "You may be eligible" - NEVER guarantee or promise that a benefit or sanction will be awarded.
2. Provide extensive, rich, and well-structured markdown details. Do not give curt or one-paragraph summaries.
3. Rely strictly on the verified scheme records provided. If a specific detail (like a contact number) is not present, guide the user to consult the official link.
4. If multiple schemes match (e.g., both transportation and medical checkups), cover each scheme in detail.
"""

class LocalOllamaClient:
    def __init__(self, base_url: str = OLLAMA_BASE_URL, model_name: str = DEFAULT_MODEL):
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.client = httpx.Client(timeout=45.0)

    def is_available(self) -> bool:
        """Checks if local Ollama daemon is active and responsive."""
        try:
            resp = self.client.get(f"{self.base_url}/api/tags", timeout=3.0)
            return resp.status_code == 200
        except Exception:
            return False

    def generate_guarded_response(self, user_query: str, retrieved_context: str, missing_attributes: Optional[list] = None) -> Dict[str, Any]:
        """
        Runs the end-to-end guarded generation pipeline:
        1. Validates input against prompt injection.
        2. Wraps into delimited prompt boundaries.
        3. Calls local llama3.2:3b via Ollama.
        4. Validates and post-processes output constraints.
        """
        # 1. Input Guardrail
        is_safe, sanitized_query, warning = PromptGuardrail.validate_user_input(user_query)
        if not is_safe:
            return {
                "success": False,
                "blocked": True,
                "response": warning,
                "model": self.model_name
            }

        # 2. Delimited Prompt Construction
        guarded_prompt = PromptGuardrail.wrap_prompt_with_boundaries(
            system_instructions=SYSTEM_DIRECTIVE,
            retrieved_context=retrieved_context,
            sanitized_user_query=sanitized_query,
            missing_attributes=missing_attributes
        )

        # 3. Call local Ollama
        try:
            resp = self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": guarded_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2, # Low temperature for factual consistency
                        "top_p": 0.9
                    }
                }
            )
            if resp.status_code == 200:
                raw_output = resp.json().get("response", "")
                # 4. Output Guardrail
                final_output = PromptGuardrail.validate_output(raw_output)
                return {
                    "success": True,
                    "blocked": False,
                    "response": final_output.strip(),
                    "model": self.model_name,
                    "guarded_prompt": guarded_prompt,
                    "raw_output": raw_output
                }
            else:
                return {
                    "success": False,
                    "blocked": False,
                    "response": f"Ollama error (HTTP {resp.status_code}): {resp.text[:200]}",
                    "model": self.model_name,
                    "guarded_prompt": guarded_prompt,
                    "raw_output": None
                }
        except Exception as e:
            return {
                "success": False,
                "blocked": False,
                "response": f"Could not connect to Ollama: {str(e)}",
                "model": self.model_name,
                "guarded_prompt": guarded_prompt,
                "raw_output": None
            }

