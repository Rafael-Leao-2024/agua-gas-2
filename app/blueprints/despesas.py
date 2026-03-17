from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.models import Despesa, db
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from app.models import agora_brasil

despesas_bp = Blueprint("despesas", __name__, url_prefix="/despesas")

@despesas_bp.route('/')
@login_required
def dashboard():
    """Dashboard de despesas"""
    return render_template('despesas/dashboard.html')


@despesas_bp.route('/nova', methods=['GET', 'POST'])
@login_required
def nova_despesa():
    """Registrar nova despesa"""
    if request.method == 'POST':
        try:
            despesa = Despesa(
                descricao=request.form['descricao'],
                valor=float(request.form['valor']),
                categoria=request.form['categoria'],
                forma_pagamento=request.form['forma_pagamento'],
                observacao=request.form.get('observacao', ''),
                usuario_id=current_user.id
            )
            
            # Se veio uma data específica
            if request.form.get('data'):
                data = datetime.strptime(request.form['data'], '%Y-%m-%d')
                despesa.data = data
            
            db.session.add(despesa)
            db.session.commit()
            
            flash('Despesa registrada com sucesso!', 'success')
            return redirect(url_for('despesas.dashboard'))
            
        except Exception as e:
            flash(f'Erro ao registrar despesa: {str(e)}', 'danger')
    
    return render_template('despesas/nova.html', datetime=datetime)


@despesas_bp.route('/lista')
@login_required
def lista():
    """Lista de despesas"""
    return render_template('despesas/lista.html')

@despesas_bp.route('/editar/<int:despesa_id>', methods=['GET', 'POST'])
@login_required
def editar(despesa_id):
    """Editar despesa"""
    despesa = Despesa.query.get_or_404(despesa_id)
    
    # Verifica se a despesa é do usuário atual
    if despesa.usuario_id != current_user.id:
        flash('Você não tem permissão para editar esta despesa.', 'danger')
        return redirect(url_for('despesas.lista'))
    
    if request.method == 'POST':
        try:
            despesa.descricao = request.form['descricao']
            despesa.valor = float(request.form['valor'])
            despesa.categoria = request.form['categoria']
            despesa.forma_pagamento = request.form['forma_pagamento']
            despesa.observacao = request.form.get('observacao', '')
            
            if request.form.get('data'):
                despesa.data = datetime.strptime(request.form['data'], '%Y-%m-%d')
            
            db.session.commit()
            
            flash('Despesa atualizada com sucesso!', 'success')
            return redirect(url_for('despesas.lista'))
            
        except Exception as e:
            flash(f'Erro ao atualizar despesa: {str(e)}', 'danger')
    
    return render_template('despesas/editar.html', despesa=despesa)

@despesas_bp.route('/excluir/<int:despesa_id>', methods=['POST'])
@login_required
def excluir(despesa_id):
    """Excluir despesa"""
    despesa = Despesa.query.get_or_404(despesa_id)
    
    if despesa.usuario_id != current_user.id:
        return jsonify({'success': False, 'message': 'Permissão negada'}), 403
    
    try:
        db.session.delete(despesa)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    

@despesas_bp.route('/api/resumo')
@login_required
def api_resumo():
    """Resumo de despesas"""
    hoje = agora_brasil().date()
    print(hoje)
    inicio_mes = datetime(hoje.year, hoje.month, 1)
    
    # Despesas hoje
    total_hoje = db.session.query(func.sum(Despesa.valor))\
        .filter(
            Despesa.usuario_id == current_user.id,
            func.date(Despesa.data) == hoje
        ).scalar() or 0
    
    qtd_hoje = Despesa.query.filter(
        Despesa.usuario_id == current_user.id,
        func.date(Despesa.data) == hoje
    ).count()
    
    # Despesas do mês
    total_mes = db.session.query(func.sum(Despesa.valor))\
        .filter(
            Despesa.usuario_id == current_user.id,
            Despesa.data >= inicio_mes
        ).scalar() or 0
    
    qtd_mes = Despesa.query.filter(
        Despesa.usuario_id == current_user.id,
        Despesa.data >= inicio_mes
    ).count()
    

    # Por categoria (últimos 30 dias)
    trinta_dias_atras = agora_brasil() - timedelta(days=30)
    
    categorias = db.session.query(
        Despesa.categoria,
        func.sum(Despesa.valor).label('total'),
        func.count(Despesa.id).label('quantidade')
    ).filter(
        Despesa.usuario_id == current_user.id,
        Despesa.data >= trinta_dias_atras
    ).group_by(Despesa.categoria).all()
    
    return jsonify({
        'total_hoje': float(total_hoje),
        'qtd_hoje': qtd_hoje,
        'total_mes': float(total_mes),
        'qtd_mes': qtd_mes,
        'categorias': [{
            'categoria': c.categoria,
            'total': float(c.total),
            'quantidade': c.quantidade
        } for c in categorias]
    })


@despesas_bp.route('/api/lista')
@login_required
def api_lista():
    """Lista de despesas com filtros"""
    filtro = request.args.get('filtro', 'mes')  # hoje, mes, todos
    hoje = agora_brasil().date()
    inicio_mes = datetime(hoje.year, hoje.month, 1)
    
    query = Despesa.query.filter(Despesa.usuario_id == current_user.id)
    
    if filtro == 'hoje':
        query = query.filter(func.date(Despesa.data) == hoje)
    elif filtro == 'mes':
        query = query.filter(Despesa.data >= inicio_mes)
    
    despesas = query.order_by(Despesa.data.desc()).all()
    
    return jsonify([{
        'id': d.id,
        'descricao': d.descricao,
        'valor': float(d.valor),
        'categoria': d.categoria,
        'data': d.data.strftime('%d/%m/%Y'),
        'data_raw': d.data.strftime('%Y-%m-%d'),
        'forma_pagamento': d.forma_pagamento,
        'observacao': d.observacao
    } for d in despesas])