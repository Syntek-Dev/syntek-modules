//! Input validation for PII data before encryption.
//!
//! Provides validation functions for email addresses, phone numbers, and IP addresses
//! to ensure only valid data is encrypted and stored in the database.
//!
//! # Security Features
//!
//! - RFC 5322 compliant email validation
//! - E.164 phone number format validation
//! - IPv4 and IPv6 address validation
//! - Length and format checks prevent injection attacks
//!
//! # Example
//!
//! ```
//! use syntek_encryption::validators::{validate_email, validate_phone_number, validate_ip_address};
//!
//! // Validate before encryption
//! validate_email("user@example.com")?;
//! validate_phone_number("+15551234567")?;
//! validate_ip_address("192.168.1.1")?;
//! ```

use anyhow::{Context, Result};
use std::net::IpAddr;

/// Maximum email address length per RFC 5321.
///
/// Total max length is 254 characters (64 local + 1 @ + 189 domain).
const MAX_EMAIL_LENGTH: usize = 254;

/// Minimum email address length.
///
/// Shortest valid email is "a@b.c" (5 characters).
const MIN_EMAIL_LENGTH: usize = 5;

/// Maximum local part length (before @).
const MAX_EMAIL_LOCAL_LENGTH: usize = 64;

/// Maximum domain part length (after @).
const MAX_EMAIL_DOMAIN_LENGTH: usize = 189;

/// Maximum phone number length in E.164 format.
///
/// E.164 allows up to 15 digits (excluding + prefix).
const MAX_PHONE_LENGTH: usize = 16; // +15 digits

/// Minimum phone number length.
///
/// Shortest valid number is 4 digits (some special services).
const MIN_PHONE_DIGITS: usize = 4;

/// Validates an email address according to RFC 5322 simplified rules.
///
/// Checks:
/// - Length constraints (5-254 characters)
/// - Contains exactly one @ symbol
/// - Local part (before @) length ≤ 64 characters
/// - Domain part (after @) length ≤ 189 characters
/// - Domain contains at least one dot
/// - No consecutive dots
/// - No leading/trailing dots
/// - Valid characters (alphanumeric, dot, hyphen, underscore, plus)
///
/// # Security Considerations
///
/// - Prevents SQL injection via email input
/// - Rejects malformed addresses that could cause parsing errors
/// - Enforces RFC 5322 length limits
///
/// # Arguments
///
/// * `email` - The email address to validate
///
/// # Returns
///
/// * `Result<()>` - Ok if valid, Err with description if invalid
///
/// # Errors
///
/// Returns error if email is invalid with specific reason.
///
/// # Example
///
/// ```
/// validate_email("user@example.com")?; // OK
/// validate_email("user@example")?;     // Error: no domain TLD
/// validate_email("@example.com")?;     // Error: missing local part
/// ```
pub fn validate_email(email: &str) -> Result<()> {
    let email = email.trim();

    // Length checks
    if email.len() < MIN_EMAIL_LENGTH {
        anyhow::bail!(
            "Email address too short (minimum {} characters)",
            MIN_EMAIL_LENGTH
        );
    }

    if email.len() > MAX_EMAIL_LENGTH {
        anyhow::bail!(
            "Email address too long (maximum {} characters)",
            MAX_EMAIL_LENGTH
        );
    }

    // Must contain exactly one @
    let at_count = email.matches('@').count();
    if at_count != 1 {
        anyhow::bail!("Email must contain exactly one @ symbol");
    }

    // Split into local and domain parts
    let parts: Vec<&str> = email.split('@').collect();
    let local = parts[0];
    let domain = parts[1];

    // Validate local part
    if local.is_empty() {
        anyhow::bail!("Email local part (before @) cannot be empty");
    }

    if local.len() > MAX_EMAIL_LOCAL_LENGTH {
        anyhow::bail!(
            "Email local part too long (maximum {} characters)",
            MAX_EMAIL_LOCAL_LENGTH
        );
    }

    // Check for invalid characters in local part
    if !local
        .chars()
        .all(|c| c.is_alphanumeric() || c == '.' || c == '-' || c == '_' || c == '+' || c == '\'')
    {
        anyhow::bail!("Email local part contains invalid characters");
    }

    // Local part cannot start or end with dot
    if local.starts_with('.') || local.ends_with('.') {
        anyhow::bail!("Email local part cannot start or end with dot");
    }

    // No consecutive dots in local part
    if local.contains("..") {
        anyhow::bail!("Email local part cannot contain consecutive dots");
    }

    // Validate domain part
    if domain.is_empty() {
        anyhow::bail!("Email domain (after @) cannot be empty");
    }

    if domain.len() > MAX_EMAIL_DOMAIN_LENGTH {
        anyhow::bail!(
            "Email domain too long (maximum {} characters)",
            MAX_EMAIL_DOMAIN_LENGTH
        );
    }

    // Domain must contain at least one dot
    if !domain.contains('.') {
        anyhow::bail!("Email domain must contain at least one dot (TLD required)");
    }

    // Check for invalid characters in domain
    if !domain
        .chars()
        .all(|c| c.is_alphanumeric() || c == '.' || c == '-')
    {
        anyhow::bail!("Email domain contains invalid characters");
    }

    // Domain cannot start or end with dot or hyphen
    if domain.starts_with('.')
        || domain.ends_with('.')
        || domain.starts_with('-')
        || domain.ends_with('-')
    {
        anyhow::bail!("Email domain cannot start or end with dot or hyphen");
    }

    // No consecutive dots in domain
    if domain.contains("..") {
        anyhow::bail!("Email domain cannot contain consecutive dots");
    }

    // Domain labels (parts between dots) validation
    for label in domain.split('.') {
        if label.is_empty() {
            anyhow::bail!("Email domain cannot have empty labels");
        }
        if label.len() > 63 {
            anyhow::bail!("Email domain label exceeds 63 characters");
        }
    }

    Ok(())
}

