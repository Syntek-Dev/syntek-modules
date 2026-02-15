//! Authentication configuration generator
//!
//! Generates comprehensive authentication configuration including:
//! - Django settings
//! - Email encryption keys
//! - Rate limiting
//! - Session security
//! - GDPR compliance
//! - Social auth providers

use crate::security::SecretsManager;
use crate::utils::error::Result;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Authentication installation mode
#[derive(Debug, Clone, Copy)]
pub enum InstallMode {
    Full,
    Minimal,
    WebOnly,
    MobileOnly,
}

/// Social auth provider configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SocialProviderConfig {
    pub name: String,
    pub client_id: String,
    pub client_secret: String,
    pub redirect_uri: String,
    pub scopes: Vec<String>,
}

/// SMS cost attack prevention configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SmsCostConfig {
    /// Global SMS rate limit (per hour)
    pub global_rate_limit: u32,
    /// Daily SMS budget limit (USD)
    pub daily_budget_limit: f64,
    /// Cost per SMS by provider
    pub cost_per_sms: HashMap<String, f64>,
    /// Budget alert thresholds (percentages)
    pub alert_thresholds: Vec<u8>,
    /// Alert destinations
    pub alert_destinations: Vec<String>,
    /// CAPTCHA escalation threshold (SMS per hour)
    pub captcha_threshold: u32,
    /// Enable automatic blocking
    pub auto_block: bool,
}

impl Default for SmsCostConfig {
    fn default() -> Self {
        let mut cost_per_sms = HashMap::new();
        cost_per_sms.insert("twilio".to_string(), 0.0075);
        cost_per_sms.insert("aws_sns".to_string(), 0.00645);
        cost_per_sms.insert("vonage".to_string(), 0.0072);

        Self {
            global_rate_limit: 1000,
            daily_budget_limit: 500.0,
            cost_per_sms,
            alert_thresholds: vec![80, 90, 100],
            alert_destinations: vec![],
            captcha_threshold: 100,
            auto_block: true,
        }
    }
}

/// Constant-time response configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConstantTimeConfig {
    /// Target response time (milliseconds)
    pub target_time_ms: u32,
    /// Endpoints to apply constant-time to
    pub endpoints: Vec<String>,
    /// Enable timing variance logging
    pub log_variance: bool,
    /// Alert if variance exceeds threshold (milliseconds)
    pub variance_alert_threshold_ms: u32,
}

impl Default for ConstantTimeConfig {
    fn default() -> Self {
        Self {
            target_time_ms: 250,
            endpoints: vec![
                "register".to_string(),
                "login".to_string(),
                "passwordReset".to_string(),
                "verifyEmail".to_string(),
            ],
            log_variance: true,
            variance_alert_threshold_ms: 5,
        }
    }
}

/// Session fingerprinting configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FingerprintConfig {
    /// Fingerprint level: minimal, balanced, aggressive
    pub level: String,
    /// Require GDPR consent for enhanced fingerprinting
    pub require_consent: bool,
    /// Enable privacy transparency notices
    pub privacy_transparency: bool,
}

impl Default for FingerprintConfig {
    fn default() -> Self {
        Self {
            level: "balanced".to_string(),
            require_consent: true,
            privacy_transparency: true,
        }
    }
}

/// GDPR compliance configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GdprConfig {
    /// Legal region (EU, USA, CA, AU, GLOBAL)
    pub legal_region: String,
    /// Privacy policy version
    pub privacy_policy_version: String,
    /// Terms of service version
    pub terms_version: String,
    /// Path to legal documents
    pub legal_docs_path: String,
    /// Regional document mapping
    pub regional_docs: HashMap<String, RegionalDocs>,
    /// Data retention period (days)
    pub data_retention_days: u32,
    /// IP log retention (days)
    pub ip_log_retention_days: u32,
    /// Account deletion grace period (days)
    pub deletion_grace_period_days: u32,
    /// Enable consent audit trail
    pub consent_audit: bool,
    /// Enable PII access logging
    pub pii_access_logging: bool,
    /// Encryption key rotation schedule (days)
    pub key_rotation_days: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RegionalDocs {
    pub privacy: String,
    pub terms: String,
}

impl Default for GdprConfig {
    fn default() -> Self {
        let mut regional_docs = HashMap::new();
        regional_docs.insert(
            "eu".to_string(),
            RegionalDocs {
                privacy: "/legal/privacy-policy-eu".to_string(),
                terms: "/legal/terms-of-service-eu".to_string(),
            },
        );
        regional_docs.insert(
            "usa".to_string(),
            RegionalDocs {
                privacy: "/legal/privacy-policy-usa".to_string(),
                terms: "/legal/terms-of-service-usa".to_string(),
            },
        );

        Self {
            legal_region: "auto".to_string(),
            privacy_policy_version: "1.0".to_string(),
            terms_version: "1.0".to_string(),
            legal_docs_path: "/legal/".to_string(),
            regional_docs,
            data_retention_days: 30,
            ip_log_retention_days: 90,
            deletion_grace_period_days: 30,
            consent_audit: true,
            pii_access_logging: true,
            key_rotation_days: 90,
        }
    }
}

