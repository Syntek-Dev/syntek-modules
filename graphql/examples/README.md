# GraphQL Examples

This directory contains example usage patterns for the Syntek GraphQL modules.

## Examples

### 1. `unified_schema.py`

Shows how to create a unified GraphQL schema combining all modules:

- syntek-graphql-core (security)
- syntek-graphql-auth (authentication)
- syntek-graphql-audit (audit logging)
- syntek-graphql-compliance (GDPR & legal)

**Use case:** Full-featured application with all GraphQL capabilities.

### 2. `selective_installation.py`

Demonstrates different installation scenarios:

- **Minimal:** Auth only
- **Auth + Audit:** With logging
- **Auth + Compliance:** GDPR-compliant apps
- **Custom:** Pick specific features

**Use case:** Tailored installations for specific requirements.

## Running Examples

```bash
# Install required dependencies
cd /path/to/your/django/project

# Install all modules (for unified_schema.py)
uv pip install syntek-graphql-core syntek-graphql-auth syntek-graphql-audit syntek-graphql-compliance

# Or install selectively (for selective_installation.py examples)
uv pip install syntek-graphql-core syntek-graphql-auth

# Import in your Django project
from graphql.examples.unified_schema import schema

# Add to your urls.py
from strawberry.django.views import GraphQLView
urlpatterns = [
    path('graphql/', GraphQLView.as_view(schema=schema)),
]
```

## Module Dependencies

```
┌─────────────────────────┐
│   syntek-graphql-core   │ ← Base (required)
└─────────────────────────┘
            ▲
            │ depends on
    ┌───────┼───────┬────────────┐
    │               │            │
┌───────┐    ┌──────────┐  ┌─────────────┐
│ Auth  │    │  Audit   │  │ Compliance  │
└───────┘    └──────────┘  └─────────────┘
```

## Additional Resources

- See individual module READMEs for detailed documentation
- Check module `schema.py` files for standalone schema functions
- Refer to test files for usage patterns