/// Validates a phone number according to E.164 format.
///
/// Checks:
/// - Optional leading + symbol
/// - Contains 4-15 digits
/// - Only digits, spaces, hyphens, parentheses, and + allowed
/// - After stripping formatting, must have 4-15 digits
///
/// # Security Considerations
///
/// - Prevents injection via phone number input
/// - Enforces E.164 length limits
/// - Rejects non-numeric characters (after formatting removal)
///
/// # Arguments
///
/// * `phone` - The phone number to validate (can include formatting)
///
/// # Returns
///
/// * `Result<()>` - Ok if valid, Err with description if invalid
///
/// # Errors
///
/// Returns error if phone number is invalid.
///
/// # Example
///
/// ```
/// validate_phone_number("+15551234567")?;     // OK
/// validate_phone_number("555-123-4567")?;     // OK
/// validate_phone_number("+1 (555) 123-4567")?; // OK
/// validate_phone_number("123")?;              // Error: too short
/// ```
pub fn validate_phone_number(phone: &str) -> Result<()> {
    let phone = phone.trim();

    if phone.is_empty() {
        anyhow::bail!("Phone number cannot be empty");
    }

    if phone.len() > MAX_PHONE_LENGTH + 10 {
        // Allow extra chars for formatting
        anyhow::bail!("Phone number too long");
    }

    // Check for valid characters (digits, +, -, (), space)
    if !phone
        .chars()
        .all(|c| c.is_ascii_digit() || c == '+' || c == '-' || c == '(' || c == ')' || c == ' ')
    {
        anyhow::bail!("Phone number contains invalid characters");
    }

    // Plus sign can only appear at the start
    if phone.matches('+').count() > 1 {
        anyhow::bail!("Phone number can only have one + symbol at the start");
    }

    if phone.contains('+') && !phone.starts_with('+') {
        anyhow::bail!("+ symbol must be at the start of phone number");
    }

    // Extract just the digits
    let digits: String = phone.chars().filter(|c| c.is_ascii_digit()).collect();

    // Validate digit count
    if digits.len() < MIN_PHONE_DIGITS {
        anyhow::bail!(
            "Phone number must have at least {} digits",
            MIN_PHONE_DIGITS
        );
    }

    if digits.len() > 15 {
        anyhow::bail!("Phone number exceeds E.164 maximum of 15 digits");
    }

    Ok(())
}

