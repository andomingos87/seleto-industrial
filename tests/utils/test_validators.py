"""
Tests for validation and normalization utilities.

This test file covers validators and normalizers for:
- Phone (E.164 format, Brazilian DDDs)
- CNPJ (14 digits with check digits validation)
- Email (lowercase)
- UF (Brazilian state codes)

Test cases include:
- Valid inputs
- Invalid inputs
- Edge cases
- Normalization behavior
- ValidationError exception
- Strict validation modes
"""

import pytest

from src.utils.validation import (
    # Exceptions
    ValidationError,
    # Constants
    VALID_UFS,
    VALID_DDDS,
    # Phone
    normalize_phone,
    validate_phone,
    validate_phone_strict,
    validate_phone_or_raise,
    # CNPJ
    normalize_cnpj,
    validate_cnpj,
    validate_cnpj_or_raise,
    # Email
    normalize_email,
    validate_email,
    validate_email_or_raise,
    # UF
    normalize_uf,
    validate_uf,
    validate_uf_strict,
    validate_uf_or_raise,
)


class TestValidationError:
    """Tests for ValidationError exception."""

    def test_has_required_attributes(self):
        """Test that ValidationError has field, value, and message."""
        error = ValidationError(field="phone", value="123", message="Invalid phone")
        assert error.field == "phone"
        assert error.value == "123"
        assert error.message == "Invalid phone"

    def test_str_representation(self):
        """Test string representation of ValidationError."""
        error = ValidationError(field="email", value="test", message="Invalid email format")
        assert str(error) == "email: Invalid email format"

    def test_can_be_raised_and_caught(self):
        """Test that ValidationError can be raised and caught."""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError(field="cnpj", value="123", message="Invalid CNPJ")
        assert exc_info.value.field == "cnpj"


class TestNormalizePhone:
    """Tests for normalize_phone function."""

    def test_removes_all_non_digit_characters(self):
        """Test that all non-digit characters are removed."""
        assert normalize_phone("+55 11 99999-9999") == "5511999999999"
        assert normalize_phone("(11) 99999-9999") == "11999999999"
        assert normalize_phone("11.99999.9999") == "11999999999"
        assert normalize_phone("55 11 99999 9999") == "5511999999999"

    def test_already_normalized_phone(self):
        """Test phone that is already normalized."""
        assert normalize_phone("5511999999999") == "5511999999999"
        assert normalize_phone("11999999999") == "11999999999"

    def test_empty_and_none_inputs(self):
        """Test empty and None inputs."""
        assert normalize_phone("") == ""
        assert normalize_phone(None) == ""

    def test_various_brazilian_formats(self):
        """Test various Brazilian phone formats."""
        # With country code
        assert normalize_phone("+55 (11) 99999-9999") == "5511999999999"
        # Without country code
        assert normalize_phone("(11) 99999-9999") == "11999999999"
        # Landline (10 digits)
        assert normalize_phone("(11) 3456-7890") == "1134567890"
        # Mobile (11 digits)
        assert normalize_phone("11987654321") == "11987654321"


class TestValidatePhone:
    """Tests for validate_phone function."""

    def test_valid_phones(self):
        """Test valid phone numbers."""
        # Brazilian mobile with country code (13 digits)
        assert validate_phone("5511999999999") is True
        # Brazilian mobile without country code (11 digits)
        assert validate_phone("11999999999") is True
        # Brazilian landline without country code (10 digits)
        assert validate_phone("1134567890") is True

    def test_invalid_phones(self):
        """Test invalid phone numbers."""
        # Too short (less than 10 digits)
        assert validate_phone("123456789") is False
        assert validate_phone("12345") is False
        assert validate_phone("") is False

    def test_normalizes_before_validation(self):
        """Test that validation normalizes phone first."""
        # Formatted phone should be normalized and validated
        assert validate_phone("+55 11 99999-9999") is True
        assert validate_phone("(11) 99999-9999") is True

    def test_strict_mode_validates_ddd(self):
        """Test that strict mode validates Brazilian DDDs."""
        # Valid DDDs
        assert validate_phone("5511999999999", strict=True) is True  # SP
        assert validate_phone("5521999999999", strict=True) is True  # RJ
        assert validate_phone("5561999999999", strict=True) is True  # DF
        # Invalid DDD (00 doesn't exist)
        assert validate_phone("5500999999999", strict=True) is False

    def test_strict_mode_without_country_code(self):
        """Test strict mode with phones without country code."""
        assert validate_phone("11999999999", strict=True) is True
        assert validate_phone("00999999999", strict=True) is False


