#!/usr/bin/env python3
"""
DBBasic Auth Service - Clean authentication service on port 8010
Provides user authentication, session management, and authorization
"""

import json
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import duckdb
import jwt

# Configuration
PORT = 8010
DB_PATH = Path("data/auth.db")
SECRET_KEY = secrets.token_hex(32)  # In production, load from env
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24

# Ensure data directory exists
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

class AuthService:
    """Authentication service with JWT tokens and session management"""

    def __init__(self):
        self.init_database()

    def init_database(self):
        """Initialize auth database with users and sessions tables"""
        self.conn = duckdb.connect(str(DB_PATH), read_only=False)

        # Create users table
        self.conn.execute("""
            CREATE SEQUENCE IF NOT EXISTS users_seq START 1
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY DEFAULT nextval('users_seq'),
                username VARCHAR UNIQUE NOT NULL,
                email VARCHAR UNIQUE NOT NULL,
                password_hash VARCHAR NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                is_admin BOOLEAN DEFAULT FALSE
            )
        """)

        # Create sessions table
        self.conn.execute("""
            CREATE SEQUENCE IF NOT EXISTS sessions_seq START 1
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY DEFAULT nextval('sessions_seq'),
                user_id INTEGER NOT NULL,
                token VARCHAR UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                is_valid BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Create password reset tokens table
        self.conn.execute("""
            CREATE SEQUENCE IF NOT EXISTS password_resets_seq START 1
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS password_resets (
                id INTEGER PRIMARY KEY DEFAULT nextval('password_resets_seq'),
                user_id INTEGER NOT NULL,
                token VARCHAR UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                used BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Add indexes
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")

        # Create default admin user if none exists
        admin_exists = self.conn.execute("SELECT COUNT(*) FROM users WHERE is_admin = TRUE").fetchone()[0]
        if not admin_exists:
            self.create_user("admin", "admin@dbbasic.local", "admin123", is_admin=True)

    def hash_password(self, password):
        """Hash password with salt"""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}${pwd_hash.hex()}"

    def verify_password(self, password, password_hash):
        """Verify password against hash"""
        try:
            salt, pwd_hash = password_hash.split('$')
            test_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return test_hash.hex() == pwd_hash
        except:
            return False

    def create_user(self, username, email, password, is_admin=False):
        """Create new user"""
        try:
            password_hash = self.hash_password(password)
            self.conn.execute("""
                INSERT INTO users (username, email, password_hash, is_admin)
                VALUES (?, ?, ?, ?)
            """, (username, email, password_hash, is_admin))
            return {"success": True, "message": "User created successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def authenticate(self, username, password):
        """Authenticate user and return JWT token"""
        try:
            result = self.conn.execute("""
                SELECT id, username, email, password_hash, is_active, is_admin
                FROM users WHERE username = ? OR email = ?
            """, (username, username)).fetchone()

            if not result:
                return {"success": False, "error": "Invalid credentials"}

            user_id, username, email, password_hash, is_active, is_admin = result

            if not is_active:
                return {"success": False, "error": "Account disabled"}

            if not self.verify_password(password, password_hash):
                return {"success": False, "error": "Invalid credentials"}

            # Create JWT token
            payload = {
                "user_id": user_id,
                "username": username,
                "email": email,
                "is_admin": is_admin,
                "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
                "iat": datetime.utcnow()
            }

            token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)

            # Store session
            expires_at = datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS)
            self.conn.execute("""
                INSERT INTO sessions (user_id, token, expires_at)
                VALUES (?, ?, ?)
            """, (user_id, token, expires_at))

            return {
                "success": True,
                "token": token,
                "user": {
                    "id": user_id,
                    "username": username,
                    "email": email,
                    "is_admin": is_admin
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def verify_token(self, token):
        """Verify JWT token"""
        try:
            # Check if session exists and is valid
            result = self.conn.execute("""
                SELECT user_id, is_valid, expires_at
                FROM sessions WHERE token = ?
            """, (token,)).fetchone()

            if not result:
                return {"success": False, "error": "Invalid token"}

            user_id, is_valid, expires_at = result

            if not is_valid:
                return {"success": False, "error": "Token revoked"}

            if datetime.fromisoformat(str(expires_at)) < datetime.utcnow():
                return {"success": False, "error": "Token expired"}

            # Verify JWT
            payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])

            return {
                "success": True,
                "user": payload
            }
        except jwt.ExpiredSignatureError:
            return {"success": False, "error": "Token expired"}
        except jwt.InvalidTokenError:
            return {"success": False, "error": "Invalid token"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def logout(self, token):
        """Invalidate session"""
        try:
            self.conn.execute("""
                UPDATE sessions SET is_valid = FALSE
                WHERE token = ?
            """, (token,))
            return {"success": True, "message": "Logged out successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def change_password(self, user_id, old_password, new_password):
        """Change user password"""
        try:
            result = self.conn.execute("""
                SELECT password_hash FROM users WHERE id = ?
            """, (user_id,)).fetchone()

            if not result:
                return {"success": False, "error": "User not found"}

            if not self.verify_password(old_password, result[0]):
                return {"success": False, "error": "Invalid current password"}

            new_hash = self.hash_password(new_password)
            self.conn.execute("""
                UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_hash, user_id))

            return {"success": True, "message": "Password changed successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}

# Initialize auth service
auth = AuthService()

class AuthHandler(BaseHTTPRequestHandler):
    """HTTP request handler for auth service"""

    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/':
            self.serve_homepage()
        elif self.path == '/health':
            self.send_json({"status": "healthy", "service": "auth", "port": PORT})
        elif self.path.startswith('/api/verify'):
            self.verify_token_endpoint()
        else:
            self.send_404()

    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/api/register':
            self.register_endpoint()
        elif self.path == '/api/login':
            self.login_endpoint()
        elif self.path == '/api/logout':
            self.logout_endpoint()
        elif self.path == '/api/change-password':
            self.change_password_endpoint()
        else:
            self.send_404()

    def serve_homepage(self):
        """Serve auth service homepage"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>DBBasic Auth Service</title>
            <style>
                body { font-family: system-ui; margin: 40px; background: #f5f5f5; }
                .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                h1 { color: #333; }
                .form-group { margin-bottom: 20px; }
                label { display: block; margin-bottom: 5px; font-weight: 500; }
                input { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
                button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
                button:hover { background: #0056b3; }
                .message { padding: 10px; border-radius: 4px; margin-top: 20px; }
                .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
                .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
                .tabs { display: flex; gap: 10px; margin-bottom: 20px; }
                .tab { padding: 8px 16px; background: #e9ecef; cursor: pointer; border-radius: 4px; }
                .tab.active { background: #007bff; color: white; }
                .form { display: none; }
                .form.active { display: block; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔐 DBBasic Auth Service</h1>
                <p>Clean authentication service with JWT tokens</p>

                <div class="tabs">
                    <div class="tab active" onclick="showForm('login')">Login</div>
                    <div class="tab" onclick="showForm('register')">Register</div>
                </div>

                <div id="login-form" class="form active">
                    <h2>Login</h2>
                    <div class="form-group">
                        <label>Username or Email</label>
                        <input type="text" id="login-username" placeholder="admin">
                    </div>
                    <div class="form-group">
                        <label>Password</label>
                        <input type="password" id="login-password" placeholder="admin123">
                    </div>
                    <button onclick="login()">Login</button>
                </div>

                <div id="register-form" class="form">
                    <h2>Register</h2>
                    <div class="form-group">
                        <label>Username</label>
                        <input type="text" id="reg-username">
                    </div>
                    <div class="form-group">
                        <label>Email</label>
                        <input type="email" id="reg-email">
                    </div>
                    <div class="form-group">
                        <label>Password</label>
                        <input type="password" id="reg-password">
                    </div>
                    <button onclick="register()">Register</button>
                </div>

                <div id="message"></div>
            </div>

            <script>
                function showForm(type) {
                    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                    document.querySelectorAll('.form').forEach(f => f.classList.remove('active'));
                    event.target.classList.add('active');
                    document.getElementById(type + '-form').classList.add('active');
                }

                function showMessage(text, type) {
                    const msg = document.getElementById('message');
                    msg.className = 'message ' + type;
                    msg.textContent = text;
                    if (type === 'success') {
                        msg.innerHTML += '<br><br>Token: <code style="word-break: break-all;">' + (window.lastToken || '') + '</code>';
                    }
                }

                async function login() {
                    const response = await fetch('/api/login', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            username: document.getElementById('login-username').value,
                            password: document.getElementById('login-password').value
                        })
                    });
                    const data = await response.json();
                    if (data.success) {
                        window.lastToken = data.token;
                        showMessage('Login successful!', 'success');
                    } else {
                        showMessage(data.error, 'error');
                    }
                }

                async function register() {
                    const response = await fetch('/api/register', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            username: document.getElementById('reg-username').value,
                            email: document.getElementById('reg-email').value,
                            password: document.getElementById('reg-password').value
                        })
                    });
                    const data = await response.json();
                    if (data.success) {
                        showMessage('Registration successful! You can now login.', 'success');
                        showForm('login');
                    } else {
                        showMessage(data.error, 'error');
                    }
                }
            </script>
        </body>
        </html>
        """
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())

    def register_endpoint(self):
        """Handle user registration"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length))

            result = auth.create_user(
                body.get('username'),
                body.get('email'),
                body.get('password')
            )
            self.send_json(result)
        except Exception as e:
            self.send_json({"success": False, "error": str(e)})

    def login_endpoint(self):
        """Handle user login"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length))

            result = auth.authenticate(
                body.get('username'),
                body.get('password')
            )
            self.send_json(result)
        except Exception as e:
            self.send_json({"success": False, "error": str(e)})

    def logout_endpoint(self):
        """Handle user logout"""
        try:
            token = self.headers.get('Authorization', '').replace('Bearer ', '')
            if not token:
                self.send_json({"success": False, "error": "No token provided"})
                return

            result = auth.logout(token)
            self.send_json(result)
        except Exception as e:
            self.send_json({"success": False, "error": str(e)})

    def verify_token_endpoint(self):
        """Verify auth token"""
        try:
            token = self.headers.get('Authorization', '').replace('Bearer ', '')
            if not token:
                self.send_json({"success": False, "error": "No token provided"})
                return

            result = auth.verify_token(token)
            self.send_json(result)
        except Exception as e:
            self.send_json({"success": False, "error": str(e)})

    def change_password_endpoint(self):
        """Handle password change"""
        try:
            token = self.headers.get('Authorization', '').replace('Bearer ', '')
            if not token:
                self.send_json({"success": False, "error": "Not authenticated"})
                return

            # Verify token first
            auth_result = auth.verify_token(token)
            if not auth_result["success"]:
                self.send_json(auth_result)
                return

            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length))

            result = auth.change_password(
                auth_result["user"]["user_id"],
                body.get('old_password'),
                body.get('new_password')
            )
            self.send_json(result)
        except Exception as e:
            self.send_json({"success": False, "error": str(e)})

    def send_json(self, data):
        """Send JSON response"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def send_404(self):
        """Send 404 response"""
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"Not Found")

    def log_message(self, format, *args):
        """Custom log format"""
        print(f"[Auth Service] {format % args}")

if __name__ == "__main__":
    server = HTTPServer(('', PORT), AuthHandler)
    print(f"🔐 DBBasic Auth Service running on port {PORT}")
    print(f"   http://localhost:{PORT}")
    print("\nDefault admin credentials:")
    print("  Username: admin")
    print("  Password: admin123")
    print("\nAPI Endpoints:")
    print("  POST /api/register - Register new user")
    print("  POST /api/login - Login and get JWT token")
    print("  POST /api/logout - Invalidate session")
    print("  GET /api/verify - Verify token")
    print("  POST /api/change-password - Change password")
    server.serve_forever()