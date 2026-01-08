"""
Knowledge Base Service - US-003: Responder dúvidas usando base de conhecimento.

This module provides functionality to:
- Load equipment knowledge files from prompts/equipamentos/*
- Search the knowledge base for relevant information
- Detect overly technical questions requiring human specialist
- Apply commercial guardrails (no prices, discounts, delivery times)
- Register technical questions for follow-up contact
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class EquipmentInfo:
    """Information about a specific equipment."""

    name: str
    category: str
    description: str
    specifications: list[str] = field(default_factory=list)
    productivity: str | None = None


@dataclass
class TechnicalQuestion:
    """A technical question registered for human follow-up."""

    phone: str
    question: str
    timestamp: str
    context: str | None = None


# In-memory storage for technical questions (can be moved to Supabase later)
_technical_questions: list[TechnicalQuestion] = []


class KnowledgeBase:
    """
    Knowledge Base for Seleto Industrial equipment.

    Loads and manages equipment information from prompts/equipamentos/*
    and provides search capabilities with commercial guardrails.
    """

    # Keywords that indicate commercial/pricing queries (guardrails)
    COMMERCIAL_KEYWORDS = [
        "preço",
        "preco",
        "valor",
        "custo",
        "quanto custa",
        "quanto é",
        "quanto e",
        "orçamento",
        "orcamento",
        "desconto",
        "promoção",
        "promocao",
        "condição de pagamento",
        "condicao de pagamento",
        "condições de pagamento",
        "condicoes de pagamento",
        "parcelamento",
        "parcela",
        "financiamento",
        "prazo de entrega",
        "prazo entrega",
        "quando entrega",
        "tempo de entrega",
        "frete",
        "como comprar",
        "quero comprar",
        "compra",
        "proposta",
        "negociar",
        "negociação",
        "negociacao",
    ]

    # Keywords that indicate overly technical questions
    TECHNICAL_KEYWORDS = [
        # Engineering specifics
        "diagrama elétrico",
        "diagrama eletrico",
        "esquema elétrico",
        "esquema eletrico",
        "circuito",
        "voltagem",
        "amperagem",
        "especificação técnica detalhada",
        "especificacao tecnica detalhada",
        "desenho técnico",
        "desenho tecnico",
        "planta",
        "projeto",
        # Maintenance/repair specifics
        "peça de reposição",
        "peca de reposicao",
        "peça de substituição",
        "peca de substituicao",
        "manutenção preventiva",
        "manutencao preventiva",
        "manutenção corretiva",
        "manutencao corretiva",
        "calibração",
        "calibracao",
        "ajuste técnico",
        "ajuste tecnico",
        "reparo",
        "conserto",
        "defeito",
        "problema técnico",
        "problema tecnico",
        "não funciona",
        "nao funciona",
        "travou",
        "parou",
        "quebrou",
        # Installation specifics
        "instalação elétrica",
        "instalacao eletrica",
        "instalação hidráulica",
        "instalacao hidraulica",
        "instalação pneumática",
        "instalacao pneumatica",
        "ponto de energia",
        "compressor",
        "pressão de ar",
        "pressao de ar",
        # Integration/customization
        "integração com",
        "integracao com",
        "integrar com",
        "customização",
        "customizacao",
        "customizar",
        "personalização",
        "personalizacao",
        "personalizar",
        "adaptar",
        "modificar estrutura",
        # Certifications/regulations
        "certificação",
        "certificacao",
        "norma técnica",
        "norma tecnica",
        "anvisa",
        "inmetro",
        "laudo",
    ]

    # Equipment categories for search
    EQUIPMENT_CATEGORIES = {
        "formadora": ["formadora", "hambúrguer", "hamburguer", "hamburgueres", "fbm", "fb300", "fb700", "se3000", "se6000", "smartpro"],
        "cortadora": ["cortadora", "corte", "bife", "cubo", "tira", "ct200", "filetadora", "fs150", "filé", "file"],
        "ensacadeira": ["ensacadeira", "linguiça", "linguica", "embutido"],
        "misturador": ["misturador", "homogeneizador", "mistura"],
        "linha_automatica": ["linha automática", "linha automatica", "epe1200", "espeto"],
    }

    def __init__(self):
        """Initialize the knowledge base."""
        self._knowledge_content: str = ""
        self._equipment_list: list[EquipmentInfo] = []
        self._loaded: bool = False

    def load_equipment_files(self) -> None:
        """
        Load all equipment files from prompts/equipamentos/*.

        Reads prompt_manus.txt and resumo_maquinas.txt and combines them
        into a searchable knowledge base.
        """
        if self._loaded:
            logger.debug("Knowledge base already loaded, skipping reload")
            return

        base_path = Path(__file__).parent.parent.parent
        equipment_dir = base_path / "prompts" / "equipamentos"

        if not equipment_dir.exists():
            logger.warning(f"Equipment directory not found: {equipment_dir}")
            return

        content_parts = []
        files_loaded = 0

        # Load all .txt files in the equipment directory
        for txt_file in sorted(equipment_dir.glob("*.txt")):
            try:
                file_content = txt_file.read_text(encoding="utf-8")
                content_parts.append(f"=== {txt_file.name} ===\n{file_content}")
                files_loaded += 1
                logger.info(f"Loaded equipment file: {txt_file.name}", extra={"size": len(file_content)})
            except Exception:
                logger.error(f"Failed to load equipment file: {txt_file}", exc_info=True)

        self._knowledge_content = "\n\n".join(content_parts)
        self._parse_equipment_info()
        self._loaded = True

        logger.info(
            "Knowledge base loaded successfully",
            extra={
                "files_loaded": files_loaded,
                "total_content_size": len(self._knowledge_content),
                "equipment_count": len(self._equipment_list),
            },
        )

    def _parse_equipment_info(self) -> None:
        """Parse equipment information from loaded content."""
        # Extract equipment names and basic info using patterns
        equipment_patterns = [
            # Formadoras
            (r"Formadora Manual FBM100", "Formadora", "formadora"),
            (r"Formadora Semi Automática FB300|Formadora semi automática FB300", "Formadora", "formadora"),
            (r"Formadora Automática FB700|Formadora automática FB700", "Formadora", "formadora"),
            (r"Formadora SE SmartPro", "Formadora", "formadora"),
            (r"Formadora Automática SE3000", "Formadora", "formadora"),
            (r"Formadora Automática SE6000", "Formadora", "formadora"),
            # Cortadoras
            (r"Cortadora CT200", "Cortadora", "cortadora"),
            (r"Filetadora Automática FS150", "Filetadora", "cortadora"),
            # Outros
            (r"Ensacadeira elétrica|Ensacadeira", "Ensacadeira", "ensacadeira"),
            (r"Misturadores e Homogeneizadores|Misturador", "Misturador", "misturador"),
            (r"Linha Automática EPE1200", "Linha Automática", "linha_automatica"),
            (r"Linha Automática \+ FB700", "Linha Automática", "linha_automatica"),
            (r"Linha automática para Espeto", "Linha Automática", "linha_automatica"),
        ]

        for pattern, category, _category_key in equipment_patterns:
            if re.search(pattern, self._knowledge_content, re.IGNORECASE):
                match = re.search(pattern, self._knowledge_content, re.IGNORECASE)
                if match:
                    self._equipment_list.append(
                        EquipmentInfo(
                            name=match.group(0),
                            category=category,
                            description="",  # Could be enhanced to extract description
                        )
                    )

    def search_knowledge_base(self, query: str) -> str:
        """
        Search the knowledge base for information relevant to the query.

        Args:
            query: User's question or search term

        Returns:
            Relevant knowledge content or empty string if not found
        """
        if not self._loaded:
            self.load_equipment_files()

        if not self._knowledge_content:
            return ""

        query_lower = query.lower()
        relevant_sections = []

        # Determine which category the query relates to
        matched_categories = []
        for category, keywords in self.EQUIPMENT_CATEGORIES.items():
            if any(kw in query_lower for kw in keywords):
                matched_categories.append(category)

        # If no specific category matched, search all content
        if not matched_categories:
            # Return general equipment overview
            return self._get_general_overview()

        # Extract relevant sections based on matched categories
        for category in matched_categories:
            section = self._extract_category_content(category)
            if section:
                relevant_sections.append(section)

        return "\n\n".join(relevant_sections) if relevant_sections else self._get_general_overview()

    def _extract_category_content(self, category: str) -> str:
        """Extract content related to a specific equipment category."""
        content_lines = self._knowledge_content.split("\n")
        relevant_lines = []
        in_relevant_section = False
        section_start_patterns = {
            "formadora": [r"Formadora", r"FBM100", r"FB300", r"FB700", r"SmartPro", r"SE3000", r"SE6000"],
            "cortadora": [r"Cortadora", r"CT200", r"Filetadora", r"FS150"],
            "ensacadeira": [r"Ensacadeira"],
            "misturador": [r"Misturador", r"Homogeneizador"],
            "linha_automatica": [r"Linha Automática", r"Linha automatica", r"EPE1200", r"Espeto"],
        }

        patterns = section_start_patterns.get(category, [])

        for line in content_lines:
            # Check if line starts a relevant section
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in patterns):
                in_relevant_section = True
                relevant_lines.append(line)
            elif in_relevant_section:
                # Check if we're starting a new equipment section (ends current)
                if line.strip().startswith("-") and len(line.strip()) > 2:
                    # Check if this is a new equipment that doesn't match our category
                    is_new_section = any(
                        re.search(pattern, line, re.IGNORECASE)
                        for cat, pats in section_start_patterns.items()
                        if cat != category
                        for pattern in pats
                    )
                    if is_new_section:
                        in_relevant_section = False
                        continue
                relevant_lines.append(line)
            elif not in_relevant_section and len(relevant_lines) > 20:
                # Limit section size
                break

        return "\n".join(relevant_lines[:50])  # Limit to 50 lines per category

    def _get_general_overview(self) -> str:
        """Get a general overview of available equipment."""
        return """A Seleto Industrial oferece os seguintes equipamentos:

**Formadoras de Hambúrguer:**
- FBM100 (Manual): 500-600 hambúrgueres/dia, cuba de 1,5kg
- FB300 (Semi Automática): 300-350 hambúrgueres/hora, reservatório de 5kg
- FB700 (Automática): 700 hambúrgueres/hora, reservatório de 10-12kg
- SE SmartPro: até 1.800 ciclos/hora, 100% elétrica
- SE3000: até 3.000 hambúrgueres/hora, industrial
- SE6000: até 6.000 hambúrgueres/hora, alta escala

**Cortadoras:**
- CT200: até 300kg/hora para bifes, cubos e tiras
- Filetadora FS150: cortes de 7 a 14mm

**Ensacadeiras:**
- Capacidades de 15kg e 30kg para linguiças

**Misturadores:**
- Capacidades de 25L a 210L

**Linhas Automáticas:**
- EPE1200: até 1.400 hambúrgueres/hora
- Linha para Espeto: 1.200 a 2.400 espetos/hora"""

    def is_commercial_query(self, query: str) -> bool:
        """
        Check if the query is asking about commercial information.

        Commercial queries include: prices, discounts, delivery times,
        payment conditions, etc.

        Args:
            query: User's message

        Returns:
            True if the query is commercial in nature
        """
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in self.COMMERCIAL_KEYWORDS)

    def is_too_technical(self, query: str) -> bool:
        """
        Check if the query is too technical for the AI agent.

        Technical queries requiring human specialist include:
        - Electrical diagrams/schematics
        - Maintenance/repair specifics
        - Custom installations
        - Certifications/regulations

        Args:
            query: User's message

        Returns:
            True if the query requires a human specialist
        """
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in self.TECHNICAL_KEYWORDS)

    def is_equipment_query(self, query: str) -> bool:
        """
        Check if the query is about equipment/products.

        Args:
            query: User's message

        Returns:
            True if the query is asking about equipment
        """
        query_lower = query.lower()

        # Check for equipment category keywords
        all_keywords = []
        for keywords in self.EQUIPMENT_CATEGORIES.values():
            all_keywords.extend(keywords)

        # Add general equipment terms
        general_terms = [
            "equipamento",
            "máquina",
            "maquina",
            "produto",
            "modelo",
            "produção",
            "producao",
            "produtividade",
            "capacidade",
            "especificação",
            "especificacao",
        ]
        all_keywords.extend(general_terms)

        return any(keyword in query_lower for keyword in all_keywords)

    def get_commercial_response(self) -> str:
        """
        Get the standard response for commercial queries.

        Returns:
            Response declining to provide commercial information
        """
        return (
            "Entendo que você gostaria de informações sobre valores e condições comerciais. "
            "Para garantir o melhor atendimento, um de nossos consultores de vendas entrará em contato "
            "para apresentar uma proposta personalizada para sua necessidade. "
            "Posso ajudar com mais alguma dúvida sobre as características técnicas dos equipamentos?"
        )

    def get_technical_escalation_response(self) -> str:
        """
        Get the response for overly technical queries.

        Returns:
            Response informing that a specialist will contact the user
        """
        return (
            "Essa é uma excelente pergunta técnica que requer a avaliação de um de nossos especialistas. "
            "Vou registrar sua dúvida e um técnico especializado entrará em contato em breve para ajudá-lo "
            "com todas as informações detalhadas. "
            "Enquanto isso, posso ajudar com outras dúvidas sobre nossos equipamentos?"
        )

    def register_technical_question(self, phone: str, question: str, context: str | None = None) -> None:
        """
        Register a technical question for human follow-up.

        Persists to database if available, falls back to in-memory storage.

        Args:
            phone: Customer's phone number
            question: The technical question asked
            context: Optional conversation context
        """
        from datetime import datetime

        from src.services.conversation_persistence import get_supabase_client

        # Try to persist to database
        client = get_supabase_client()
        if client:
            try:
                client.table("technical_questions").insert({
                    "phone": phone,
                    "question": question,
                    "context": context,
                }).execute()
                logger.info(
                    "Technical question registered in database",
                    extra={
                        "phone": phone,
                        "question_preview": question[:100] if len(question) > 100 else question,
                    },
                )
                return
            except Exception as e:
                logger.warning(
                    "Failed to persist technical question to database, using in-memory fallback",
                    extra={"error": str(e)},
                )

        # Fallback to in-memory storage
        technical_question = TechnicalQuestion(
            phone=phone,
            question=question,
            timestamp=datetime.now().isoformat(),
            context=context,
        )

        _technical_questions.append(technical_question)

        logger.info(
            "Technical question registered in memory",
            extra={
                "phone": phone,
                "question_preview": question[:100] if len(question) > 100 else question,
            },
        )

    def get_pending_technical_questions(self) -> list[TechnicalQuestion]:
        """
        Get all pending technical questions.

        Returns:
            List of technical questions awaiting follow-up
        """
        return _technical_questions.copy()

    def clear_technical_question(self, phone: str) -> None:
        """
        Clear technical questions for a specific phone number.

        Args:
            phone: Customer's phone number
        """
        global _technical_questions
        _technical_questions = [q for q in _technical_questions if q.phone != phone]

    def get_equipment_response(self, query: str) -> tuple[str, str]:
        """
        Get appropriate response for an equipment query with guardrails.

        This is the main method for processing equipment-related queries.
        It applies all guardrails and returns the appropriate response.

        Args:
            query: User's question

        Returns:
            Tuple of (response_type, response_content)
            response_type: "commercial", "technical", "knowledge", or "general"
        """
        # Check commercial guardrail first
        if self.is_commercial_query(query):
            return ("commercial", self.get_commercial_response())

        # Check if too technical
        if self.is_too_technical(query):
            return ("technical", self.get_technical_escalation_response())

        # Check if it's an equipment query
        if self.is_equipment_query(query):
            knowledge = self.search_knowledge_base(query)
            if knowledge:
                return ("knowledge", knowledge)

        # General query - return overview
        return ("general", self._get_general_overview())


# Singleton instance
_knowledge_base: KnowledgeBase | None = None


def get_knowledge_base() -> KnowledgeBase:
    """
    Get the singleton KnowledgeBase instance.

    Returns:
        KnowledgeBase instance
    """
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = KnowledgeBase()
        _knowledge_base.load_equipment_files()
    return _knowledge_base


def search_knowledge(query: str) -> str:
    """
    Convenience function to search the knowledge base.

    Args:
        query: Search query

    Returns:
        Relevant knowledge content
    """
    kb = get_knowledge_base()
    return kb.search_knowledge_base(query)


def is_commercial_query(query: str) -> bool:
    """
    Convenience function to check if query is commercial.

    Args:
        query: User's message

    Returns:
        True if query is about commercial matters
    """
    kb = get_knowledge_base()
    return kb.is_commercial_query(query)


def is_too_technical(query: str) -> bool:
    """
    Convenience function to check if query is too technical.

    Args:
        query: User's message

    Returns:
        True if query requires human specialist
    """
    kb = get_knowledge_base()
    return kb.is_too_technical(query)


def register_technical_question(phone: str, question: str, context: str | None = None) -> None:
    """
    Convenience function to register a technical question.

    Args:
        phone: Customer's phone number
        question: The technical question
        context: Optional conversation context
    """
    kb = get_knowledge_base()
    kb.register_technical_question(phone, question, context)
