from flask import Flask
from dotenv import load_dotenv

from app.config import Config
from app.extensions import db
from app.routes import main_bp
from app.security import seed_default_admin
from app.services.ticket_service import is_solved, status_label


def create_app() -> Flask:
    load_dotenv()
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(Config)

    db.init_app(app)
    app.register_blueprint(main_bp)

    @app.context_processor
    def inject_template_helpers():
        return {"status_label": status_label, "is_solved": is_solved}

    with app.app_context():
        db.create_all()
        seed_default_admin()

    return app


app = create_app()
