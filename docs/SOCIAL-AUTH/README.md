# Social Authentication Setup Guide

Complete guide for configuring OAuth 2.0 social authentication with 7 providers.

## Supported Providers

1. **Google OAuth 2.0** - Google accounts
2. **GitHub OAuth 2.0** - GitHub accounts
3. **Microsoft OAuth 2.0 / Azure AD** - Microsoft/Office 365 accounts
4. **Apple Sign In** - Apple ID accounts
5. **Facebook Login** - Facebook accounts
6. **Twitter OAuth 2.0** - Twitter accounts
7. **LinkedIn OAuth 2.0** - LinkedIn accounts

## Quick Start

### 1. Install Social Auth Module

\`\`\`bash

# Full installation (includes social auth)

syntek install auth --full

# Social auth only

syntek install auth --social-auth
\`\`\`

### 2. Configure Environment

Add to `.env`:

\`\`\`bash

# Google OAuth

GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret

# GitHub OAuth

GITHUB_CLIENT_ID=your-client-id
GITHUB_CLIENT_SECRET=your-client-secret

# Microsoft OAuth

MICROSOFT_CLIENT_ID=your-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret

# Apple Sign In

APPLE_CLIENT_ID=your.app.bundle.id
APPLE_TEAM_ID=your-team-id
APPLE_KEY_ID=your-key-id
APPLE_PRIVATE_KEY_PATH=/path/to/AuthKey_XXXX.p8

# Facebook Login

FACEBOOK_APP_ID=your-app-id
FACEBOOK_APP_SECRET=your-app-secret

# Twitter OAuth

TWITTER_CLIENT_ID=your-client-id
TWITTER_CLIENT_SECRET=your-client-secret

# LinkedIn OAuth

LINKEDIN_CLIENT_ID=your-client-id
LINKEDIN_CLIENT_SECRET=your-client-secret
\`\`\`

### 3. Add Django Settings

In `backend/settings.py`:

\`\`\`python
SYNTEK_SOCIAL_AUTH = {
'ENABLED_PROVIDERS': [
'google',
'github',
'microsoft',
'apple',
'facebook',
'twitter',
'linkedin'
],
'REDIRECT_URIS': {
'web': '<https://yourapp.com/auth/callback>',
'mobile': 'yourapp://auth/callback'
}
}
\`\`\`

## Provider-Specific Setup

### [Google OAuth 2.0](./GOOGLE.md)

- Google Cloud Console setup
- OAuth consent screen configuration
- Callback URL configuration

### [GitHub OAuth 2.0](./GITHUB.md)

- GitHub OAuth Apps setup
- Organization access
- Email scope configuration

### [Microsoft OAuth 2.0](./MICROSOFT.md)

- Azure AD app registration
- API permissions
- Multi-tenant configuration

### [Apple Sign In](./APPLE.md)

- Apple Developer account setup
- Services ID configuration
- Private key generation

### [Facebook Login](./FACEBOOK.md)

- Facebook App creation
- App Review process
- Privacy Policy requirements

### [Twitter OAuth 2.0](./TWITTER.md)

- Twitter Developer Portal
- App permissions
- Callback URLs

### [LinkedIn OAuth 2.0](./LINKEDIN.md)

- LinkedIn App creation
- OAuth 2.0 settings
- Product access

## Testing

\`\`\`bash

# Run social auth pentests

syntek pentest --module social_auth

# Test specific provider

curl -X GET <http://localhost:8000/api/v1/auth/social/google/authorize/>
\`\`\`

## Security Best Practices

1. **Never commit secrets** - Use environment variables
2. **Use HTTPS** - Required for production OAuth
3. **Implement PKCE** - For mobile apps
4. **Validate state parameter** - CSRF protection
5. **Restrict redirect URIs** - Whitelist only
6. **Rotate secrets** - Quarterly minimum
7. **Monitor usage** - Track OAuth failures

## Troubleshooting

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common issues.

## References

- [OAuth 2.0 RFC 6749](https://tools.ietf.org/html/rfc6749)
- [OpenID Connect](https://openid.net/connect/)
- [PKCE RFC 7636](https://tools.ietf.org/html/rfc7636)