class TestValidatePhoneStrict:
    """Tests for validate_phone_strict convenience function."""

    def test_validates_valid_ddd(self):
        """Test that valid DDDs pass."""
        assert validate_phone_strict("5511999999999") is True
        assert validate_phone_strict("11999999999") is True

    def test_rejects_invalid_ddd(self):
        """Test that invalid DDDs fail."""
        assert validate_phone_strict("5500999999999") is False
        assert validate_phone_strict("00999999999") is False


class TestValidatePhoneOrRaise:
    """Tests for validate_phone_or_raise function."""

    def test_returns_normalized_phone_when_valid(self):
        """Test that valid phone returns normalized value."""
        result = validate_phone_or_raise("+55 11 99999-9999")
        assert result == "5511999999999"

    def test_raises_validation_error_when_invalid(self):
        """Test that invalid phone raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_phone_or_raise("123")
        assert exc_info.value.field == "phone"
        assert "Invalid phone" in exc_info.value.message


class TestNormalizeCnpj:
    """Tests for normalize_cnpj function."""

    def test_removes_punctuation(self):
        """Test that punctuation is removed."""
        assert normalize_cnpj("12.345.678/0001-90") == "12345678000190"
        assert normalize_cnpj("12-345-678/0001.90") == "12345678000190"

    def test_already_normalized_cnpj(self):
        """Test CNPJ that is already normalized."""
        assert normalize_cnpj("12345678000190") == "12345678000190"

    def test_empty_and_none_inputs(self):
        """Test empty and None inputs."""
        assert normalize_cnpj("") == ""
        assert normalize_cnpj(None) == ""

    def test_various_formats(self):
        """Test various CNPJ formats."""
        assert normalize_cnpj("12.345.678/0001-90") == "12345678000190"
        assert normalize_cnpj("12 345 678 0001 90") == "12345678000190"
        assert normalize_cnpj("12345678/0001-90") == "12345678000190"


class TestValidateCnpj:
    """Tests for validate_cnpj function with check digit validation."""

    def test_valid_cnpjs(self):
        """Test valid CNPJs with correct check digits."""
        # Known valid CNPJs (check digits calculated)
        assert validate_cnpj("11222333000181") is True  # Valid CNPJ
        assert validate_cnpj("11.222.333/0001-81") is True  # Formatted

    def test_invalid_cnpj_wrong_check_digits(self):
        """Test CNPJs with wrong check digits."""
        # Wrong first check digit
        assert validate_cnpj("11222333000191") is False
        # Wrong second check digit
        assert validate_cnpj("11222333000182") is False

    def test_invalid_cnpj_wrong_length(self):
        """Test CNPJs with wrong length."""
        assert validate_cnpj("1234567890123") is False  # 13 digits
        assert validate_cnpj("123456789012345") is False  # 15 digits
        assert validate_cnpj("") is False

    def test_rejects_all_same_digits(self):
        """Test that CNPJs with all same digits are rejected."""
        assert validate_cnpj("11111111111111") is False
        assert validate_cnpj("00000000000000") is False
        assert validate_cnpj("99999999999999") is False

    def test_normalizes_before_validation(self):
        """Test that CNPJ is normalized before validation."""
        # Valid CNPJ with formatting
        assert validate_cnpj("11.222.333/0001-81") is True


class TestValidateCnpjOrRaise:
    """Tests for validate_cnpj_or_raise function."""

    def test_returns_normalized_cnpj_when_valid(self):
        """Test that valid CNPJ returns normalized value."""
        result = validate_cnpj_or_raise("11.222.333/0001-81")
        assert result == "11222333000181"

    def test_raises_validation_error_when_invalid(self):
        """Test that invalid CNPJ raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_cnpj_or_raise("12345678000100")  # Invalid check digits
        assert exc_info.value.field == "cnpj"


class TestValidateEmail:
    """Tests for validate_email function."""

    def test_valid_emails(self):
        """Test valid email addresses."""
        assert validate_email("user@example.com") is True
        assert validate_email("user.name@example.com") is True
        assert validate_email("user+tag@example.com") is True
        assert validate_email("user@subdomain.example.com") is True
        assert validate_email("user123@example.co.br") is True

    def test_invalid_emails(self):
        """Test invalid email addresses."""
        assert validate_email("") is False
        assert validate_email(None) is False
        assert validate_email("invalid") is False
        assert validate_email("@example.com") is False
        assert validate_email("user@") is False
        assert validate_email("user@.com") is False

    def test_normalizes_before_validation(self):
        """Test that email is normalized before validation."""
        # With leading/trailing whitespace - now should pass
        assert validate_email("  user@example.com  ") is True
        # With uppercase - should pass
        assert validate_email("USER@EXAMPLE.COM") is True

    def test_edge_cases(self):
        """Test edge cases."""
        # Very long local part
        assert validate_email("a" * 64 + "@example.com") is True
        # Numeric domain
        assert validate_email("user@123.com") is True


