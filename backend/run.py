"""
Vedang Backend — Entry point
Starts the Flask application server.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import build_app
from app.config import Settings


def main():
    settings = Settings()
    missing = settings.check_required()
    if missing:
        print("⚠️  Warning — missing config (LLM calls will fail):")
        for m in missing:
            print(f"   • {m}")
        print("   Edit .env to fix this.\n")

    application = build_app()
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", "5001"))
    application.run(host=host, port=port, debug=settings.DEBUG, threaded=True)


if __name__ == "__main__":
    main()
