# 🎬 The Complete OAuth PKCE Story: A Step-by-Step Journey

## **Chapter 0: Setting Up Auth0 with Google Authentication**

Before our OAuth story begins, we need to set up the authentication infrastructure. Here's how you set up Auth0 with Google integration:

### **🏗️ Step 1: Creating Auth0 Account**

**👤 You** go to [auth0.com](https://auth0.com) and:
1. Click "Sign Up" and create a free account
2. Choose a **tenant domain** (this becomes your AUTH0_DOMAIN)
   - Example: `dev-a85i5cax3v3cy6l4.us.auth0.com`
3. Select "For personal use" and continue

### **🔧 Step 2: Create a New Application**

In the Auth0 Dashboard:
```
1. Go to Applications → Applications
2. Click "Create Application"
3. Name: "OAuth PKCE Demo" 
4. Type: "Single Page Application" (for PKCE support)
5. Click "Create"
```

**📋 Application Settings:**
```
Basic Information:
- Name: OAuth PKCE Demo
- Domain: dev-a85i5cax3v3cy6l4.us.auth0.com
- Client ID: QhgXEVKKNmJzLwQxZeUuxtfqXlf619S5 (yours will be different)
- Client Secret: [Not needed for PKCE/public clients]

Application URIs:
- Allowed Callback URLs: http://localhost:8091/callback
- Allowed Web Origins: http://localhost:8091
- Allowed Origins (CORS): http://localhost:8091
```

### **🔐 Step 3: Configure Google Social Connection**

**🌐 In Auth0 Dashboard:**
```
1. Go to Authentication → Social
2. Click the Google icon
3. Click "Create Connection"
```

**🔑 Google OAuth Setup:**
```
You need Google OAuth credentials from Google Cloud Console:

1. Go to console.cloud.google.com
2. Create a new project or select existing
3. Go to APIs & Services → Credentials
4. Click "Create Credentials" → "OAuth 2.0 Client IDs"
5. Application type: "Web application"
6. Name: "Auth0 Integration"
7. Authorized redirect URIs: 
   https://dev-a85i5cax3v3cy6l4.us.auth0.com/login/callback
```

**📊 Google Console Configuration:**
```javascript
// In Google Cloud Console, you configure:
{
  "client_id": "123456789-abcdefghijklmnop.apps.googleusercontent.com",
  "client_secret": "GOCSPX-your_google_client_secret",
  "redirect_uris": [
    "https://dev-a85i5cax3v3cy6l4.us.auth0.com/login/callback"
  ],
  "authorized_domains": [
    "dev-a85i5cax3v3cy6l4.us.auth0.com"
  ]
}
```

**🔗 Back in Auth0:**
```
Google Social Connection Settings:
- Client ID: [Paste from Google Console]
- Client Secret: [Paste from Google Console]
- Allowed Scopes: email, profile, openid
- Attributes:
  ✅ Email address
  ✅ Profile
  ✅ Basic profile
```

### **🔗 Step 4: Connect Application to Google**

**⚙️ In Auth0 Dashboard:**
```
1. Go to Applications → Applications → Your App
2. Click "Connections" tab
3. Under "Social", enable Google
4. Disable "Username-Password-Authentication" if you only want Google
```

### **🎯 Step 5: Test Configuration**

**🧪 Auth0 provides a test button:**
```
1. In your Google connection settings
2. Click "Try Connection"
3. You should see Google login page
4. After login, Auth0 shows user profile data
```

**📱 What happens during the test:**
```javascript
// Auth0 redirects to Google with:
{
  "url": "https://accounts.google.com/oauth/authorize",
  "params": {
    "client_id": "your-google-client-id",
    "redirect_uri": "https://your-tenant.auth0.com/login/callback", 
    "scope": "openid email profile",
    "response_type": "code",
    "state": "auth0-state-token"
  }
}

// Google redirects back to Auth0 with:
{
  "code": "google-authorization-code",
  "state": "auth0-state-token"
}

// Auth0 exchanges code for Google tokens and creates Auth0 user profile
```

### **🏢 Corporate Integration Notes**

**🔐 In enterprise environments, instead of Google, you'd configure:**
```
Enterprise Connections:
- SAML (Active Directory Federation Services)
- OpenID Connect (Azure AD, Okta)
- LDAP (Corporate directory)

Example ADFS Configuration:
{
  "domain": "company.com",
  "sso_url": "https://adfs.company.com/adfs/ls/",
  "certificate": "-----BEGIN CERTIFICATE-----...",
  "user_id_attribute": "windowsaccountname",
  "email_attribute": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"
}
```

### **🚀 Step 6: Update Your Code**

**📝 Finally, update your application configuration:**
```python
# Auth0 Configuration from your dashboard
AUTH0_DOMAIN = "dev-a85i5cax3v3cy6l4.us.auth0.com"  # Your tenant domain
CLIENT_ID = "QhgXEVKKNmJzLwQxZeUuxtfqXlf619S5"      # Your app's Client ID
REDIRECT_URI = "http://localhost:8091/callback"        # Must match Auth0 settings
SCOPE = "openid profile email"                         # Requested permissions
```

**🔍 Verification Checklist:**
```
✅ Auth0 tenant created with custom domain
✅ Application created with PKCE support
✅ Google Cloud OAuth credentials configured
✅ Google social connection enabled in Auth0
✅ Callback URLs match between all systems:
   - Google: https://your-tenant.auth0.com/login/callback
   - Auth0: http://localhost:8091/callback
   - Your app: REDIRECT_URI = "http://localhost:8091/callback"
✅ Application connected to Google social connection
✅ Test connection successful
```

Now when users click "Continue with Google" in your app, this entire backend infrastructure handles the authentication securely!

---

## **Chapter 1: The User's Journey Begins**

**👤 You (the user)** open your browser and type:
```
http://localhost:8091
```

**🖥️ Your Local Server** receives this request and responds with a welcome page:

```python
def handle_home(self):
    # Your server shows you a login button
    html = """
    <h1>🔐 Complete OAuth PKCE Flow</h1>
    <a href="/login">🚀 Start OAuth Login (PKCE)</a>
    """
    self.wfile.write(html.encode())
```

**📖 What's happening:** Your local Python server is running and ready to demonstrate OAuth.

---

## **Chapter 2: The Secret Generation**

**👤 You** click the "Start OAuth Login" button, which sends your browser to:
```
http://localhost:8091/login
```

**🖥️ Your Local Server** immediately gets to work creating PKCE secrets:

```python
def handle_login(self):
    # Step 1: Generate PKCE secrets (like creating a unique password)
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip('=')
    # Example: "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
    
    # Step 2: Create a puzzle from the secret (one-way hash)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip('=')
    # Example: "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
    
    # Step 3: Store the secret for later (your server remembers it)
    self.server.code_verifier = code_verifier
```

**📖 What's happening:** Your server creates a cryptographic secret (verifier) and a puzzle (challenge). It keeps the secret safe and will send only the puzzle to Auth0.

---

## **Chapter 3: The Redirect to Auth0**

**🖥️ Your Local Server** builds a special URL and redirects your browser:

```python
    # Step 4: Build the authorization URL
    params = {
        'response_type': 'code',                    # "I want an authorization code"
        'client_id': 'QhgXEVKKNmJzLwQxZeUuxtfqXlf619S5',  # "This is who I am"
        'redirect_uri': 'http://localhost:8091/callback',    # "Send the user back here"
        'scope': 'openid profile email',           # "I want these permissions"
        'code_challenge': code_challenge,          # "Here's my puzzle"
        'code_challenge_method': 'S256',          # "I used SHA256 to make the puzzle"
        'state': 'random_security_token'          # "Anti-forgery protection"
    }
    
    auth_url = f"https://dev-a85i5cax3v3cy6l4.us.auth0.com/authorize?" + urllib.parse.urlencode(params)
    # Redirects your browser to Auth0
    self.send_response(302)
    self.send_header('Location', auth_url)
```

**🌐 Your Browser** automatically goes to Auth0 with this long URL:
```
https://dev-a85i5cax3v3cy6l4.us.auth0.com/authorize?
  response_type=code&
  client_id=QhgXEVKKNmJzLwQxZeUuxtfqXlf619S5&
  redirect_uri=http://localhost:8091/callback&
  scope=openid+profile+email&
  code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&
  code_challenge_method=S256&
  state=abc123
```

**📖 What's happening:** Your server tells your browser to visit Auth0 with the puzzle (challenge) but keeps the secret (verifier) safe at home.

---

## **Chapter 4: Auth0 Stores the Puzzle**

**🏛️ Auth0 Server** receives your browser's request and:

```javascript
// Inside Auth0's servers (conceptual)
auth0_storage = {
    client_id: "QhgXEVKKNmJzLwQxZeUuxtfqXlf619S5",
    redirect_uri: "http://localhost:8091/callback",
    code_challenge: "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
    code_challenge_method: "S256",
    scope: "openid profile email",
    // Auth0 remembers all of this!
}
```

**🌐 Auth0** shows you a login page and you choose "Continue with Google"

**📖 What's happening:** Auth0 safely stores your puzzle and all the request details, then shows you authentication options.

---

## **Chapter 4.5: The Hidden Google OAuth Flow (Behind the Scenes)**

**🔍 Here's what REALLY happens when you click "Continue with Google":**

### **Step 1: Auth0 → Google OAuth Flow**
```javascript
// When you click "Continue with Google", Auth0 immediately:

// 1. Auth0 redirects YOUR BROWSER to Google OAuth
const googleAuthUrl = "https://accounts.google.com/oauth/authorize?" + new URLSearchParams({
    client_id: "123456789-abcdefghijklmnop.apps.googleusercontent.com", // Auth0's Google client
    redirect_uri: "https://dev-a85i5cax3v3cy6l4.us.auth0.com/login/callback", // Back to Auth0!
    scope: "openid email profile",
    response_type: "code",
    state: "auth0_google_state_token"
});

// Your browser goes to Google, NOT directly back to your app!
```

### **Step 2: Google Authentication**
**👤 You** complete Google login (password, 2FA, etc.)

**🔐 Google** authenticates you and redirects back to **AUTH0** (not your app):
```
https://dev-a85i5cax3v3cy6l4.us.auth0.com/login/callback?
  code=GOOGLE_AUTH_CODE_xyz123&
  state=auth0_google_state_token
```

### **Step 3: Auth0 ↔ Google Token Exchange (Hidden from You)**
**🏛️ Auth0** now does its OWN OAuth token exchange with Google:

```javascript
// Auth0's backend calls Google's token endpoint directly
const googleTokenRequest = {
    method: 'POST',
    url: 'https://oauth2.googleapis.com/token',
    data: {
        grant_type: 'authorization_code',
        client_id: 'auth0s_google_client_id',      // Auth0's Google credentials
        client_secret: 'auth0s_google_client_secret', // Auth0's Google secret
        code: 'GOOGLE_AUTH_CODE_xyz123',           // Code Google gave Auth0
        redirect_uri: 'https://dev-a85i5cax3v3cy6l4.us.auth0.com/login/callback'
    }
};

// Google responds to Auth0 with:
const googleTokens = {
    access_token: "ya29.google_access_token_here",
    id_token: "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6IjEyMyJ9...", // Google JWT
    expires_in: 3600,
    scope: "openid email profile"
};
```

### **Step 4: Auth0 Gets Your Google Profile**
**🏛️ Auth0** uses Google's access token to fetch your profile:

```javascript
// Auth0 calls Google's userinfo endpoint
const googleProfile = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
    headers: {
        'Authorization': `Bearer ${googleTokens.access_token}`
    }
});

// Google returns your profile to Auth0:
const userProfile = {
    id: "1234567890",
    email: "user@gmail.com", 
    name: "John Doe",
    picture: "https://lh3.googleusercontent.com/...",
    verified_email: true
};
```

### **Step 5: Auth0 Creates Internal User Record**
```javascript
// Auth0 creates/updates internal user record
const auth0User = {
    user_id: "google-oauth2|1234567890",  // Auth0's internal ID
    email: "user@gmail.com",
    name: "John Doe", 
    picture: "https://lh3.googleusercontent.com/...",
    provider: "google-oauth2",
    connection: "google-oauth2",
    // Auth0 stores this in its database
};
```

**📖 What's happening:** Auth0 performs a complete OAuth flow with Google on your behalf, gets your Google profile, and creates an internal user record. You never see the Google tokens - Auth0 handles everything.

---

## **Chapter 5: Auth0 Generates Your App's Authorization Code**

**🏛️ Auth0** NOW generates the authorization code for YOUR application:

```javascript
// Only AFTER Google authentication succeeds, Auth0 creates YOUR app's code
const yourAppAuthCode = {
    code: "AUTH_CODE_abc123xyz789",           // This is for YOUR app
    linked_to_challenge: "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
    redirect_uri: "http://localhost:8091/callback",  // YOUR app's callback
    user_id: "google-oauth2|1234567890",     // Links to internal Auth0 user
    expires_in: 600,  // 10 minutes
    scope: "openid profile email"
};
```

**🌐 Auth0** redirects your browser to YOUR application:
```
http://localhost:8091/callback?code=AUTH_CODE_abc123xyz789&state=abc123
```

**📖 What's happening:** Auth0 creates a NEW authorization code specifically for your application, linked to the authenticated Google user.

---

## **🔄 The Complete Multi-Layer Flow:**

```
👤 Your Browser    🖥️ Your App    🏛️ Auth0 Server    🔐 Google APIs
     │                 │              │                 │
     │ 1. /login        │              │                 │
     ├─────────────────▶│              │                 │
     │                  │ 2. Redirect  │                 │
     │                  │    to Auth0  │                 │
     ◀─────────────────┤              │                 │
     │                                 │                 │
     │ 3. Auth request with PKCE      │                 │
     ├────────────────────────────────▶│                 │
     │                  │              │ 4. Store PKCE  │
     │ 5. Login page    │              │    challenge   │
     ◀────────────────────────────────┤              │
     │                  │              │                 │
     │ 6. "Continue with Google"       │                 │
     ├────────────────────────────────▶│                 │
     │                  │              │ 7. Redirect to  │
     │                  │              │    Google       │
     │ 8. Google OAuth URL             │                 │
     ◀────────────────────────────────┤              │
     │                  │                              │
     │ 9. Google login page                           │
     ├────────────────────────────────────────────────▶│
     │                  │              │                 │
     │ 10. Enter credentials                           │
     ├────────────────────────────────────────────────▶│
     │                  │              │                 │
     │ 11. Google callback to Auth0    │                 │
     ◀────────────────────────────────┤              │
     │                  │              │                 │
     │                  │              │ 12. Auth0 calls │
     │                  │              │     Google APIs │
     │                  │              ├────────────────▶│
     │                  │              │ 13. User profile│
     │                  │              ◀────────────────┤
     │                  │              │ 14. Create user │
     │                  │              │     in Auth0    │
     │                  │              │ 15. Generate    │
     │                  │              │     YOUR code   │
     │ 16. Callback to YOUR app        │                 │
     ◀────────────────────────────────┤              │
     │                  │                              │
     │ 17. Send code    │              │                 │
     ├─────────────────▶│              │                 │
     │                  │ 18. Exchange │                 │
     │                  │     code +   │                 │
     │                  │     verifier │                 │
     │                  ├─────────────▶│                 │
     │                  │              │ 19. Verify PKCE│
     │                  │              │     & return    │
     │                  │              │     JWT tokens │
     │                  ◀─────────────┤              │
     │ 20. Success page │              │                 │
     ◀─────────────────┤              │                 │
```

---

## **🎯 Key Insights:**

### **Two Separate OAuth Flows:**
1. **Auth0 ↔ Google**: Happens behind the scenes, you never see Google's tokens
2. **Your App ↔ Auth0**: The PKCE flow you implement

### **When Does Auth0 Call Google?**
- **BEFORE** generating your app's authorization code
- Auth0 must verify the user with Google first
- Only after Google confirms identity does Auth0 create your app's code

### **What You Never See:**
- Google's authorization code (goes to Auth0)
- Google's access tokens (stored by Auth0)  
- Google API calls (made by Auth0)

### **What You Do See:**
- Auth0's authorization code (for your app)
- Auth0's JWT tokens (containing Google user info)
- Your PKCE flow (between your app and Auth0)

**🎉 This is why Auth0 is so powerful** - it handles the complex Google OAuth flow so you don't have to!

**👤 You** complete authentication with Google (enter password, 2FA, etc.)

**🔐 Google** tells Auth0: "Yes, this user is authenticated and consents to sharing profile information"

**🏛️ Auth0** generates a special authorization code:
```javascript
// Auth0 creates a temporary code linked to your puzzle
authorization_code = "AUTH_CODE_abc123xyz789"

// Auth0 links this code to your stored challenge
auth0_code_storage = {
    code: "AUTH_CODE_abc123xyz789",
    linked_to_challenge: "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
    redirect_uri: "http://localhost:8091/callback",
    expires_in: 600  // 10 minutes
}
```

**📖 What's happening:** Google confirms your identity to Auth0, and Auth0 creates a temporary code that's cryptographically linked to your puzzle.

---

## **Chapter 6: The Return Journey**

**🏛️ Auth0** redirects your browser back to your application:
```
http://localhost:8091/callback?code=AUTH_CODE_abc123xyz789&state=abc123
```

**🖥️ Your Local Server** catches this callback:

```python
def handle_callback(self):
    # Parse the URL to extract the authorization code
    query = urllib.parse.urlparse(self.path).query
    params = urllib.parse.parse_qs(query)
    
    auth_code = params['code'][0]  # "AUTH_CODE_abc123xyz789"
    print(f"✅ Authorization Code received: {auth_code}")
    
    # Now we'll exchange this code for tokens!
    tokens = self.exchange_code_for_tokens(auth_code)
```

**📖 What's happening:** Auth0 sends your browser back home with a temporary authorization code as proof that you successfully authenticated (via Google behind the scenes).

---

## **Chapter 7: The Token Exchange - The Critical Moment**

**🖥️ Your Local Server** now makes a direct server-to-server call to Auth0:

```python
def exchange_code_for_tokens(self, auth_code):
    token_url = f"https://{AUTH0_DOMAIN}/oauth/token"
    
    # Prepare the token exchange request
    data = {
        'grant_type': 'authorization_code',           # "I'm exchanging a code"
        'client_id': CLIENT_ID,                      # "This is who I am"
        'code': auth_code,                           # "Here's the code you gave me"
        'redirect_uri': REDIRECT_URI,                # "Same redirect as before (security check)"
        'code_verifier': self.server.code_verifier   # "HERE'S MY SECRET!"
    }
    
    # Make the synchronous HTTP request
    req = urllib.request.Request(
        token_url,
        data=urllib.parse.urlencode(data).encode(),
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    
    with urllib.request.urlopen(req) as response:
        tokens = json.loads(response.read().decode())
        return tokens
```

**📖 What's happening:** Your server sends the authorization code AND the secret (code_verifier) directly to Auth0. No browser involved - this is server-to-server communication.

---

## **Chapter 8: Auth0's Verification Process**

**🏛️ Auth0 Server** receives your token request and performs multiple security checks:

```javascript
// Inside Auth0's token endpoint (conceptual)
function processTokenExchange(request) {
    // Step 1: Find the stored challenge using the code
    const storedData = findByCode(request.code);
    
    // Step 2: Verify redirect_uri matches
    if (storedData.redirect_uri !== request.redirect_uri) {
        throw new Error("redirect_uri mismatch - possible attack!");
    }
    
    // Step 3: THE CRITICAL PKCE VERIFICATION
    const provided_verifier = request.code_verifier;  // Your secret
    const stored_challenge = storedData.code_challenge;  // Your puzzle
    
    // Step 4: Recreate the puzzle from your secret
    const computed_challenge = sha256_base64(provided_verifier);
    
    // Step 5: Compare the puzzles
    if (computed_challenge === stored_challenge) {
        // SUCCESS! You proved you have the original secret
        return generateTokens(storedData.user_id, storedData.scope);
    } else {
        throw new Error("PKCE verification failed - invalid code_verifier!");
    }
}
```

**🔐 The Magic Verification:**
```
Your original secret:     "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
Puzzle you sent before:   "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
Secret you're sending now: "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"

Auth0 calculates: SHA256("dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk")
Result:           "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"

Match? ✅ YES! You must be the same entity that started this flow!
```

**📖 What's happening:** Auth0 uses cryptography to prove you're the same application that started the authentication process. Only you could have the secret that creates the stored puzzle.

---

## **Chapter 9: The Token Response**

**🏛️ Auth0** generates JWT tokens and responds to your server:

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjEyMyJ9.eyJpc3MiOiJodHRwczovL2Rldi1hODVpNWNheDN2M2N5Nmw0LnVzLmF1dGgwLmNvbS8iLCJzdWIiOiJnb29nbGUtb2F1dGgyfDEyMzQ1Njc4OTAiLCJhdWQiOlsiUWhncVhFVktLTm1Kekx3UXhaZVV1eHRmcVhsZjYxOVM1Il0sImlhdCI6MTcwNjM2MjgwMCwiZXhwIjoxNzA2NDQ5MjAwLCJhenAiOiJRaGdxWEVWS0tObUp6THdReFplVXV4dGZxWGxmNjE5UzUiLCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIn0.signature",
  "id_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjEyMyJ9.eyJpc3MiOiJodHRwczovL2Rldi1hODVpNWNheDN2M2N5Nmw0LnVzLmF1dGgwLmNvbS8iLCJzdWIiOiJnb29nbGUtb2F1dGgyfDEyMzQ1Njc4OTAiLCJhdWQiOiJRaGdxWEVWS0tObUp6THdReFplVXV4dGZxWGxmNjE5UzUiLCJpYXQiOjE3MDYzNjI4MDAsImV4cCI6MTcwNjQ0OTIwMCwiZW1haWwiOiJ1c2VyQGV4YW1wbGUuY29tIiwibmFtZSI6IkpvaG4gRG9lIn0.signature",
  "token_type": "Bearer",
  "expires_in": 86400
}
```

**🖥️ Your Local Server** receives these tokens:

```python
    with urllib.request.urlopen(req) as response:
        tokens = json.loads(response.read().decode())
        
        # Store tokens for later use
        self.server.access_token = tokens['access_token']
        self.server.id_token = tokens.get('id_token', '')
        
        print(f"✅ Tokens received: {list(tokens.keys())}")
        return tokens