class TestNormalizeEmail:
    """Tests for normalize_email function."""

    def test_converts_to_lowercase(self):
        """Test that email is converted to lowercase."""
        assert normalize_email("User@Example.COM") == "user@example.com"
        assert normalize_email("USER@EXAMPLE.COM") == "user@example.com"

    def test_removes_whitespace(self):
        """Test that whitespace is removed."""
        assert normalize_email("  user@example.com  ") == "user@example.com"
        assert normalize_email("user@example.com ") == "user@example.com"

    def test_empty_and_none_inputs(self):
        """Test empty and None inputs."""
        assert normalize_email("") == ""
        assert normalize_email(None) == ""


class TestValidateEmailOrRaise:
    """Tests for validate_email_or_raise function."""

    def test_returns_normalized_email_when_valid(self):
        """Test that valid email returns normalized value."""
        result = validate_email_or_raise("User@Example.COM")
        assert result == "user@example.com"

    def test_raises_validation_error_when_invalid(self):
        """Test that invalid email raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_email_or_raise("invalid")
        assert exc_info.value.field == "email"


class TestValidUfs:
    """Tests for VALID_UFS constant."""

    def test_contains_all_brazilian_states(self):
        """Test that VALID_UFS contains all 27 Brazilian states."""
        assert len(VALID_UFS) == 27
        # Check some known states
        assert "SP" in VALID_UFS
        assert "RJ" in VALID_UFS
        assert "MG" in VALID_UFS
        assert "DF" in VALID_UFS
        assert "AC" in VALID_UFS
        assert "TO" in VALID_UFS

    def test_does_not_contain_invalid_codes(self):
        """Test that VALID_UFS doesn't contain invalid codes."""
        assert "XX" not in VALID_UFS
        assert "ZZ" not in VALID_UFS
        assert "BR" not in VALID_UFS


class TestValidateUf:
    """Tests for validate_uf function."""

    def test_valid_ufs(self):
        """Test valid Brazilian state codes."""
        for uf in VALID_UFS:
            assert validate_uf(uf) is True, f"UF {uf} should be valid"

    def test_case_insensitive(self):
        """Test that validation is case insensitive."""
        assert validate_uf("sp") is True
        assert validate_uf("Sp") is True
        assert validate_uf("SP") is True

    def test_invalid_ufs_strict_mode(self):
        """Test invalid state codes in strict mode (default)."""
        assert validate_uf("") is False
        assert validate_uf(None) is False
        # "XX" is not a valid Brazilian state - strict mode rejects it
        assert validate_uf("XX") is False
        assert validate_uf("ZZ") is False
        assert validate_uf("S") is False  # Only 1 letter
        # Note: "SPP" gets normalized to "SP" before validation, so it passes
        assert validate_uf("SPP") is True  # Truncated to "SP" which is valid
        assert validate_uf("XXX") is False  # Truncated to "XX" which is invalid
        assert validate_uf("123") is False  # Numbers

    def test_non_strict_mode(self):
        """Test non-strict mode (only checks format, not valid states)."""
        # "XX" has valid format (2 letters) but is not a real state
        assert validate_uf("XX", strict=False) is True
        assert validate_uf("ZZ", strict=False) is True
        # Still rejects invalid formats
        assert validate_uf("S", strict=False) is False
        assert validate_uf("123", strict=False) is False


class TestValidateUfStrict:
    """Tests for validate_uf_strict convenience function."""

    def test_validates_real_states(self):
        """Test that real Brazilian states pass."""
        assert validate_uf_strict("SP") is True
        assert validate_uf_strict("RJ") is True

    def test_rejects_invalid_codes(self):
        """Test that invalid codes fail."""
        assert validate_uf_strict("XX") is False
        assert validate_uf_strict("ZZ") is False


