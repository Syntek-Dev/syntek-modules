"""Example: Complete authentication flow using GraphQL mutations.

This example demonstrates the full authentication flow:
1. Register a new user
2. Verify email
3. Login
4. Setup 2FA
5. Refresh token
6. Logout
"""

import requests

# Base URL for GraphQL endpoint
GRAPHQL_URL = "http://localhost:8000/graphql/"


def graphql_request(query, variables=None, access_token=None):
    """Send a GraphQL request.

    Args:
        query: GraphQL query or mutation string
        variables: Optional variables dict
        access_token: Optional JWT access token

    Returns:
        Response JSON data
    """
    headers = {"Content-Type": "application/json"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    response = requests.post(
        GRAPHQL_URL,
        json={"query": query, "variables": variables},
        headers=headers,
        timeout=30
    )
    return response.json()


# 1. Register a new user
def register_user():
    """Register a new user account."""
    mutation = """
    mutation Register($input: RegisterInput!) {
      register(input: $input) {
        accessToken
        refreshToken
        user {
          id
          email
          emailVerified
        }
        requiresTwoFactor
      }
    }
    """

    variables = {
        "input": {
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "firstName": "John",
            "lastName": "Doe",
            "organisationSlug": "acme-corp",
            "captchaToken": "03AGdBq25...",  # Get from reCAPTCHA
            "acceptedDocumentIds": [1, 2],  # Terms & Privacy Policy IDs
        }
    }

    result = graphql_request(mutation, variables)
    print("Registration:", result)
    return result["data"]["register"]


# 2. Verify email
def verify_email(token):
    """Verify user's email address.

    Args:
        token: Email verification token from email
    """
    mutation = """
    mutation VerifyEmail($token: String!) {
      verifyEmail(token: $token)
    }
    """

    result = graphql_request(mutation, {"token": token})
    print("Email verification:", result)
    return result["data"]["verifyEmail"]


# 3. Login
def login():
    """Login with email and password."""
    mutation = """
    mutation Login($input: LoginInput!) {
      login(input: $input) {
        accessToken
        refreshToken
        user {
          id
          email
          organisation {
            name
            slug
          }
        }
        requiresTwoFactor
        sessionCount
        sessionLimit
      }
    }
    """

    variables = {
        "input": {
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "captchaToken": "03AGdBq25...",
        }
    }

    result = graphql_request(mutation, variables)
    print("Login:", result)
    return result["data"]["login"]


# 4. Setup 2FA
def setup_2fa(access_token):
    """Setup two-factor authentication.

    Args:
        access_token: JWT access token from login

    Returns:
        TOTP setup data (secret, QR code, backup codes)
    """
    # 4a. Generate setup data
    mutation = """
    mutation Generate2FA($input: Setup2FAInput!) {
      setup2FA(input: $input) {
        secret
        qrCodeUri
        backupCodes
      }
    }
    """

    variables = {"input": {"deviceName": "My iPhone"}}

    result = graphql_request(mutation, variables, access_token)
    print("2FA setup:", result)

    # Extract QR code and secret from setup result (not used in this example)
    # In a real app, display the QR code to the user for scanning
    # setup_data = result["data"]["setup2FA"]

    # 4b. Confirm setup with TOTP code
    confirm_mutation = """
    mutation Confirm2FA($input: Confirm2FAInput!) {
      confirm2FA(input: $input) {
        success
        backupCodes
      }
    }
    """

    # User scans QR code and enters TOTP code from authenticator app
    totp_code = input("Enter TOTP code from authenticator app: ")

    confirm_variables = {
        "input": {
            "deviceName": "My iPhone",
            "totpCode": totp_code,
        }
    }

    confirm_result = graphql_request(confirm_mutation, confirm_variables, access_token)
    print("2FA confirmation:", confirm_result)
    return confirm_result["data"]["confirm2FA"]


# 5. Login with 2FA
def login_with_2fa(totp_code):
    """Login with 2FA enabled.

    Args:
        totp_code: TOTP code from authenticator app
    """
    mutation = """
    mutation LoginWith2FA($input: LoginInput!) {
      login(input: $input) {
        accessToken
        refreshToken
        user {
          id
          email
        }
        requiresTwoFactor
      }
    }
    """

    variables = {
        "input": {
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "captchaToken": "03AGdBq25...",
            "totpCode": totp_code,
        }
    }

    result = graphql_request(mutation, variables)
    print("Login with 2FA:", result)
    return result["data"]["login"]


# 6. Refresh access token
def refresh_token(refresh_token):
    """Refresh access token using refresh token.

    Args:
        refresh_token: Valid refresh token

    Returns:
        New access and refresh tokens
    """
    mutation = """
    mutation RefreshToken($refreshToken: String!) {
      refreshToken(refreshToken: $refreshToken) {
        accessToken
        refreshToken
        user {
          id
          email
        }
      }
    }
    """

    result = graphql_request(mutation, {"refreshToken": refresh_token})
    print("Token refresh:", result)
    return result["data"]["refreshToken"]


# 7. Query current user
def get_current_user(access_token):
    """Get current authenticated user.

    Args:
        access_token: JWT access token
    """
    query = """
    query Me {
      me {
        id
        email
        emailVerified
        firstName
        lastName
        organisation {
          name
          slug
        }
        totpDevices {
          id
          name
          isConfirmed
          createdAt
        }
      }
    }
    """

    result = graphql_request(query, access_token=access_token)
    print("Current user:", result)
    return result["data"]["me"]


# 8. Logout
def logout(access_token):
    """Logout and revoke current session.

    Args:
        access_token: JWT access token
    """
    mutation = """
    mutation Logout {
      logout
    }
    """

    result = graphql_request(mutation, access_token=access_token)
    print("Logout:", result)
    return result["data"]["logout"]


# Example usage
if __name__ == "__main__":
    # 1. Register
    auth_data = register_user()
    access_token = auth_data["accessToken"]
    refresh_token_value = auth_data["refreshToken"]

    # 2. Verify email (token would come from email in real scenario)
    # verify_email("email-verification-token-from-email")

    # 3. Login (after email verification)
    login_data = login()
    access_token = login_data["accessToken"]
    refresh_token_value = login_data["refreshToken"]

    # 4. Setup 2FA
    # setup_2fa(access_token)

    # 5. Get current user
    user = get_current_user(access_token)

    # 6. Refresh token
    new_tokens = refresh_token(refresh_token_value)
    access_token = new_tokens["accessToken"]

    # 7. Logout
    logout(access_token)
