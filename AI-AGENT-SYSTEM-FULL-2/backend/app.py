#!/usr/bin/env python3
"""
AI Agent System - Flask Backend Application.

Security-sensitive configuration is loaded from environment variables and
validated before the Flask application is created.
"""

import os
import sys
from datetime import datetime, timedelta

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager

load_dotenv()

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.config import load_settings
from src.models import db

settings = load_settings()

app = Flask(__name__, static_folder="static")
app.config["SECRET_KEY"] = settings.secret_key
app.config["SQLALCHEMY_DATABASE_URI"] = settings.database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = settings.jwt_secret_key
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(seconds=settings.jwt_access_token_expires)
app.config["ALLOW_PUBLIC_REGISTRATION"] = settings.allow_public_registration

db.init_app(app)
jwt = JWTManager(app)
CORS(
    app,
    origins=list(settings.cors_origins),
    supports_credentials=settings.cors_supports_credentials,
)

from src.models.task import Task
from src.models.user import User
from src.routes.auth import auth_bp
from src.routes.chat import chat_bp
from src.routes.tasks import tasks_bp
from src.routes.telegram import telegram_bp

app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(tasks_bp, url_prefix="/api/tasks")
app.register_blueprint(chat_bp, url_prefix="/api/chat")
app.register_blueprint(telegram_bp, url_prefix="/api/telegram")


@app.before_request
def protect_public_registration():
    """Keep registration disabled by default and prevent client-selected admin roles."""

    if request.method != "POST" or request.path != "/api/auth/register":
        return None

    if not app.config["ALLOW_PUBLIC_REGISTRATION"]:
        return jsonify({
            "status": "error",
            "message": "Public registration is disabled.",
        }), 403

    payload = request.get_json(silent=True) or {}
    requested_role = payload.get("role")
    if requested_role not in (None, "team"):
        return jsonify({
            "status": "error",
            "message": "Public registration can only create team accounts.",
        }), 403

    return None


@app.after_request
def add_security_headers(response):
    """Apply inexpensive browser security headers to every response."""

    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return response


@app.route("/api/health")
def health_check():
    """Return non-sensitive service readiness information."""

    return jsonify({
        "status": "healthy",
        "message": "AI Agent System Backend is running",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment,
        "integrations": {
            "openai_configured": bool(settings.openai_api_key),
            "telegram_configured": settings.telegram_configured,
        },
    })


@app.route("/")
def serve_frontend():
    """Serve React frontend."""

    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path:path>")
def serve_static(path):
    """Serve static files."""

    return send_from_directory(app.static_folder, path)


def initialize_database():
    """Create tables and optionally seed explicitly enabled development data."""

    with app.app_context():
        try:
            db.create_all()

            if not settings.allow_demo_data:
                print("Database tables ready; demo data seeding is disabled.")
                return

            admin_user = User.query.filter_by(username="admin").first()
            if admin_user:
                print("Database already contains the demo admin user.")
                return

            admin_user = User(
                username="admin",
                email="admin@aiagent.local",
                role="admin",
            )
            admin_user.set_password(settings.demo_admin_password)
            db.session.add(admin_user)

            team_members = [
                {"username": "john_doe", "email": "john@aiagent.local"},
                {"username": "jane_smith", "email": "jane@aiagent.local"},
                {"username": "mike_wilson", "email": "mike@aiagent.local"},
            ]
            for member_data in team_members:
                member = User(
                    username=member_data["username"],
                    email=member_data["email"],
                    role="team",
                )
                member.set_password(settings.demo_user_password)
                db.session.add(member)

            db.session.flush()
            users_by_name = {
                user.username: user.id
                for user in User.query.filter(User.username.in_([
                    "admin", "john_doe", "jane_smith", "mike_wilson"
                ])).all()
            }

            sample_tasks = [
                {
                    "title": "Setup Development Environment",
                    "description": "Configure development tools and environment for the project",
                    "priority": "high",
                    "status": "completed",
                    "assigned_to": users_by_name["john_doe"],
                    "created_by": users_by_name["admin"],
                    "due_date": datetime.utcnow() - timedelta(days=1),
                    "completed_at": datetime.utcnow() - timedelta(hours=2),
                },
                {
                    "title": "Design Database Schema",
                    "description": "Create comprehensive database schema for the AI Agent System",
                    "priority": "high",
                    "status": "in_progress",
                    "assigned_to": users_by_name["jane_smith"],
                    "created_by": users_by_name["admin"],
                    "due_date": datetime.utcnow() + timedelta(days=2),
                },
                {
                    "title": "Implement User Authentication",
                    "description": "Build JWT-based authentication system with role management",
                    "priority": "urgent",
                    "status": "pending",
                    "assigned_to": users_by_name["mike_wilson"],
                    "created_by": users_by_name["admin"],
                    "due_date": datetime.utcnow() + timedelta(days=3),
                },
            ]
            for task_data in sample_tasks:
                db.session.add(Task(**task_data))

            db.session.commit()
            print("Development demo data initialized.")
        except Exception:
            db.session.rollback()
            raise


if __name__ == "__main__":
    initialize_database()
    print("Starting AI Agent System Backend")
    print(f"Server: http://{settings.host}:{settings.port}")
    print(f"Debug mode: {settings.debug}")
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
