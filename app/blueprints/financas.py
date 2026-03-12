# app/blueprints/financas.py
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app.models import Pedido, db
from datetime import datetime
from sqlalchemy import func, extract
from app.models import agora_brasil



financas_bp = Blueprint('financas', __name__, url_prefix='/financas')

@financas_bp.route('/')
@login_required
def dashboard():
    """Dashboard principal de finanças"""
    return render_template('financas/dashboard.html')

@financas_bp.route('/pendentes')
@login_required
def pendentes():
    """Pedidos com pagamento pendente"""
    return render_template('financas/pendentes.html')

@financas_bp.route('/pagos')
@login_required
def pagos():
    """Pedidos com pagamento confirmado"""
    return render_template('financas/pagos.html')

@financas_bp.route('/mensal')
@login_required
def mensal():
    """Visão mensal de faturamento"""
    return render_template('financas/mensal.html')

@financas_bp.route('/devedores')
@login_required
def devedores():
    """Clientes com pendências (fiado)"""
    return render_template('financas/devedores.html')

# ==================== API ROUTES ====================

@financas_bp.route('/api/resumo-diario')
@login_required
def api_resumo_diario():
    """Resumo do dia atual"""
    from app.models import agora_brasil
    hoje = agora_brasil().date()
    
    # Total do dia
    total_dia = db.session.query(func.sum(Pedido.valor_total))\
        .filter(func.date(Pedido.data_criacao) == hoje)\
        .scalar() or 0
    
    # Pendentes do dia
    pendentes_dia = db.session.query(func.sum(Pedido.valor_total))\
        .filter(
            func.date(Pedido.data_criacao) == hoje,
            Pedido.status_pagamento == 'pendente'
        ).scalar() or 0
    
    # Pagos do dia
    pagos_dia = db.session.query(func.sum(Pedido.valor_total))\
        .filter(
            func.date(Pedido.data_criacao) == hoje,
            Pedido.status_pagamento == 'pago'
        ).scalar() or 0
    
    # Quantidades
    qtd_total = Pedido.query.filter(func.date(Pedido.data_criacao) == hoje).count()
    qtd_pendentes = Pedido.query.filter(
        func.date(Pedido.data_criacao) == hoje,
        Pedido.status_pagamento == 'pendente'
    ).count()
    qtd_pagos = Pedido.query.filter(
        func.date(Pedido.data_criacao) == hoje,
        Pedido.status_pagamento == 'pago'
    ).count()
    
    return jsonify({
        'total_dia': float(total_dia),
        'pendentes_dia': float(pendentes_dia),
        'pagos_dia': float(pagos_dia),
        'qtd_total': qtd_total,
        'qtd_pendentes': qtd_pendentes,
        'qtd_pagos': qtd_pagos
    })

@financas_bp.route('/api/resumo-mensal')
@login_required
def api_resumo_mensal():
    """Resumo do mês atual"""
    hoje = agora_brasil()
    print(f"Data atual: {hoje}")  # Debug para verificar a data atual
    mes_atual = hoje.month
    ano_atual = hoje.year
    
    # Total do mês
    total_mes = db.session.query(func.sum(Pedido.valor_total))\
        .filter(
            extract('month', Pedido.data_criacao) == mes_atual,
            extract('year', Pedido.data_criacao) == ano_atual
        ).scalar() or 0
    
    # Pendentes do mês
    pendentes_mes = db.session.query(func.sum(Pedido.valor_total))\
        .filter(
            extract('month', Pedido.data_criacao) == mes_atual,
            extract('year', Pedido.data_criacao) == ano_atual,
            Pedido.status_pagamento == 'pendente'
        ).scalar() or 0
    
    # Pagos do mês
    pagos_mes = db.session.query(func.sum(Pedido.valor_total))\
        .filter(
            extract('month', Pedido.data_criacao) == mes_atual,
            extract('year', Pedido.data_criacao) == ano_atual,
            Pedido.status_pagamento == 'pago'
        ).scalar() or 0
    
    return jsonify({
        'total_mes': float(total_mes),
        'pendentes_mes': float(pendentes_mes),
        'pagos_mes': float(pagos_mes)
    })

