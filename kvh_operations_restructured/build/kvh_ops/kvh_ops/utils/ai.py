"""
AI integration utilities for KVH Operations.
Provides OpenAI-compatible lead summary generation.
Mirrors the AI SDK usage in the Lovable frontend.
"""

import frappe
from frappe import _


def generate_lead_summary(lead_doc) -> str:
    """
    Generate an AI summary for a lead using configured OpenAI-compatible API.
    Mirrors: ai_summary field population in the Lovable system.

    Args:
        lead_doc: Frappe CRM Lead document

    Returns:
        str: AI-generated summary text
    """
    api_key = frappe.db.get_single_value("KVH Settings", "openai_api_key") or ""
    api_base = frappe.db.get_single_value("KVH Settings", "openai_api_base") or "https://api.openai.com/v1"
    model = frappe.db.get_single_value("KVH Settings", "ai_model") or "gpt-4o-mini"

    if not api_key:
        frappe.throw(_("OpenAI API key not configured. Please set it in KVH Settings."))

    # Build context from lead data
    context_parts = []
    if lead_doc.lead_name:
        context_parts.append(f"Name: {lead_doc.lead_name}")
    if lead_doc.mobile_no:
        context_parts.append(f"Phone: {lead_doc.mobile_no}")
    if lead_doc.source:
        context_parts.append(f"Source: {lead_doc.source}")
    if lead_doc.lead_stage:
        context_parts.append(f"Stage: {lead_doc.lead_stage}")
    if lead_doc.get("place"):
        context_parts.append(f"Location: {lead_doc.get('place')}")
    if lead_doc.notes:
        context_parts.append(f"Notes: {lead_doc.notes}")

    context = "\n".join(context_parts)
    prompt = (
        f"Summarize the following sales lead in 2-3 concise sentences, "
        f"highlighting the key information and next steps:\n\n{context}"
    )

    try:
        import openai
        client = openai.OpenAI(api_key=api_key, base_url=api_base)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful sales assistant that summarizes lead information concisely."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=150,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()

    except ImportError:
        frappe.throw(_("OpenAI package not installed. Run: pip install openai"))
    except Exception as e:
        frappe.log_error(f"AI summary generation error: {e}", "KVH AI")
        raise
