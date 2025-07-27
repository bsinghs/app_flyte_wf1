#!/usr/bin/env python3
"""
Simple OAuth PKCE demonstration server
This will show you exactly how the OAuth flow works locally
"""

import base64
import hashlib
import json
import secrets
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time

# Auth0 Configuration
AUTH0_DOMAIN = "dev-a85i5cax3v3cy6l4.us.auth0.com"
CLIENT_ID = "QhgXEVKKNmJzLwQxZeUuxtfqXlf619S5"
REDIRECT_URI = "http://localhost:8090/callback"
SCOPE = "openid profile email"

class OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/callback'):
            self.handle_callback()
        elif self.path == '/':
            self.handle_home()
        elif self.path == '/login':
            self.handle_login()
        else:
            self.send_error(404)
    
    def handle_home(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = """
        <html>
        <head><title>OAuth PKCE Demo</title></head>
        <body>
            <h1>OAuth PKCE Flow Demonstration</h1>
            <p>This demonstrates the same flow that flytectl would use.</p>
            <a href="/login">🔐 Start OAuth Login (PKCE)</a>
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
        
        # Store for later verification (in real app, use session storage)
        global stored_verifier
        stored_verifier = code_verifier
        
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
        
        print(f"\n🔑 PKCE Parameters Generated:")
        print(f"   Code Verifier: {code_verifier[:20]}...")
        print(f"   Code Challenge: {code_challenge[:20]}...")
        print(f"\n🌐 Redirecting to Auth0: {auth_url[:50]}...")
        
        # Step 3: Redirect to Auth0
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
        print(f"\n✅ Received authorization code: {auth_code[:20]}...")
        
        # Step 4: Exchange code for token (would happen here)
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = f"""
        <html>
        <head><title>OAuth Success!</title></head>
        <body>
            <h1>🎉 OAuth PKCE Flow Complete!</h1>
            <h2>What Just Happened:</h2>
            <ol>
                <li><strong>Code Verifier Generated:</strong> {stored_verifier[:30]}...</li>
                <li><strong>Code Challenge Created:</strong> SHA256 hash of verifier</li>
                <li><strong>Redirected to Auth0:</strong> With challenge (not verifier!)</li>
                <li><strong>User Authenticated:</strong> Via Google login</li>
                <li><strong>Authorization Code Received:</strong> {auth_code[:30]}...</li>
                <li><strong>Next Step:</strong> Exchange code + verifier for JWT token</li>
            </ol>
            
            <h2>🔐 Security Benefits:</h2>
            <ul>
                <li>✅ No client secrets stored</li>
                <li>✅ Code challenge prevents interception attacks</li>
                <li>✅ Only we have the code verifier to complete exchange</li>
            </ul>
            
            <p><strong>This is exactly how flytectl would authenticate with Flyte!</strong></p>
        </body>
        </html>
        """
        self.wfile.write(html.encode())
        
        # Shutdown server after success
        threading.Thread(target=self.server.shutdown).start()

def main():
    print("🚀 Starting OAuth PKCE Demonstration Server...")
    print("📍 Open your browser to: http://localhost:8090")
    print("🔍 This will show you the exact OAuth flow that flytectl uses!")
    
    server = HTTPServer(('localhost', 8090), OAuthHandler)
    
    # Auto-open browser
    threading.Timer(1, lambda: webbrowser.open('http://localhost:8090')).start()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        print("\n✅ OAuth demonstration complete!")

if __name__ == '__main__':
    stored_verifier = None
    main()