@financas_bp.route('/api/pedidos-pendentes')
@login_required
def api_pedidos_pendentes():
    """Lista pedidos com pagamento pendente"""
    filtro = request.args.get('filtro', 'todos')  # hoje, mes, todos
    
    query = Pedido.query.filter(Pedido.status_pagamento == 'pendente')
    
    if filtro == 'hoje':
        hoje = agora_brasil().date()
        query = query.filter(func.date(Pedido.data_criacao) == hoje)
    elif filtro == 'mes':
        mes_atual = agora_brasil().month
        ano_atual = agora_brasil().year
        query = query.filter(
            extract('month', Pedido.data_criacao) == mes_atual,
            extract('year', Pedido.data_criacao) == ano_atual
        )
    
    pedidos = query.order_by(Pedido.data_criacao.desc()).all()
    
    return jsonify([{
        'id': p.id,
        'codigo': p.codigo_acompanhamento,
        'cliente': p.nome_cliente,
        'produto': p.produto,
        'volumes': p.volumes,
        'valor': float(p.valor_total),
        'data': p.data_criacao.strftime('%d/%m/%Y'),
        'forma_pagamento': p.forma_pagamento,
        'status_pedido': p.status
    } for p in pedidos])

@financas_bp.route('/api/pedidos-pagos')
@login_required
def api_pedidos_pagos():
    """Lista pedidos com pagamento confirmado"""
    filtro = request.args.get('filtro', 'todos')
    
    query = Pedido.query.filter(Pedido.status_pagamento == 'pago')
    
    if filtro == 'hoje':
        hoje = agora_brasil().date()
        query = query.filter(func.date(Pedido.data_criacao) == hoje)
    elif filtro == 'mes':
        mes_atual = agora_brasil().month
        ano_atual = agora_brasil().year
        query = query.filter(
            extract('month', Pedido.data_criacao) == mes_atual,
            extract('year', Pedido.data_criacao) == ano_atual
        )
    
    pedidos = query.order_by(Pedido.data_criacao.desc()).all()
    
    return jsonify([{
        'id': p.id,
        'codigo': p.codigo_acompanhamento,
        'cliente': p.nome_cliente,
        'produto': p.produto,
        'volumes': p.volumes,
        'valor': float(p.valor_total),
        'data': p.data_criacao.strftime('%d/%m/%Y'),
        'forma_pagamento': p.forma_pagamento,
        'status_pedido': p.status
    } for p in pedidos])

@financas_bp.route('/api/devedores')
@login_required
def api_devedores():
    """Clientes com fiado pendente"""
    devedores = Pedido.query.filter(
        Pedido.forma_pagamento == 'Fiado',
        Pedido.status_pagamento == 'pendente'
    ).order_by(Pedido.nome_cliente).all()
    
    # Agrupa por cliente
    clientes = {}
    for p in devedores:
        if p.nome_cliente not in clientes:
            clientes[p.nome_cliente] = {
                'cliente': p.nome_cliente,
                'total': 0,
                'qtd_pedidos': 0,
                'ultimo_pedido': p.data_criacao.strftime('%d/%m/%Y')
            }
        clientes[p.nome_cliente]['total'] += p.valor_total
        clientes[p.nome_cliente]['qtd_pedidos'] += 1
    
    return jsonify(list(clientes.values()))

@financas_bp.route('/api/marcar-pago/<int:pedido_id>', methods=['POST'])
@login_required
def marcar_pago(pedido_id):
    """Marca um pedido como pago"""
    pedido = Pedido.query.get_or_404(pedido_id)
    
    try:
        pedido.status_pagamento = 'pago'
        db.session.commit()
        return jsonify({'success': True, 'message': 'Pedido marcado como pago!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    

@financas_bp.route('/api/pedidos-por-mes')
@login_required
def api_pedidos_por_mes():
    """Pedidos de um mês específico"""
    mes = request.args.get('mes', type=int)
    ano = request.args.get('ano', type=int)
    
    if not mes or not ano:
        hoje = agora_brasil()
        mes = hoje.month
        ano = hoje.year
    
    pedidos = Pedido.query.filter(
        extract('month', Pedido.data_criacao) == mes,
        extract('year', Pedido.data_criacao) == ano
    ).order_by(Pedido.data_criacao).all()
    
    total = sum(p.valor_total for p in pedidos)
    pagos = sum(p.valor_total for p in pedidos if p.status_pagamento == 'pago')
    pendentes = sum(p.valor_total for p in pedidos if p.status_pagamento == 'pendente')
    
    return jsonify({
        'total': float(total),
        'pagos': float(pagos),
        'pendentes': float(pendentes),
        'pedidos': [{
            'id': p.id,
            'cliente': p.nome_cliente,
            'produto': p.produto,
            'volumes': p.volumes,
            'valor': float(p.valor_total),
            'data': p.data_criacao.strftime('%d/%m/%Y'),
            'forma_pagamento': p.forma_pagamento,
            'status_pagamento': p.status_pagamento
        } for p in pedidos]
    })