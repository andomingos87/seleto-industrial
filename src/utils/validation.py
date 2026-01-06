"""
Validation and normalization utilities for data inputs.

This module provides validators and normalizers for:
- Phone (E.164 format, Brazilian DDDs)
- CNPJ (14 digits with check digits validation)
- Email (lowercase, RFC 5322 basic format)
- UF (Brazilian state codes)

TECH-026: Implementar validacao e normalizacao de dados de entrada.
"""

import logging
import re

# Get logger for validation module
logger = logging.getLogger("seleto_sdr.utils.validation")


class ValidationError(Exception):
    """
    Custom exception for validation errors.

    Attributes:
        field: The field that failed validation
        value: The value that failed (may be masked for sensitive data)
        message: Human-readable error message
    """

    def __init__(self, field: str, value: str, message: str):
        self.field = field
        self.value = value
        self.message = message
        super().__init__(f"{field}: {message}")


# =============================================================================
# Brazilian State Codes (UF)
# =============================================================================

# Valid Brazilian state codes (27 states + DF)
VALID_UFS = frozenset([
    "AC",  # Acre
    "AL",  # Alagoas
    "AP",  # Amapá
    "AM",  # Amazonas
    "BA",  # Bahia
    "CE",  # Ceará
    "DF",  # Distrito Federal
    "ES",  # Espírito Santo
    "GO",  # Goiás
    "MA",  # Maranhão
    "MT",  # Mato Grosso
    "MS",  # Mato Grosso do Sul
    "MG",  # Minas Gerais
    "PA",  # Pará
    "PB",  # Paraíba
    "PR",  # Paraná
    "PE",  # Pernambuco
    "PI",  # Piauí
    "RJ",  # Rio de Janeiro
    "RN",  # Rio Grande do Norte
    "RS",  # Rio Grande do Sul
    "RO",  # Rondônia
    "RR",  # Roraima
    "SC",  # Santa Catarina
    "SP",  # São Paulo
    "SE",  # Sergipe
    "TO",  # Tocantins
])

# Valid Brazilian DDDs (area codes)
VALID_DDDS = frozenset([
    # São Paulo
    "11", "12", "13", "14", "15", "16", "17", "18", "19",
    # Rio de Janeiro / Espírito Santo
    "21", "22", "24", "27", "28",
    # Minas Gerais
    "31", "32", "33", "34", "35", "37", "38",
    # Paraná / Santa Catarina
    "41", "42", "43", "44", "45", "46", "47", "48", "49",
    # Rio Grande do Sul
    "51", "53", "54", "55",
    # Centro-Oeste (DF, GO, TO, MT, MS)
    "61", "62", "63", "64", "65", "66", "67",
    # Nordeste
    "71", "73", "74", "75", "77",  # Bahia
    "79",  # Sergipe
    "81", "82", "83", "84", "85", "86", "87", "88", "89",  # PE, AL, PB, RN, CE, PI
    # Norte
    "91", "92", "93", "94", "95", "96", "97", "98", "99",  # PA, AM, RR, AP, MA
])


# =============================================================================
# Phone Validation and Normalization
# =============================================================================

def normalize_phone(phone: str) -> str:
    """
    Normalize phone number to E.164 format (digits only).

    Args:
        phone: Phone number in any format (e.g., "+55 11 99999-9999", "(11) 99999-9999")

    Returns:
        Normalized phone number with only digits (e.g., "5511999999999")

    Examples:
        >>> normalize_phone("+55 11 99999-9999")
        '5511999999999'
        >>> normalize_phone("(11) 99999-9999")
        '11999999999'
        >>> normalize_phone("5511999999999")
        '5511999999999'
    """
    if not phone:
        return ""
    # Remove all non-digit characters
    normalized = re.sub(r"\D", "", phone)
    return normalized


def validate_phone(phone: str, strict: bool = False) -> bool:
    """
    Validate phone number format.

    Validates:
    - Minimum 10 digits (DDD + number)
    - Maximum 13 digits (country code + DDD + mobile)
    - If strict=True, also validates DDD against list of valid Brazilian DDDs

    Args:
        phone: Phone number (normalized or not)
        strict: If True, validates DDD against valid Brazilian area codes

    Returns:
        True if phone appears valid, False otherwise
    """
    normalized = normalize_phone(phone)

    # Basic validation: 10-13 digits
    if len(normalized) < 10 or len(normalized) > 13:
        if normalized:  # Only log if there was actually a value
            logger.debug(
                "Phone validation failed: invalid length",
                extra={"phone_length": len(normalized), "expected": "10-13"}
            )
        return False

    if strict:
        # Extract DDD based on phone length
        if len(normalized) >= 12:  # Has country code (55)
            ddd = normalized[2:4]
        else:
            ddd = normalized[0:2]

        if ddd not in VALID_DDDS:
            logger.debug(
                "Phone validation failed: invalid DDD",
                extra={"ddd": ddd, "valid_ddds_sample": list(VALID_DDDS)[:5]}
            )
            return False

    return True


