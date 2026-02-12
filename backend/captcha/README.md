# Syntek Captcha - reCAPTCHA v3 Integration

## Overview

Syntek Captcha provides Google reCAPTCHA v3 integration for bot protection in Django applications. It uses score-based verification (0.0-1.0) with action-specific thresholds and graceful degradation.

## Features

- **reCAPTCHA v3**: Invisible CAPTCHA with score-based verification
- **Action-Specific Thresholds**: Different scores for login, register, password reset
- **Fail-Open**: Service unavailability doesn't block legitimate users
- **Configurable**: Thresholds and API keys via Django settings
- **Async Support**: Non-blocking verification
- **Error Handling**: Graceful handling of network errors

## Installation

```bash
uv pip install syntek-captcha
```

## Configuration

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    'syntek_captcha',
]
```

Settings:

```python
SYNTEK_CAPTCHA = {
    'SECRET_KEY': 'your-recaptcha-secret-key',
    'SITE_KEY': 'your-recaptcha-site-key',
    'ENABLED': True,
    'FAIL_OPEN': True,  # Allow users through if reCAPTCHA service is down
    'THRESHOLDS': {
        'register': 0.5,
        'login': 0.3,
        'password_reset': 0.5,
        'contact': 0.5,
        'default': 0.5,
    },
}
```

## Usage

### Backend Verification

```python
from syntek_captcha.services.captcha_service import CaptchaService

def register_view(request):
    captcha_token = request.POST.get('g-recaptcha-response')

    # Verify reCAPTCHA
    is_valid, score, error = CaptchaService.verify_token(
        token=captcha_token,
        action='register'
    )

    if not is_valid:
        return JsonResponse({'error': f'CAPTCHA verification failed: {error}'})

    # Proceed with registration
    # ...
```

### Frontend Integration

```html
<!-- Add reCAPTCHA script -->
<script src="https://www.google.com/recaptcha/api.js?render={{ RECAPTCHA_SITE_KEY }}"></script>

<script>
  function onSubmit(e) {
    e.preventDefault();

    grecaptcha.ready(function () {
      grecaptcha
        .execute("{{ RECAPTCHA_SITE_KEY }}", { action: "register" })
        .then(function (token) {
          // Add token to form
          document.getElementById("g-recaptcha-response").value = token;

          // Submit form
          document.getElementById("register-form").submit();
        });
    });
  }
</script>

<form id="register-form" onsubmit="onSubmit(event)">
  <input type="hidden" id="g-recaptcha-response" name="g-recaptcha-response" />
  <!-- form fields -->
  <button type="submit">Register</button>
</form>
```

### GraphQL Integration

```python
from syntek_captcha.services.captcha_service import CaptchaService
import strawberry

@strawberry.mutation
def register(
    self,
    email: str,
    password: str,
    captcha_token: str,
    info: strawberry.Info
) -> RegisterResult:
    # Verify CAPTCHA
    is_valid, score, error = CaptchaService.verify_token(
        token=captcha_token,
        action='register'
    )

    if not is_valid:
        raise Exception(f"CAPTCHA verification failed: {error}")

    # Proceed with registration
    # ...
```

## API Reference

### Services

#### CaptchaService

- `verify_token(token, action)`: Verify a reCAPTCHA token
  - **Returns**: `(is_valid: bool, score: float, error: str | None)`
  - **Parameters**:
    - `token`: reCAPTCHA response token from frontend
    - `action`: Action name for threshold lookup
- `is_enabled()`: Check if CAPTCHA verification is enabled
- `get_threshold(action)`: Get score threshold for an action

## Action Thresholds

Default thresholds (higher = more strict):

| Action           | Threshold | Description                     |
| ---------------- | --------- | ------------------------------- |
| `register`       | 0.5       | User registration               |
| `login`          | 0.3       | Login (lower to avoid lockouts) |
| `password_reset` | 0.5       | Password reset requests         |
| `contact`        | 0.5       | Contact form submissions        |
| `default`        | 0.5       | Fallback for undefined actions  |

Scores range from 0.0 (bot) to 1.0 (human).

## Testing

```bash
pytest tests/
```

## Security Considerations

- Secret key MUST be kept confidential (never expose in frontend)
- Site key is public but should be restricted to your domain
- Fail-open mode allows users through if reCAPTCHA is down
- Failed verifications are logged for security monitoring
- Consider rate limiting in addition to CAPTCHA
- Use HTTPS to prevent token interception

## Fail-Open Behavior

When `FAIL_OPEN` is enabled:

- Network errors allow users through
- Invalid API keys block users (configuration error)
- Service timeouts allow users through
- This prevents legitimate users from being blocked

## Performance

- Verification adds ~100-300ms latency
- Asynchronous verification recommended for production
- Results are not cached (each token is single-use)
- No database queries required

## License

MIT