class TestValidateUfOrRaise:
    """Tests for validate_uf_or_raise function."""

    def test_returns_normalized_uf_when_valid(self):
        """Test that valid UF returns normalized value."""
        result = validate_uf_or_raise("sp")
        assert result == "SP"

    def test_raises_validation_error_when_invalid(self):
        """Test that invalid UF raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_uf_or_raise("XX")
        assert exc_info.value.field == "uf"


class TestNormalizeUf:
    """Tests for normalize_uf function."""

    def test_converts_to_uppercase(self):
        """Test that UF is converted to uppercase."""
        assert normalize_uf("sp") == "SP"
        assert normalize_uf("Sp") == "SP"

    def test_removes_whitespace(self):
        """Test that whitespace is removed."""
        assert normalize_uf("  sp  ") == "SP"
        assert normalize_uf("sp ") == "SP"

    def test_truncates_to_two_chars(self):
        """Test that UF is truncated to 2 characters."""
        assert normalize_uf("SPP") == "SP"
        assert normalize_uf("spp") == "SP"

    def test_empty_and_none_inputs(self):
        """Test empty and None inputs."""
        assert normalize_uf("") == ""
        assert normalize_uf(None) == ""

    def test_single_char_preserved(self):
        """Test that single character is preserved."""
        assert normalize_uf("S") == "S"


class TestValidDdds:
    """Tests for VALID_DDDS constant."""

    def test_contains_major_ddds(self):
        """Test that VALID_DDDS contains major Brazilian area codes."""
        # São Paulo
        assert "11" in VALID_DDDS
        # Rio de Janeiro
        assert "21" in VALID_DDDS
        # Brasília
        assert "61" in VALID_DDDS
        # Belo Horizonte
        assert "31" in VALID_DDDS

    def test_does_not_contain_invalid_ddds(self):
        """Test that invalid DDDs are not in the set."""
        assert "00" not in VALID_DDDS
        assert "01" not in VALID_DDDS
        assert "10" not in VALID_DDDS


class TestValidationIntegration:
    """Integration tests for validation utilities."""

    def test_phone_normalization_and_validation_pipeline(self):
        """Test complete phone normalization and validation pipeline."""
        test_cases = [
            # (input, expected_normalized, expected_valid)
            ("+55 11 99999-9999", "5511999999999", True),
            ("(11) 99999-9999", "11999999999", True),
            ("1199999999", "1199999999", True),
            ("123", "123", False),
            ("", "", False),
        ]

        for phone_input, expected_normalized, expected_valid in test_cases:
            normalized = normalize_phone(phone_input)
            assert normalized == expected_normalized, f"normalize_phone({phone_input!r}) failed"
            assert validate_phone(phone_input) is expected_valid, f"validate_phone({phone_input!r}) failed"

    def test_cnpj_normalization_pipeline(self):
        """Test complete CNPJ normalization pipeline."""
        test_cases = [
            # (input, expected_normalized, expected_length)
            ("12.345.678/0001-90", "12345678000190", 14),
            ("12345678000190", "12345678000190", 14),
            ("12.345.678/0001-9", "1234567800019", 13),  # Invalid length
            ("", "", 0),
        ]

        for cnpj_input, expected_normalized, expected_length in test_cases:
            normalized = normalize_cnpj(cnpj_input)
            assert normalized == expected_normalized
            assert len(normalized) == expected_length

    def test_email_normalization_and_validation_pipeline(self):
        """Test complete email normalization and validation pipeline."""
        test_cases = [
            # (input, expected_normalized, expected_valid)
            ("User@Example.COM", "user@example.com", True),
            # validate_email now normalizes before validation
            ("  user@example.com  ", "user@example.com", True),
            ("invalid", "invalid", False),
            ("", "", False),
        ]

        for email_input, expected_normalized, expected_valid in test_cases:
            normalized = normalize_email(email_input)
            assert normalized == expected_normalized
            assert validate_email(email_input) is expected_valid


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_phone_with_special_characters(self):
        """Test phone with various special characters."""
        assert normalize_phone("tel:+5511999999999") == "5511999999999"

    def test_cnpj_with_extra_digits(self):
        """Test CNPJ with extra digits."""
        # Should preserve all digits
        assert normalize_cnpj("123456789012345") == "123456789012345"
        # But validation should fail
        assert validate_cnpj("123456789012345") is False

    def test_email_with_special_domains(self):
        """Test email with special domain patterns."""
        assert validate_email("user@example.com.br") is True
        assert validate_email("user@sub.domain.example.com") is True

    def test_uf_with_numbers(self):
        """Test UF with numbers (should fail)."""
        assert validate_uf("S1") is False
        assert validate_uf("1P") is False


class TestCnpjCheckDigits:
    """Tests specifically for CNPJ check digit calculation."""

    def test_known_valid_cnpjs(self):
        """Test known valid CNPJs."""
        # These are mathematically valid CNPJs
        valid_cnpjs = [
            "11222333000181",
            "11444777000161",
            "19131243000197",
        ]
        for cnpj in valid_cnpjs:
            assert validate_cnpj(cnpj) is True, f"CNPJ {cnpj} should be valid"

    def test_altered_check_digits(self):
        """Test that altering check digits makes CNPJ invalid."""
        # Valid: 11222333000181
        # Alter first check digit (8 -> 9)
        assert validate_cnpj("11222333000191") is False
        # Alter second check digit (1 -> 2)
        assert validate_cnpj("11222333000182") is False
        # Alter both
        assert validate_cnpj("11222333000192") is False

    def test_altered_base_digits(self):
        """Test that altering base digits makes CNPJ invalid."""
        # Valid: 11222333000181
        # Alter first digit
        assert validate_cnpj("21222333000181") is False
        # Alter middle digit
        assert validate_cnpj("11232333000181") is False