```

**📖 What's happening:** Auth0 sends back JWT tokens that prove you're authenticated and contain user information. Your server can now make API calls on behalf of the user.

---

## **Chapter 10: The Victory - Using the Tokens**

**🖥️ Your Local Server** can now make authenticated API calls:

```python
def handle_protected_api(self):
    # Simulate a protected API call (like Flyte APIs)
    if not hasattr(self.server, 'access_token'):
        return self.send_error(401, "No access token")
    
    # In real life, you'd send this token to APIs:
    headers = {
        'Authorization': f'Bearer {self.server.access_token}',
        'Content-Type': 'application/json'
    }
    
    # This is how flytectl would call Flyte APIs!
    api_response = {
        "message": "Access granted to protected resource",
        "user": "authenticated", 
        "timestamp": "2025-07-27T15:00:00Z",
        "scope": "read:workflows write:workflows"
    }
```

**🎯 JWT Token Breakdown:**
```python
def parse_jwt_payload(self, jwt_token):
    # JWT has 3 parts: header.payload.signature
    parts = jwt_token.split('.')
    
    # Decode the payload (contains user info)
    payload = parts[1]
    payload += '=' * (4 - len(payload) % 4)  # Add padding
    decoded = base64.urlsafe_b64decode(payload)
    
    user_info = json.loads(decoded)
    # Example result:
    # {
    #   "iss": "https://dev-a85i5cax3v3cy6l4.us.auth0.com/",
    #   "sub": "google-oauth2|1234567890",
    #   "email": "user@example.com",
    #   "name": "John Doe",
    #   "exp": 1706449200
    # }
