from flask import Flask

def create_app() -> Flask:
    app = Flask(__name__)

    from kycc.routes.health import bp as health_bp
    app.register_blueprint(health_bp)

    return app
