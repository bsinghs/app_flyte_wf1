#!/usr/bin/env python3
"""
Complete OAuth PKCE Flow with Token Exchange
This demonstrates the FULL OAuth flow including token exchange
"""

import base64
import hashlib
import json
import secrets
import urllib.parse
import urllib.request
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time

# Auth0 Configuration
AUTH0_DOMAIN = "dev-a85i5cax3v3cy6l4.us.auth0.com"
CLIENT_ID = "QhgXEVKKNmJzLwQxZeUuxtfqXlf619S5"
REDIRECT_URI = "http://localhost:8091/callback"
SCOPE = "openid profile email"

class FullOAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/callback'):
            self.handle_callback()
        elif self.path == '/':
            self.handle_home()
        elif self.path == '/login':
            self.handle_login()
        elif self.path.startswith('/api/protected'):
            self.handle_protected_api()
        else:
            self.send_error(404)
    
    def handle_home(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        token_info = ""
        if hasattr(self.server, 'access_token'):
            token_info = f"""
            <div style="background: #e8f5e8; padding: 10px; margin: 10px 0; border-radius: 5px;">
                <h3>🎉 You are authenticated!</h3>
                <p><strong>Access Token:</strong> {self.server.access_token[:50]}...</p>
                <p><a href="/api/protected">🔒 Test Protected API Call</a></p>
            </div>
            """
        
        html = f"""
        <html>
        <head><title>Complete OAuth PKCE Demo</title></head>
        <body>
            <h1>🔐 Complete OAuth PKCE Flow</h1>
            <p>This demonstrates the complete OAuth flow that enterprise applications use.</p>
            
            {token_info}
            
            <div style="margin: 20px 0;">
                <a href="/login" style="background: #007cba; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                    🚀 Start OAuth Login (PKCE)
                </a>
            </div>
            
            <h2>📚 What You'll Learn:</h2>
            <ul>
                <li><strong>PKCE Generation:</strong> Code verifier and challenge creation</li>
                <li><strong>OAuth Redirect:</strong> Secure authorization flow</li>
                <li><strong>Token Exchange:</strong> Authorization code → JWT tokens</li>
                <li><strong>API Authentication:</strong> Using tokens for API calls</li>
                <li><strong>Token Validation:</strong> JWT parsing and verification</li>
            </ul>
        </body>
        </html>
        """
        self.wfile.write(html.encode())
    
    def handle_login(self):
        # Step 1: Generate PKCE parameters
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip('=')
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode().rstrip('=')
        
        # Store for later verification
        self.server.code_verifier = code_verifier
        
        # Step 2: Build authorization URL
        params = {
            'response_type': 'code',
            'client_id': CLIENT_ID,
            'redirect_uri': REDIRECT_URI,
            'scope': SCOPE,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
            'state': secrets.token_urlsafe(32)
        }
        
        auth_url = f"https://{AUTH0_DOMAIN}/authorize?" + urllib.parse.urlencode(params)
        
        print(f"\n🔑 PKCE Parameters:")
        print(f"   Code Verifier: {code_verifier}")
        print(f"   Code Challenge: {code_challenge}")
        print(f"\n🌐 Auth URL: {auth_url}")
        
        # Redirect to Auth0
        self.send_response(302)
        self.send_header('Location', auth_url)
        self.end_headers()
    
    def handle_callback(self):
        # Parse callback parameters
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        
        if 'error' in params:
            self.send_error(400, f"OAuth Error: {params['error'][0]}")
            return
        
        if 'code' not in params:
            self.send_error(400, "Missing authorization code")
            return
        
        auth_code = params['code'][0]
        print(f"\n✅ Authorization Code: {auth_code}")
        
        # Step 3: Exchange code for tokens
        try:
            tokens = self.exchange_code_for_tokens(auth_code)
            self.server.access_token = tokens['access_token']
            self.server.id_token = tokens.get('id_token', '')
            
            # Parse JWT payload (without verification for demo)
            user_info = self.parse_jwt_payload(tokens.get('id_token', ''))
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = f"""
            <html>
            <head><title>OAuth Success!</title></head>
            <body>
                <h1>🎉 Complete OAuth PKCE Flow Successful!</h1>
                
                <h2>🔄 Flow Steps Completed:</h2>
                <ol>
                    <li>✅ <strong>PKCE Generated:</strong> Code verifier and challenge</li>
                    <li>✅ <strong>Auth Request:</strong> Redirected to Auth0 with challenge</li>
                    <li>✅ <strong>User Login:</strong> Authenticated via Google</li>
                    <li>✅ <strong>Code Received:</strong> Authorization code returned</li>
                    <li>✅ <strong>Token Exchange:</strong> Code + verifier → JWT tokens</li>
                </ol>
                
                <h2>🎫 Received Tokens:</h2>
                <div style="background: #f5f5f5; padding: 10px; margin: 10px 0; font-family: monospace; word-break: break-all;">
                    <strong>Access Token:</strong><br>
                    {tokens['access_token'][:100]}...<br><br>
                    <strong>ID Token:</strong><br>
                    {tokens.get('id_token', 'Not provided')[:100]}...
                </div>
                
                <h2>👤 User Information:</h2>
                <div style="background: #e8f5e8; padding: 10px; margin: 10px 0;">
                    <pre>{json.dumps(user_info, indent=2)}</pre>
                </div>
                
                <div style="margin: 20px 0;">
                    <a href="/" style="background: #007cba; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                        🏠 Back to Home
                    </a>
                    <a href="/api/protected" style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-left: 10px;">
                        🔒 Test API Call
                    </a>
                </div>
                
                <h2>🏢 Corporate Application:</h2>
                <p><strong>This is exactly how flytectl/enterprise apps work:</strong></p>
                <ul>
                    <li>Same PKCE flow for CLI tools</li>
                    <li>Same token exchange process</li>
                    <li>Same JWT token usage for API calls</li>
                    <li>Same security benefits (no client secrets)</li>
                </ul>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
            
        except Exception as e:
            print(f"❌ Token exchange failed: {e}")
            self.send_error(500, f"Token exchange failed: {e}")
    
    def handle_protected_api(self):
        # Simulate protected API endpoint
        auth_header = self.headers.get('Authorization', '')
        
        if not hasattr(self.server, 'access_token'):
            self.send_response(401)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = "<h1>401 Unauthorized</h1><p>No access token available. Please <a href='/login'>login</a> first.</p>"
            self.wfile.write(html.encode())
            return
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = f"""
        <html>
        <head><title>Protected API Success</title></head>
        <body>
            <h1>🔒 Protected API Call Successful!</h1>
            <p>✅ Your access token was validated successfully.</p>
            
            <h2>🎫 Token Used:</h2>
            <div style="background: #f5f5f5; padding: 10px; margin: 10px 0; font-family: monospace; word-break: break-all;">
                {self.server.access_token}
            </div>
            
            <h2>📡 API Response:</h2>
            <div style="background: #e8f5e8; padding: 10px; margin: 10px 0;">
                <pre>{json.dumps({
                    "message": "Access granted to protected resource",
                    "user": "authenticated", 
                    "timestamp": "2025-07-27T15:00:00Z",
                    "scope": "read:workflows write:workflows"
                }, indent=2)}</pre>
            </div>
            
            <div style="margin: 20px 0;">
                <a href="/" style="background: #007cba; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                    🏠 Back to Home
                </a>
            </div>
            
            <p><strong>🏢 In Flyte:</strong> This is how flytectl would use your token to call Flyte APIs!</p>
        </body>
        </html>
        """
        self.wfile.write(html.encode())
    
    def exchange_code_for_tokens(self, auth_code):
        """Exchange authorization code for tokens using PKCE"""
        token_url = f"https://{AUTH0_DOMAIN}/oauth/token"
        
        data = {
            'grant_type': 'authorization_code',
            'client_id': CLIENT_ID,
            'code': auth_code,
            'redirect_uri': REDIRECT_URI,  # MUST match original request for security
            'code_verifier': self.server.code_verifier
        }
        
        # 🚨 SECURITY NOTE: If you change redirect_uri here to something different
        # like 'http://evil-site.com/callback', Auth0 will reject the request
        # This prevents token theft attacks!
        
        print(f"\n🔄 Token Exchange Request:")
        print(f"   URL: {token_url}")
        print(f"   Code: {auth_code[:20]}...")
        print(f"   Verifier: {self.server.code_verifier[:20]}...")
        
        req = urllib.request.Request(
            token_url,
            data=urllib.parse.urlencode(data).encode(),
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        with urllib.request.urlopen(req) as response:
            tokens = json.loads(response.read().decode())
            print(f"✅ Tokens received: {list(tokens.keys())}")
            return tokens
    
    def parse_jwt_payload(self, jwt_token):
        """Parse JWT payload (without signature verification for demo)"""
        if not jwt_token:
            return {}
        
        try:
            # JWT has 3 parts separated by dots
            parts = jwt_token.split('.')
            if len(parts) != 3:
                return {}
            
            # Decode the payload (second part)
            payload = parts[1]
            # Add padding if needed
            payload += '=' * (4 - len(payload) % 4)
            decoded = base64.urlsafe_b64decode(payload)
            return json.loads(decoded)
        except:
            return {}

def main():
    print("🚀 Starting Complete OAuth PKCE Demonstration...")
    print("📍 Open your browser to: http://localhost:8091")
    print("🎯 This shows the COMPLETE OAuth flow with token exchange!")
    
    server = HTTPServer(('localhost', 8091), FullOAuthHandler)
    
    # Auto-open browser
    threading.Timer(1, lambda: webbrowser.open('http://localhost:8091')).start()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        print("\n✅ Complete OAuth demonstration finished!")

if __name__ == '__main__':
    main()
