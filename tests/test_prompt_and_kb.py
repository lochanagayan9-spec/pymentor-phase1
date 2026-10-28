import pytest
from app.prompt_builder import load_knowledge_base, build_system_prompt
from app.config import KNOWLEDGE_FILE

def test_knowledge_base_file_exists_and_loads():
    """Verify that knowledge.md is stored externally and loaded into memory."""
    assert KNOWLEDGE_FILE.exists(), "knowledge.md file must exist in data/ directory"
    content = load_knowledge_base()
    assert len(content) > 1000, "Knowledge base content should be substantial"
    assert "Section 1: Python Data Model" in content
    assert "LEGB Scope Resolution" in content
    assert "Mutable Default Argument" in content

def test_system_prompt_four_layers():
    """Verify that the generated system prompt covers all 4 customization layers."""
    prompt = build_system_prompt()

    # Layer 1: Persona & Role
    assert "LAYER 1: PERSONA & ROLE DEFINITION" in prompt
    assert "PyMentor" in prompt
    assert "expert senior Python software architect" in prompt

    # Layer 2: Knowledge Base
    assert "LAYER 2: DOMAIN CONTEXT & CURATED KNOWLEDGE BASE" in prompt
    assert "--- BEGIN DOMAIN KNOWLEDGE BASE ---" in prompt
    assert "--- END DOMAIN KNOWLEDGE BASE ---" in prompt

    # Layer 3: Boundaries & Rules
    assert "LAYER 3: TASK INSTRUCTIONS & BOUNDARY RULES" in prompt
    assert "STRICT DOMAIN RESTRICTION" in prompt
    assert "OUT-OF-SCOPE BEHAVIOR" in prompt
    assert "I DON'T KNOW" in prompt

    # Layer 4: Output Formatting & Constraints
    assert "LAYER 4: OUTPUT FORMATTING & PEDAGOGICAL STRUCTURE" in prompt
    assert "Quick Insight (TL;DR)" in prompt
    assert "Code Walkthrough" in prompt
    assert "Under the Hood" in prompt
    assert "Pythonic Tip" in prompt