```

**📖 What's happening:** Your server now has cryptographically signed tokens that prove the user's identity and can be used to access protected resources.

---

## **🏢 Corporate Application: How This Maps to Flyte**

```python
# This is exactly what flytectl does:

def flytectl_login():
    """How flytectl authenticates with corporate Flyte"""
    
    # 1. Generate PKCE parameters (same as our demo)
    code_verifier = generate_pkce_verifier()
    code_challenge = generate_pkce_challenge(code_verifier)
    
    # 2. Open browser to corporate Auth0/ADFS
    auth_url = f"{CORPORATE_AUTH_SERVER}/authorize?" + urlencode({
        'client_id': FLYTE_CLIENT_ID,
        'redirect_uri': 'http://localhost:8089/callback',
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256'
    })
    webbrowser.open(auth_url)
    
    # 3. Start local server to catch callback
    server = HTTPServer(('localhost', 8089), CallbackHandler)
    
    # 4. Exchange code for tokens (same as our demo)
    tokens = exchange_code_for_tokens(auth_code, code_verifier)
    
    # 5. Use tokens to call Flyte APIs
    flyte_response = requests.get(
        f"{FLYTE_API_SERVER}/api/v1/projects",
        headers={'Authorization': f'Bearer {tokens["access_token"]}'}
    )

