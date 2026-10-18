from typing import Dict
import os

# Versioned prompt templates
# Each template includes few-shot examples as per requirements
PROMPTS = {
    "clause_analysis": {
        "template": "Analyze the following legal clause and explain its meaning in plain language. Separate explicit statements from interpretations.\n\nClause: {clause}\n\nAnalysis:",
        "system": "You are a legal document triage assistant. You do NOT provide legal advice. You explain what the document says. If the document is silent on a point, say 'document is silent'.",
        "few_shot": [
            {"input": "Tenant shall pay rent on the 1st of each month.", "output": "Explicit: Rent is due on the 1st. Interpretation: The tenant is responsible for timely payment to avoid late fees."},
            {"input": "The parties may agree to modify this in writing.", "output": "Explicit: Modifications must be written. Interpretation: Verbal agreements to change terms are likely not binding."}
        ]
    },
    "risk_detection": {
        "template": "Identify any 'red flag' language or unfavorable terms in the following text. Be objective.\n\nText: {text}\n\nRisks:",
        "system": "You are a risk detection agent. Identify unfavorable terms without giving legal verdicts like 'illegal'.",
        "few_shot": [
            {"input": "Landlord may enter premises at any time without notice.", "output": "Red Flag: Lack of notice for entry may violate privacy expectations."},
            {"input": "This agreement is governed by the laws of the Galactic Empire.", "output": "Risk: Unfamiliar or non-standard jurisdiction."}
        ]
    },
    "classify_label": {
        "template": "Classify the following document into one of these categories: [rental, employment, legal_notice, service_agreement, non_legal].\n\nDocument text: {text}\n\nCategory:",
        "system": "You are a document classifier. Only output the category label.",
        "few_shot": [
            {"input": "This lease agreement is between...", "output": "rental"},
            {"input": "I am writing to notify you that your employment...", "output": "employment"},
            {"input": "The weather is nice today.", "output": "non_legal"}
        ]
    }
}

def get_prompt(key: str, **kwargs) -> str:
    template = PROMPTS.get(key, {}).get("template", "")
    return template.format(**kwargs)

def get_system_prompt(key: str) -> str:
    return PROMPTS.get(key, {}).get("system", "")
