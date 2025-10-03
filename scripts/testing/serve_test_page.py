#!/usr/bin/env python3
"""
Simple HTTP server to serve the WebRTC API test page
"""

import http.server
import socketserver
import webbrowser
import os
import sys

PORT = 8081

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers to allow cross-origin requests
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

def main():
    # Change to the directory containing the test page
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Check if the test page exists
    if not os.path.exists('webrtc-api-test.html'):
        print("❌ webrtc-api-test.html not found!")
        sys.exit(1)
    
    with socketserver.TCPServer(("0.0.0.0", PORT), MyHTTPRequestHandler) as httpd:
        print(f"🌐 WebRTC API Test Server running at:")
        print(f"   http://localhost:{PORT}/webrtc-api-test.html")
        print(f"   http://127.0.0.1:{PORT}/webrtc-api-test.html")
        print(f"   http://10.30.250.245:{PORT}/webrtc-api-test.html")
        print(f"\n📱 Open the URL in your browser to test the WebRTC API Gateway")
        print(f"⏹️  Press Ctrl+C to stop the server")
        
        try:
            # Try to open browser automatically
            webbrowser.open(f'http://localhost:{PORT}/webrtc-api-test.html')
        except:
            pass
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n⏹️ Server stopped")

if __name__ == "__main__":
    main()
