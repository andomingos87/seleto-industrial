"""
Validation and normalization utilities for data inputs.
"""

import re
from typing import Optional


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


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format (basic check).

    Args:
        phone: Phone number (normalized or not)

    Returns:
        True if phone appears valid (has at least 10 digits), False otherwise
    """
    normalized = normalize_phone(phone)
    # Basic validation: at least 10 digits (DDD + number)
    return len(normalized) >= 10


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


def validate_email(email: str) -> bool:
    """
    Validate email format (basic regex check).

    Args:
        email: Email address to validate

    Returns:
        True if email format appears valid, False otherwise
    """
    if not email:
        return False
    # Basic email regex
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def normalize_email(email: str) -> str:
    """
    Normalize email to lowercase.

    Args:
        email: Email address

    Returns:
        Lowercase email address
    """
    if not email:
        return ""
    return email.lower().strip()


def validate_uf(uf: str) -> bool:
    """
    Validate UF (state code) format.

    Args:
        uf: State code (should be 2 uppercase letters)

    Returns:
        True if UF is 2 uppercase letters, False otherwise
    """
    if not uf:
        return False
    # Should be exactly 2 uppercase letters
    return bool(re.match(r"^[A-Z]{2}$", uf.upper()))


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

