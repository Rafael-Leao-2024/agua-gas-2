# app/__init__.py
from flask import Flask, session
from config import Config
from app.extensions import db, migrate, login_manager
from datetime import timedelta
import os

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=600)  # Define o tempo de expiração da sessão
    
    # Inicializa extensões
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'
    
    # Registra blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.pedidos import pedidos_bp
    from app.blueprints.main import main_bp
    from app.blueprints.financas import financas_bp
    from app.blueprints.despesas import despesas_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(pedidos_bp, url_prefix='/pedidos')
    app.register_blueprint(main_bp)
    app.register_blueprint(financas_bp)
    app.register_blueprint(despesas_bp)
    
    return app