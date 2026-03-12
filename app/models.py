# app/models.py
from app.extensions import db
from flask_login import UserMixin
from datetime import datetime, timedelta
from app import db, login_manager


def agora_brasil():
    return datetime.utcnow() - timedelta(hours=3)


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

class Usuario(UserMixin, db.Model):
    """Modelo de usuário - autenticação via Google"""
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    google_id = db.Column(db.String(100), unique=True)
    foto_perfil = db.Column(db.String(200))
    data_cadastro = db.Column(db.DateTime, default=agora_brasil)
    ultimo_acesso = db.Column(db.DateTime, default=agora_brasil, onupdate=agora_brasil)
    
    # Relacionamento com pedidos
    pedidos = db.relationship('Pedido', backref='usuario_criador', lazy=True)
    entregas = db.relationship('Entrega', backref='entregador', lazy=True)
    
    def __repr__(self):
        return f'<Usuario {self.email}>'

class Pedido(db.Model):
    """Modelo de pedido de água/gás"""
    __tablename__ = 'pedidos'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo_acompanhamento = db.Column(db.String(10), unique=True, nullable=False)
    
    # Informações do pedido
    volumes = db.Column(db.Integer, nullable=False)
    produto = db.Column(db.String(50), nullable=False)  # Água ou Gás
    nome_cliente = db.Column(db.String(100), nullable=False)
    endereco_cliente = db.Column(db.String(200), nullable=False)
    valor_total = db.Column(db.Float, nullable=False)
    forma_pagamento = db.Column(db.String(50), nullable=False)  # Dinheiro, Cartão, Pix, etc
    status_pagamento = db.Column(db.String(20), default='pendente')  # pendente, pago
    
    # Status do pedido
    status = db.Column(db.String(20), default='processo')  # processo, caminho, entregue
    
    # Datas e timestamps
    data_criacao = db.Column(db.DateTime, default=agora_brasil)
    data_atualizacao = db.Column(db.DateTime, default=agora_brasil, onupdate=agora_brasil)
    data_processo = db.Column(db.DateTime)
    data_caminho = db.Column(db.DateTime)
    data_entrega = db.Column(db.DateTime)
    
    # Chaves estrangeiras
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    # Relacionamentos
    entregas = db.relationship('Entrega', backref='pedido', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Pedido {self.codigo_acompanhamento} - {self.nome_cliente}>'

class Entrega(db.Model):
    """Modelo de entrega - registro de quem entregou"""
    __tablename__ = 'entregas'
    
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    data_hora = db.Column(db.DateTime, default=agora_brasil)
    observacao = db.Column(db.String(200))
    
    def __repr__(self):
        return f'<Entrega {self.pedido_id} - {self.data_hora}>'