def validate_phone_strict(phone: str) -> bool:
    """
    Validate phone number with strict DDD validation.

    Convenience function that calls validate_phone with strict=True.

    Args:
        phone: Phone number (normalized or not)

    Returns:
        True if phone is valid with a valid Brazilian DDD
    """
    return validate_phone(phone, strict=True)


# =============================================================================
# CNPJ Validation and Normalization
# =============================================================================

def normalize_cnpj(cnpj: str) -> str:
    """
    Normalize CNPJ to 14 digits (remove punctuation).

    Args:
        cnpj: CNPJ in any format (e.g., "12.345.678/0001-90", "12345678000190")

    Returns:
        Normalized CNPJ with only digits (e.g., "12345678000190")
    """
    if not cnpj:
        return ""
    # Remove all non-digit characters
    normalized = re.sub(r"\D", "", cnpj)
    return normalized


def _calculate_cnpj_check_digit(cnpj_base: str, weights: list[int]) -> int:
    """
    Calculate a CNPJ check digit.

    Args:
        cnpj_base: The CNPJ digits to calculate from
        weights: The weights to apply to each digit

    Returns:
        The calculated check digit (0-9)
    """
    total = sum(int(digit) * weight for digit, weight in zip(cnpj_base, weights, strict=True))
    remainder = total % 11
    return 0 if remainder < 2 else 11 - remainder


def validate_cnpj(cnpj: str) -> bool:
    """
    Validate CNPJ format and check digits.

    Validates:
    - Exactly 14 digits after normalization
    - Not all digits are the same (e.g., 11111111111111)
    - Valid check digits (dígitos verificadores)

    Args:
        cnpj: CNPJ in any format

    Returns:
        True if CNPJ is valid, False otherwise
    """
    normalized = normalize_cnpj(cnpj)

    # Must have exactly 14 digits
    if len(normalized) != 14:
        if normalized:
            logger.debug(
                "CNPJ validation failed: invalid length",
                extra={"cnpj_length": len(normalized), "expected": 14}
            )
        return False

    # Reject CNPJs with all same digits (e.g., 11111111111111)
    if len(set(normalized)) == 1:
        logger.debug(
            "CNPJ validation failed: all digits are the same",
            extra={"cnpj_masked": f"{normalized[:2]}...{normalized[-2:]}"}
        )
        return False

    # Validate check digits
    # First check digit: weights 5,4,3,2,9,8,7,6,5,4,3,2 for first 12 digits
    weights_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    expected_digit_1 = _calculate_cnpj_check_digit(normalized[:12], weights_1)

    if int(normalized[12]) != expected_digit_1:
        logger.debug(
            "CNPJ validation failed: first check digit invalid",
            extra={"cnpj_masked": f"{normalized[:2]}...{normalized[-2:]}"}
        )
        return False

    # Second check digit: weights 6,5,4,3,2,9,8,7,6,5,4,3,2 for first 13 digits
    weights_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    expected_digit_2 = _calculate_cnpj_check_digit(normalized[:13], weights_2)

    if int(normalized[13]) != expected_digit_2:
        logger.debug(
            "CNPJ validation failed: second check digit invalid",
            extra={"cnpj_masked": f"{normalized[:2]}...{normalized[-2:]}"}
        )
        return False

    return True


# =============================================================================
# Email Validation and Normalization
# =============================================================================

def normalize_email(email: str) -> str:
    """
    Normalize email to lowercase and strip whitespace.

    Args:
        email: Email address

    Returns:
        Lowercase email address with whitespace stripped
    """
    if not email:
        return ""
    return email.lower().strip()