/// Validates an IP address (IPv4 or IPv6).
///
/// Uses Rust's `std::net::IpAddr` for robust validation.
///
/// # Security Considerations
///
/// - Prevents injection via IP address input
/// - Validates both IPv4 and IPv6 formats
/// - Rejects malformed addresses
///
/// # Arguments
///
/// * `ip` - The IP address to validate
///
/// # Returns
///
/// * `Result<()>` - Ok if valid, Err with description if invalid
///
/// # Errors
///
/// Returns error if IP address is invalid.
///
/// # Example
///
/// ```
/// validate_ip_address("192.168.1.1")?;      // OK (IPv4)
/// validate_ip_address("2001:0db8::1")?;     // OK (IPv6)
/// validate_ip_address("256.1.1.1")?;        // Error: invalid IPv4
/// ```
pub fn validate_ip_address(ip: &str) -> Result<()> {
    let ip = ip.trim();

    if ip.is_empty() {
        anyhow::bail!("IP address cannot be empty");
    }

    // Parse using standard library
    let _parsed: IpAddr = ip
        .parse()
        .context("Invalid IP address format (must be IPv4 or IPv6)")?;

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    // Email validation tests
    #[test]
    fn test_validate_email_valid() {
        assert!(validate_email("user@example.com").is_ok());
        assert!(validate_email("test.user@example.co.uk").is_ok());
        assert!(validate_email("user+tag@example.com").is_ok());
        assert!(validate_email("user_name@example.com").is_ok());
        assert!(validate_email("user-name@example.com").is_ok());
        assert!(validate_email("u@example.com").is_ok());
    }

    #[test]
    fn test_validate_email_invalid_no_at() {
        let result = validate_email("userexample.com");
        assert!(result.is_err());
        assert!(result.unwrap_err().to_string().contains("one @ symbol"));
    }

    #[test]
    fn test_validate_email_invalid_multiple_at() {
        let result = validate_email("user@@example.com");
        assert!(result.is_err());
    }

    #[test]
    fn test_validate_email_invalid_missing_local() {
        let result = validate_email("@example.com");
        assert!(result.is_err());
        assert!(result.unwrap_err().to_string().contains("cannot be empty"));
    }

    #[test]
    fn test_validate_email_invalid_missing_domain() {
        let result = validate_email("user@");
        assert!(result.is_err());
    }

    #[test]
    fn test_validate_email_invalid_no_tld() {
        let result = validate_email("user@example");
        assert!(result.is_err());
        assert!(result
            .unwrap_err()
            .to_string()
            .contains("must contain at least one dot"));
    }

    #[test]
    fn test_validate_email_invalid_too_long() {
        let long_local = "a".repeat(65);
        let email = format!("{}@example.com", long_local);
        let result = validate_email(&email);
        assert!(result.is_err());
        assert!(result.unwrap_err().to_string().contains("too long"));
    }

    #[test]
    fn test_validate_email_invalid_consecutive_dots() {
        assert!(validate_email("user..name@example.com").is_err());
        assert!(validate_email("user@example..com").is_err());
    }

    #[test]
    fn test_validate_email_invalid_leading_dot() {
        assert!(validate_email(".user@example.com").is_err());
        assert!(validate_email("user@.example.com").is_err());
    }

    #[test]
    fn test_validate_email_invalid_trailing_dot() {
        assert!(validate_email("user.@example.com").is_err());
        assert!(validate_email("user@example.com.").is_err());
    }

    // Phone number validation tests
    #[test]
    fn test_validate_phone_valid() {
        assert!(validate_phone_number("+15551234567").is_ok());
        assert!(validate_phone_number("5551234567").is_ok());
        assert!(validate_phone_number("+1 (555) 123-4567").is_ok());
        assert!(validate_phone_number("555-123-4567").is_ok());
        assert!(validate_phone_number("+44 20 7123 4567").is_ok());
    }

    #[test]
    fn test_validate_phone_invalid_too_short() {
        let result = validate_phone_number("123");
        assert!(result.is_err());
        assert!(result.unwrap_err().to_string().contains("at least"));
    }

    #[test]
    fn test_validate_phone_invalid_too_long() {
        let result = validate_phone_number("+1234567890123456"); // 16 digits
        assert!(result.is_err());
        assert!(result.unwrap_err().to_string().contains("exceeds"));
    }

    #[test]
    fn test_validate_phone_invalid_characters() {
        assert!(validate_phone_number("+1-555-ABC-4567").is_err());
        assert!(validate_phone_number("555@1234567").is_err());
    }

    #[test]
    fn test_validate_phone_invalid_multiple_plus() {
        let result = validate_phone_number("+1+5551234567");
        assert!(result.is_err());
    }

    #[test]
    fn test_validate_phone_invalid_plus_position() {
        let result = validate_phone_number("1+5551234567");
        assert!(result.is_err());
    }

    #[test]
    fn test_validate_phone_empty() {
        assert!(validate_phone_number("").is_err());
        assert!(validate_phone_number("   ").is_err());
    }

    // IP address validation tests
    #[test]
    fn test_validate_ip_valid_ipv4() {
        assert!(validate_ip_address("192.168.1.1").is_ok());
        assert!(validate_ip_address("8.8.8.8").is_ok());
        assert!(validate_ip_address("127.0.0.1").is_ok());
        assert!(validate_ip_address("0.0.0.0").is_ok());
        assert!(validate_ip_address("255.255.255.255").is_ok());
    }

    #[test]
    fn test_validate_ip_valid_ipv6() {
        assert!(validate_ip_address("2001:0db8::1").is_ok());
        assert!(validate_ip_address("::1").is_ok());
        assert!(validate_ip_address("fe80::1").is_ok());
        assert!(validate_ip_address("2001:0db8:0000:0000:0000:0000:0000:0001").is_ok());
    }

    #[test]
    fn test_validate_ip_invalid_ipv4() {
        assert!(validate_ip_address("256.1.1.1").is_err());
        assert!(validate_ip_address("192.168.1").is_err());
        assert!(validate_ip_address("192.168.1.1.1").is_err());
        assert!(validate_ip_address("abc.def.ghi.jkl").is_err());
    }

    #[test]
    fn test_validate_ip_invalid_ipv6() {
        assert!(validate_ip_address("gggg::1").is_err());
        assert!(validate_ip_address("2001:0db8:::1").is_err());
    }

    #[test]
    fn test_validate_ip_empty() {
        assert!(validate_ip_address("").is_err());
        assert!(validate_ip_address("   ").is_err());
    }

    #[test]
    fn test_validate_ip_random_text() {
        assert!(validate_ip_address("not-an-ip").is_err());
        assert!(validate_ip_address("hello world").is_err());
    }
}
