from flask import Flask


def create_app():
    app = Flask(__name__)

    from backend.endpoints import endpoints

    app.register_blueprint(endpoints)
    return app
