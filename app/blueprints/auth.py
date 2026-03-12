# app/blueprints/auth.py
from flask import Blueprint, redirect, url_for, flash, render_template, request, session
from flask_login import login_user, logout_user, login_required
from app.models import Usuario, agora_brasil
from app.extensions import db
from datetime import datetime
import os
import requests
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import urllib.parse

auth_bp = Blueprint('auth', __name__)

def get_google_auth_url():
    """Gera URL de autenticação do Google"""
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    
    params = {
        'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
        'redirect_uri': os.environ.get('GOOGLE_REDIRECT_URI'),
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'offline',
        'prompt': 'consent'
    }
    
    return f"{base_url}?{urllib.parse.urlencode(params)}"

def exchange_code_for_token(code):
    """Troca o código de autorização por um token"""
    token_url = "https://oauth2.googleapis.com/token"
    
    data = {
        'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
        'client_secret': os.environ.get('GOOGLE_CLIENT_SECRET'),
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': os.environ.get('GOOGLE_REDIRECT_URI')
    }
    
    response = requests.post(token_url, data=data)
    return response.json()

def validate_google_token(id_token_str):
    """Valida o token ID do Google"""
    idinfo = id_token.verify_oauth2_token(
        id_token_str,
        google_requests.Request(),
        os.environ.get('GOOGLE_CLIENT_ID')
    )
    return idinfo

@auth_bp.route('/login')
def login():
    """Página de login"""
    return render_template('auth/login.html', 
                         google_auth_url=get_google_auth_url())

@auth_bp.route('/login/callback')
def login_callback():
    """Callback após autenticação do Google"""
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        flash(f'Erro na autenticação: {error}', 'danger')
        return redirect(url_for('auth.login'))
    
    if not code:
        flash('Falha na autenticação: código não recebido', 'danger')
        return redirect(url_for('auth.login'))
    
    try:
        # Troca o código por um token
        token_response = exchange_code_for_token(code)
        
        if 'error' in token_response:
            flash(f'Erro ao obter token: {token_response.get("error")}', 'danger')
            return redirect(url_for('auth.login'))
        
        # Valida o token e obtém informações do usuário
        user_info = validate_google_token(token_response['id_token'])
        
        # Verifica se usuário já existe
        usuario = Usuario.query.filter_by(email=user_info['email']).first()
        print(user_info)
        if not usuario:
            # Cria novo usuário
            usuario = Usuario(
                email=user_info['email'],
                nome=user_info['name'],
                google_id=user_info['sub'],
                foto_perfil=user_info.get('picture', '')
            )
            db.session.add(usuario)
            db.session.commit()
            session.permanent = True  # Torna a sessão permanente para usar o tempo de expiração definido

            
            flash('Bem-vindo ao sistema!', 'success')
        else:
            # Atualiza informações do usuário existente
            usuario.nome = user_info['name']
            usuario.foto_perfil = user_info.get('picture', '')
            usuario.ultimo_acesso = agora_brasil()
            db.session.commit()
            session.permanent = True  # Torna a sessão permanente para usar o tempo de expiração definido

            
            flash('Login realizado com sucesso!', 'success')
        
        # Faz login do usuário
        login_user(usuario)
        return redirect(url_for('main.index'))
        
    except Exception as e:
        print(f"Erro na autenticação: {e}")
        flash('Erro na autenticação', 'danger')
        return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout do usuário"""
    logout_user()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('main.index'))