# Legal Documentation Templates

Templates for Privacy Policy, Terms of Service, and Cookie Policy.

## Templates Provided

1. **PRIVACY-POLICY-TEMPLATE.md** - GDPR-compliant privacy policy
2. **TERMS-OF-SERVICE-TEMPLATE.md** - Standard terms of service
3. **COOKIE-POLICY-TEMPLATE.md** - Cookie usage policy

## Usage

1. Copy templates to your project
2. Replace `[COMPANY_NAME]`, `[EMAIL]`, etc. with your details
3. Review with legal counsel
4. Update version dates
5. Configure paths in Django settings:

\`\`\`python
SYNTEK_LEGAL = {
'PRIVACY_POLICY_URL': '/legal/privacy',
'TERMS_URL': '/legal/terms',
'COOKIE_POLICY_URL': '/legal/cookies',
'PRIVACY_POLICY_VERSION': '1.0',
'TERMS_VERSION': '1.0',
}
\`\`\`

## Regional Variants

- **EU/GDPR**: Includes data protection rights, DPO contact
- **CCPA (California)**: Includes "Do Not Sell" provisions
- **UK**: Post-Brexit GDPR alignment
- **Global**: General template

## Required Updates

- Contact information
- Data processing purposes
- Third-party services used
- Data retention periods
- User rights procedures

## Legal Review Required

⚠️ **IMPORTANT**: These are templates only. Have them reviewed by legal counsel before use.