/// Complete authentication configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuthConfig {
    /// Installation mode
    #[serde(skip)]
    pub mode: String,

    /// Enabled social providers
    pub social_providers: Vec<SocialProviderConfig>,

    /// SMS cost attack prevention
    pub sms_cost_prevention: SmsCostConfig,

    /// Constant-time responses
    pub constant_time: ConstantTimeConfig,

    /// Session fingerprinting
    pub fingerprinting: FingerprintConfig,

    /// GDPR compliance
    pub gdpr: GdprConfig,

    /// Email encryption key (generated)
    #[serde(skip_serializing)]
    pub email_encryption_key: String,

    /// Rate limiting rules
    pub rate_limiting: HashMap<String, RateLimitRule>,

    /// Argon2id parameters
    pub argon2: Argon2Config,

    /// Backup code settings
    pub backup_codes: BackupCodeConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RateLimitRule {
    pub requests: u32,
    pub window_seconds: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Argon2Config {
    /// Memory cost (KiB)
    pub memory_kib: u32,
    /// Time cost (iterations)
    pub iterations: u32,
    /// Parallelism
    pub parallelism: u32,
    /// Enable auto-tuning
    pub auto_tune: bool,
}

impl Default for Argon2Config {
    fn default() -> Self {
        Self {
            memory_kib: 19456, // 19 MiB
            iterations: 2,
            parallelism: 1,
            auto_tune: false,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackupCodeConfig {
    /// Number of backup codes
    pub count: u8,
    /// Code length
    pub length: u8,
    /// Expiry days
    pub expiry_days: u32,
}

impl Default for BackupCodeConfig {
    fn default() -> Self {
        Self {
            count: 10,
            length: 8,
            expiry_days: 90,
        }
    }
}

/// Authentication configuration generator
pub struct AuthConfigGenerator;

impl AuthConfigGenerator {
    /// Generate configuration for installation mode
    pub fn generate(mode: InstallMode, secrets: &mut SecretsManager) -> Result<AuthConfig> {
        let mut rate_limiting = HashMap::new();

        // Default rate limits
        rate_limiting.insert(
            "register".to_string(),
            RateLimitRule {
                requests: 5,
                window_seconds: 3600,
            },
        );
        rate_limiting.insert(
            "login".to_string(),
            RateLimitRule {
                requests: 10,
                window_seconds: 600,
            },
        );
        rate_limiting.insert(
            "password_reset".to_string(),
            RateLimitRule {
                requests: 3,
                window_seconds: 3600,
            },
        );
        rate_limiting.insert(
            "verify_email".to_string(),
            RateLimitRule {
                requests: 5,
                window_seconds: 3600,
            },
        );

        // Generate encryption key
        let email_key = secrets.generate("email_encryption_key", 32);

        Ok(AuthConfig {
            mode: format!("{:?}", mode),
            social_providers: Vec::new(),
            sms_cost_prevention: SmsCostConfig::default(),
            constant_time: ConstantTimeConfig::default(),
            fingerprinting: FingerprintConfig::default(),
            gdpr: GdprConfig::default(),
            email_encryption_key: email_key,
            rate_limiting,
            argon2: Argon2Config::default(),
            backup_codes: BackupCodeConfig::default(),
        })
    }

    /// Add social provider
    pub fn add_social_provider(
        config: &mut AuthConfig,
        provider: &str,
        secrets: &mut SecretsManager,
    ) -> Result<()> {
        let scopes = match provider {
            "google" => vec!["openid", "email", "profile"],
            "github" => vec!["user:email"],
            "microsoft" => vec!["openid", "email", "profile"],
            "apple" => vec!["name", "email"],
            "facebook" => vec!["email", "public_profile"],
            "linkedin" => vec!["r_emailaddress", "r_liteprofile"],
            "twitter" | "x" => vec!["tweet.read", "users.read"],
            _ => return Err(crate::utils::error::CliError::ValidationFailed(
                format!("Unsupported provider: {}", provider),
            )),
        };

        config.social_providers.push(SocialProviderConfig {
            name: provider.to_string(),
            client_id: format!("${{{}_CLIENT_ID}}", provider.to_uppercase()),
            client_secret: format!("${{{}_CLIENT_SECRET}}", provider.to_uppercase()),
            redirect_uri: format!("/auth/callback/{}", provider),
            scopes: scopes.iter().map(|s| s.to_string()).collect(),
        });

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_generate_config() {
        let mut secrets = SecretsManager::new();
        let config = AuthConfigGenerator::generate(InstallMode::Full, &mut secrets).unwrap();

        assert!(!config.email_encryption_key.is_empty());
        assert_eq!(config.constant_time.target_time_ms, 250);
        assert_eq!(config.gdpr.deletion_grace_period_days, 30);
    }

    #[test]
    fn test_add_social_provider() {
        let mut secrets = SecretsManager::new();
        let mut config = AuthConfigGenerator::generate(InstallMode::Full, &mut secrets).unwrap();

        AuthConfigGenerator::add_social_provider(&mut config, "google", &mut secrets).unwrap();

        assert_eq!(config.social_providers.len(), 1);
        assert_eq!(config.social_providers[0].name, "google");
        assert!(config.social_providers[0].scopes.contains(&"email".to_string()));
    }
}