def call_flyte_api(access_token):
    """Use the token to interact with Flyte"""
    headers = {'Authorization': f'Bearer {access_token}'}
    
    # List workflows
    workflows = requests.get(f"{FLYTE_API}/workflows", headers=headers)
    
    # Submit execution
    execution = requests.post(f"{FLYTE_API}/executions", 
                            headers=headers, 
                            json=workflow_spec)
```

---

## **🔒 Security Summary: Why This Works**

1. **PKCE Protection**: Even if someone intercepts the authorization code, they can't use it without the secret (code_verifier)

2. **Redirect URI Validation**: Prevents code theft by ensuring callbacks only go to registered URIs

3. **State Parameter**: Prevents CSRF attacks by ensuring the callback matches the original request

4. **JWT Signatures**: Tokens are cryptographically signed and can't be forged

5. **Time-Limited Codes**: Authorization codes expire quickly (usually 10 minutes)

6. **No Client Secrets**: Public clients (like CLIs) don't need to store secrets that could be compromised

---

## **🎯 The Complete Flow Visualization**

```
👤 User Browser    🖥️ Your Server    🏛️ Auth0 Server    🔐 Google
     │                   │                │                │
     │ 1. /login         │                │                │
     ├──────────────────▶│                │                │
     │                   │ 2. Generate    │                │
     │                   │    PKCE        │                │
     │                   │    secrets     │                │
     │ 3. Redirect to    │                │                │
     │    Auth0          │                │                │
     ◀──────────────────┤                │                │
     │                                    │                │
     │ 4. Auth request   │                │                │
     │    with challenge │                │                │
     ├───────────────────────────────────▶│                │
     │                   │                │ 5. Store       │
     │                   │                │    challenge   │
     │                   │                │                │
     │ 6. Login page     │                │                │
     ◀───────────────────────────────────┤                │
     │                   │                │                │
     │ 7. Authenticate   │                │                │
     ├───────────────────────────────────▶│ 8. Verify      │
     │                   │                ├───────────────▶│
     │                   │                │ 9. Confirm     │
     │                   │                ◀───────────────┤
     │                   │                │ 10. Generate   │
     │                   │                │     auth code  │
     │ 11. Callback      │                │                │
     │     with code     │                │                │
     ◀───────────────────────────────────┤                │
     │                   │                │                │
     │ 12. Send code to  │                │                │
     │     your server   │                │                │
     ├──────────────────▶│                │                │
     │                   │ 13. Exchange   │                │
     │                   │     code +     │                │
     │                   │     verifier   │                │
     │                   ├───────────────▶│                │
     │                   │                │ 14. Verify     │
     │                   │                │     PKCE       │
     │                   │ 15. JWT tokens │                │
     │                   ◀───────────────┤                │
     │ 16. Success page  │                │                │
     ◀──────────────────┤                │                │
```

---

## **🚀 Try It Yourself**

Run the demo:
```bash
python3 complete_oauth_demo.py
```

Then open: http://localhost:8091

Watch the console output to see each step of the PKCE flow in action!

---

**🎉 Congratulations!** You now understand the complete OAuth PKCE flow that powers enterprise authentication systems like Flyte, GitHub CLI, Google Cloud CLI, and thousands of other secure applications.