def validate_email(email: str) -> bool:
    """
    Validate email format (basic regex check).

    Normalizes the email (strips whitespace, lowercase) before validation.

    Args:
        email: Email address to validate

    Returns:
        True if email format appears valid, False otherwise
    """
    if not email:
        return False

    # Normalize before validation
    normalized = normalize_email(email)

    if not normalized:
        return False

    # Basic email regex (RFC 5322 simplified)
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    is_valid = bool(re.match(pattern, normalized))

    if not is_valid:
        logger.debug(
            "Email validation failed: invalid format",
            extra={"email_domain": normalized.split("@")[-1] if "@" in normalized else "unknown"}
        )

    return is_valid


# =============================================================================
# UF (State Code) Validation and Normalization
# =============================================================================

def normalize_uf(uf: str) -> str:
    """
    Normalize UF to uppercase.

    Args:
        uf: State code

    Returns:
        Uppercase UF (2 letters)
    """
    if not uf:
        return ""
    normalized = uf.upper().strip()
    # Take only first 2 characters if longer
    return normalized[:2] if len(normalized) >= 2 else normalized


def validate_uf(uf: str, strict: bool = True) -> bool:
    """
    Validate UF (state code) format.

    Args:
        uf: State code (should be 2 uppercase letters)
        strict: If True, validates against list of valid Brazilian states

    Returns:
        True if UF is valid, False otherwise
    """
    if not uf:
        return False

    normalized = normalize_uf(uf)

    # Must be exactly 2 uppercase letters
    if not re.match(r"^[A-Z]{2}$", normalized):
        logger.debug(
            "UF validation failed: not 2 uppercase letters",
            extra={"uf": uf}
        )
        return False

    if strict:
        if normalized not in VALID_UFS:
            logger.debug(
                "UF validation failed: not a valid Brazilian state",
                extra={"uf": normalized, "valid_ufs": list(VALID_UFS)}
            )
            return False

    return True


def validate_uf_strict(uf: str) -> bool:
    """
    Validate UF against list of valid Brazilian states.

    Convenience function that calls validate_uf with strict=True.

    Args:
        uf: State code

    Returns:
        True if UF is a valid Brazilian state code
    """
    return validate_uf(uf, strict=True)


# =============================================================================
# Validation with Exception Raising
# =============================================================================

def validate_phone_or_raise(phone: str, strict: bool = False) -> str:
    """
    Validate and normalize phone, raising ValidationError if invalid.

    Args:
        phone: Phone number to validate
        strict: If True, validates DDD against valid Brazilian area codes

    Returns:
        Normalized phone number

    Raises:
        ValidationError: If phone is invalid
    """
    normalized = normalize_phone(phone)
    if not validate_phone(normalized, strict=strict):
        raise ValidationError(
            field="phone",
            value=f"{normalized[:4]}...{normalized[-2:]}" if len(normalized) > 6 else normalized,
            message="Invalid phone number format"
        )
    return normalized


def validate_cnpj_or_raise(cnpj: str) -> str:
    """
    Validate and normalize CNPJ, raising ValidationError if invalid.

    Args:
        cnpj: CNPJ to validate

    Returns:
        Normalized CNPJ (14 digits)

    Raises:
        ValidationError: If CNPJ is invalid
    """
    normalized = normalize_cnpj(cnpj)
    if not validate_cnpj(normalized):
        raise ValidationError(
            field="cnpj",
            value=f"{normalized[:2]}...{normalized[-2:]}" if len(normalized) > 4 else normalized,
            message="Invalid CNPJ (check digits failed or invalid format)"
        )
    return normalized


def validate_email_or_raise(email: str) -> str:
    """
    Validate and normalize email, raising ValidationError if invalid.

    Args:
        email: Email to validate

    Returns:
        Normalized email (lowercase, stripped)

    Raises:
        ValidationError: If email is invalid
    """
    normalized = normalize_email(email)
    if not validate_email(normalized):
        raise ValidationError(
            field="email",
            value=f"***@{normalized.split('@')[-1]}" if "@" in normalized else "***",
            message="Invalid email format"
        )
    return normalized


def validate_uf_or_raise(uf: str, strict: bool = True) -> str:
    """
    Validate and normalize UF, raising ValidationError if invalid.

    Args:
        uf: State code to validate
        strict: If True, validates against valid Brazilian states

    Returns:
        Normalized UF (uppercase, 2 letters)

    Raises:
        ValidationError: If UF is invalid
    """
    normalized = normalize_uf(uf)
    if not validate_uf(normalized, strict=strict):
        raise ValidationError(
            field="uf",
            value=normalized,
            message="Invalid UF (not a valid Brazilian state code)"
        )
    return normalized
