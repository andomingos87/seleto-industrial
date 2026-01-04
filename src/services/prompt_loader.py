"""
Service for loading and parsing system prompts from XML files.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from src.utils.logging import get_logger

logger = get_logger(__name__)


def load_system_prompt_from_xml(xml_path: str | Path) -> str:
    """
    Load and parse system prompt from XML file.

    Converts the structured XML into a readable text format for the LLM.

    Args:
        xml_path: Path to the XML file containing the system prompt

    Returns:
        Formatted system prompt as a string

    Raises:
        FileNotFoundError: If the XML file doesn't exist
        ET.ParseError: If the XML is malformed
    """
    xml_path = Path(xml_path)
    if not xml_path.exists():
        raise FileNotFoundError(f"System prompt XML file not found: {xml_path}")

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Extract and format the prompt
        prompt_parts = []

        # Role section
        role = root.find("role")
        if role is not None:
            identity = role.find("identity")
            mission = role.find("mission")
            company_context = role.find("company_context")

            if identity is not None and identity.text:
                prompt_parts.append(f"IDENTIDADE: {identity.text.strip()}")
            if mission is not None and mission.text:
                prompt_parts.append(f"\nMISSÃO: {mission.text.strip()}")
            if company_context is not None and company_context.text:
                prompt_parts.append(f"\nCONTEXTO DA EMPRESA: {company_context.text.strip()}")

        # Rules section
        rules = root.find("rules")
        if rules is not None:
            prompt_parts.append("\n\n=== REGRAS DE COMPORTAMENTO ===")

            tone = rules.find("tone")
            if tone is not None:
                guidelines = tone.find("guidelines")
                if guidelines is not None:
                    items = guidelines.findall("item")
                    if items:
                        prompt_parts.append("\nTOM E ESTILO:")
                        for item in items:
                            if item.text:
                                prompt_parts.append(f"- {item.text.strip()}")

            conversation_flow = rules.find("conversation_flow")
            if conversation_flow is not None:
                guidelines = conversation_flow.find("guidelines")
                if guidelines is not None:
                    items = guidelines.findall("item")
                    if items:
                        prompt_parts.append("\nFLUXO DE CONVERSA:")
                        for item in items:
                            if item.text:
                                prompt_parts.append(f"- {item.text.strip()}")

            limits = rules.find("limits")
            if limits is not None:
                restrictions = limits.find("restrictions")
                if restrictions is not None:
                    items = restrictions.findall("item")
                    if items:
                        prompt_parts.append("\nLIMITAÇÕES:")
                        for item in items:
                            if item.text:
                                prompt_parts.append(f"- {item.text.strip()}")

            behavior = rules.find("behavior")
            if behavior is not None:
                guidelines = behavior.find("guidelines")
                if guidelines is not None:
                    items = guidelines.findall("item")
                    if items:
                        prompt_parts.append("\nCOMPORTAMENTO:")
                        for item in items:
                            if item.text:
                                prompt_parts.append(f"- {item.text.strip()}")

        # Objectives section
        objectives = root.find("objectives")
        if objectives is not None:
            prompt_parts.append("\n\n=== OBJETIVOS ===")

            primary = objectives.find("primary")
            if primary is not None:
                items = primary.findall("item")
                if items:
                    prompt_parts.append("\nOBJETIVOS PRIMÁRIOS:")
                    for item in items:
                        if item.text:
                            prompt_parts.append(f"- {item.text.strip()}")

            data_collection = objectives.find("data_collection")
            if data_collection is not None:
                description = data_collection.find("description")
                if description is not None and description.text:
                    prompt_parts.append(f"\n{description.text.strip()}")
                fields = data_collection.find("fields")
                if fields is not None:
                    field_items = fields.findall("field")
                    if field_items:
                        prompt_parts.append("Dados a coletar:")
                        for field in field_items:
                            if field.text:
                                prompt_parts.append(f"- {field.text.strip()}")

        # Conversation guidelines
        conversation_guidelines = root.find("conversation_guidelines")
        if conversation_guidelines is not None:
            prompt_parts.append("\n\n=== DIRETRIZES DE CONVERSA ===")

            opening = conversation_guidelines.find("opening")
            if opening is not None:
                description = opening.find("description")
                example = opening.find("example")
                if description is not None and description.text:
                    prompt_parts.append(f"\n{description.text.strip()}")
                if example is not None:
                    text_elem = example.find("text")
                    if text_elem is not None and text_elem.text:
                        prompt_parts.append("\nExemplo de abertura:")
                        prompt_parts.append(text_elem.text.strip())

            flow_techniques = conversation_guidelines.find("flow_techniques")
            if flow_techniques is not None:
                items = flow_techniques.findall("item")
                if items:
                    prompt_parts.append("\nTÉCNICAS DE FLUXO:")
                    for item in items:
                        if item.text:
                            prompt_parts.append(f"- {item.text.strip()}")

        # Technical knowledge
        technical_knowledge = root.find("technical_knowledge")
        if technical_knowledge is not None:
            prompt_parts.append("\n\n=== CONHECIMENTO TÉCNICO ===")
            prompt_parts.append(
                "Use as informações abaixo para responder dúvidas sobre produtos:\n"
            )

            # Products
            products = technical_knowledge.findall("product")
            for product in products:
                name = product.get("name", "")
                description = product.find("description")
                specifications = product.find("specifications")

                if name:
                    prompt_parts.append(f"\n{name}:")
                if description is not None and description.text:
                    prompt_parts.append(description.text.strip())
                if specifications is not None:
                    specs = specifications.findall("spec")
                    for spec in specs:
                        if spec.text:
                            prompt_parts.append(f"  - {spec.text.strip()}")

            # Product categories
            categories = technical_knowledge.findall("product_category")
            for category in categories:
                name = category.get("name", "")
                description = category.find("description")
                specifications = category.find("specifications")
                products_in_category = category.find("products")

                if name:
                    prompt_parts.append(f"\n{name}:")
                if description is not None and description.text:
                    prompt_parts.append(description.text.strip())
                if specifications is not None:
                    specs = specifications.findall("spec")
                    for spec in specs:
                        if spec.text:
                            prompt_parts.append(f"  - {spec.text.strip()}")
                if products_in_category is not None:
                    products_list = products_in_category.findall("product")
                    for product in products_list:
                        name = product.get("name", "")
                        product_type = product.find("type")
                        capacity = product.find("capacity")
                        if name:
                            prompt_parts.append(f"  {name}:")
                        if product_type is not None and product_type.text:
                            prompt_parts.append(f"    Tipo: {product_type.text.strip()}")
                        if capacity is not None and capacity.text:
                            prompt_parts.append(f"    Capacidade: {capacity.text.strip()}")

        # Final mission
        final_mission = root.find("final_mission")
        if final_mission is not None:
            statement = final_mission.find("statement")
            if statement is not None and statement.text:
                prompt_parts.append("\n\n=== MISSÃO FINAL ===")
                prompt_parts.append(statement.text.strip())

        # Join all parts
        full_prompt = "\n".join(prompt_parts)

        logger.info(
            f"System prompt loaded from {xml_path}",
            extra={"prompt_length": len(full_prompt)},
        )

        return full_prompt

    except ET.ParseError as e:
        logger.error(f"Failed to parse XML file: {xml_path}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error loading system prompt: {xml_path}", exc_info=True)
        raise


def get_system_prompt_path(prompt_name: str = "sp_agente_v1.xml") -> Path:
    """
    Get the path to a system prompt file.

    Args:
        prompt_name: Name of the prompt file (default: sp_agente_v1.xml)

    Returns:
        Path to the prompt file
    """
    # Assume prompts are in prompts/system_prompt/ directory
    base_path = Path(__file__).parent.parent.parent
    prompt_path = base_path / "prompts" / "system_prompt" / prompt_name
    return prompt_path

