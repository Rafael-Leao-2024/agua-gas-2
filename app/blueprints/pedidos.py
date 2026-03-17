# app/blueprints/pedidos.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import Pedido, Entrega, db, agora_brasil
from datetime import datetime
import random
import string

pedidos_bp = Blueprint('pedidos', __name__)

def gerar_codigo_acompanhamento():
    """Gera código único para acompanhamento do pedido"""
    while True:
        codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if not Pedido.query.filter_by(codigo_acompanhamento=codigo).first():
            return codigo

@pedidos_bp.route('/')
@login_required
def lista_pedidos():
    """Lista todos os pedidos"""
    status = request.args.get('status', 'processo')
    
    if status == 'todos':
        pedidos = Pedido.query.order_by(Pedido.data_criacao.desc()).all()[:1500]

    elif status == "entregue":
        hoje = agora_brasil().date()
        pedidos = Pedido.query.filter(
            Pedido.status == 'entregue',
            db.func.date(Pedido.data_entrega) == hoje
        ).order_by(Pedido.data_entrega.desc()).all()

    else:
        pedidos = Pedido.query.filter_by(status=status).order_by(Pedido.data_criacao.desc()).all()
    
    return render_template('pedidos/lista.html', pedidos=pedidos, status_atual=status)

@pedidos_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo_pedido():
    """Cria novo pedido"""
    if request.method == 'POST':
        try:
            pedido = Pedido(
                codigo_acompanhamento=gerar_codigo_acompanhamento(),
                volumes=int(request.form['volumes']),
                produto=request.form['produto'],
                nome_cliente=request.form['nome_cliente'].title(),
                endereco_cliente=request.form['endereco_cliente'].title(),
                valor_total=float(request.form['valor_total']),
                forma_pagamento=request.form['forma_pagamento'],
                status_pagamento=request.form['status_pagamento'],
                status='processo',
                data_processo=agora_brasil(),
                usuario_id=current_user.id
            )
            
            db.session.add(pedido)
            db.session.commit()
            
            flash('Pedido criado com sucesso!', 'success')
            return redirect(url_for('pedidos.lista_pedidos'))
        except Exception as e:
            flash(f'Erro ao criar pedido: {str(e)}', 'danger')
    
    return render_template('pedidos/novo.html')

@pedidos_bp.route('/editar/<int:pedido_id>', methods=['GET', 'POST'])
@login_required
def editar_pedido(pedido_id):
    """Edita pedido existente"""
    pedido = Pedido.query.get_or_404(pedido_id)
    
    if request.method == 'POST':
        try:
            pedido.volumes = int(request.form['volumes'])
            pedido.produto = request.form['produto']
            pedido.nome_cliente = request.form['nome_cliente']
            pedido.endereco_cliente = request.form['endereco_cliente']
            pedido.valor_total = float(request.form['valor_total'])
            pedido.forma_pagamento = request.form['forma_pagamento']
            pedido.status_pagamento = request.form['status_pagamento']
            
            db.session.commit()
            
            flash('Pedido atualizado com sucesso!', 'success')
            return redirect(url_for('pedidos.lista_pedidos'))
        except Exception as e:
            flash(f'Erro ao atualizar pedido: {str(e)}', 'danger')
    
    return render_template('pedidos/editar.html', pedido=pedido)

@pedidos_bp.route('/status/<int:pedido_id>', methods=['POST'])
@login_required
def atualizar_status(pedido_id):
    """Atualiza status do pedido"""
    pedido = Pedido.query.get_or_404(pedido_id)
    novo_status = request.json.get('status')
    
    try:
        # Atualiza data conforme status
        if novo_status == 'processo':
            pedido.data_processo = agora_brasil()
        elif novo_status == 'caminho':
            pedido.data_caminho = agora_brasil()
        elif novo_status == 'entregue':
            pedido.data_entrega = agora_brasil()
            # Registra entrega
            entrega = Entrega(
                pedido_id=pedido.id,
                usuario_id=current_user.id
            )
            db.session.add(entrega)
        
        pedido.status = novo_status
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Status atualizado!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@pedidos_bp.route('/excluir/<int:pedido_id>', methods=['POST'])
@login_required
def excluir_pedido(pedido_id):
    """Exclui pedido"""
    pedido = Pedido.query.get_or_404(pedido_id)
    print(f"Excluindo pedido ID {pedido_id} - Código: {pedido.codigo_acompanhamento} - Nome: {pedido.nome_cliente}")
    try:
        db.session.delete(pedido)
        db.session.commit()
        flash('Pedido excluído com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir pedido: {str(e)}', 'danger')
    
    return redirect(url_for('pedidos.lista_pedidos'))

@pedidos_bp.route('/acompanhar/<codigo>')
def acompanhar_pedido(codigo):
    """Página pública para cliente acompanhar pedido"""
    pedido = Pedido.query.filter_by(codigo_acompanhamento=codigo).first_or_404()
    return render_template('pedidos/visualizar_cliente.html', pedido=pedido)

@pedidos_bp.route('/whatsapp-link/<int:pedido_id>')
@login_required
def whatsapp_link(pedido_id):
    """Gera link do WhatsApp para compartilhar acompanhamento"""
    pedido = Pedido.query.get_or_404(pedido_id)
    
    # URL do pedido (ajuste conforme seu domínio)
    url_acompanhamento = url_for('pedidos.acompanhar_pedido', 
                                 codigo=pedido.codigo_acompanhamento, 
                                 _external=True)
    
    # Mensagem para WhatsApp
    mensagem = f"""Olá {pedido.nome_cliente}! 

Seu pedido de {pedido.volumes} {pedido.produto} foi registrado.
Valor: R$ {pedido.valor_total:.2f}
Status atual: {pedido.status}

Acompanhe seu pedido aqui: {url_acompanhamento}"""

    # Link do WhatsApp
    import urllib.parse
    link_whatsapp = f"https://wa.me/?text={urllib.parse.quote(mensagem)}"
    
    return jsonify({'link': link_whatsapp})


# Rotas API para o dashboard
@pedidos_bp.route('/api/resumo')
@login_required
def api_resumo():
    """API para resumo dos pedidos"""
    hoje = agora_brasil().date()
    
    # Contadores por status
    processos = Pedido.query.filter_by(status='processo').count()
    caminho = Pedido.query.filter_by(status='caminho').count()
    entregues = Pedido.query.filter(
    Pedido.status == 'entregue',
    db.func.date(Pedido.data_criacao) == hoje
).count()
    
    # Total de vendas hoje
    pedidos_hoje = Pedido.query.filter(
        db.func.date(Pedido.data_criacao) == hoje
    ).all()
    
    total_hoje = sum(pedido.valor_total for pedido in pedidos_hoje)
    
    return jsonify({
        'processos': processos,
        'caminho': caminho,
        'entregues': entregues,
        'total_hoje': total_hoje
    })

@pedidos_bp.route('/api/ultimos')
@login_required
def api_ultimos():
    """API para últimos 5 pedidos"""
    pedidos = Pedido.query.order_by(Pedido.data_criacao.desc()).limit(5).all()
    
    return jsonify([{
        'id': p.id,
        'codigo': p.codigo_acompanhamento,
        'cliente': p.nome_cliente,
        'produto': p.produto,
        'volumes': p.volumes,
        'status': p.status,
        'data': p.data_criacao.isoformat()
    } for p in pedidos])


@pedidos_bp.route('/detalhe/<int:pedido_id>')
@login_required
def detalhe_pedido(pedido_id):
    """Página de detalhes do pedido"""
    pedido = Pedido.query.get_or_404(pedido_id)
    return render_template('pedidos/detalhe.html', pedido=pedido)


@pedidos_bp.route('/editar-pagamento/<int:pedido_id>')
@login_required
def editar_pagamento(pedido_id):
    """Página para editar apenas pagamento"""
    pedido = Pedido.query.get_or_404(pedido_id)
    return render_template('pedidos/editar_pagamento.html', pedido=pedido)


@pedidos_bp.route('/atualizar-pagamento/<int:pedido_id>', methods=['POST'])
@login_required
def atualizar_pagamento(pedido_id):
    """Atualiza apenas forma e status de pagamento"""
    pedido = Pedido.query.get_or_404(pedido_id)
    
    try:
        # Atualiza forma de pagamento
        pedido.forma_pagamento = request.form['forma_pagamento']
        
        # Atualiza status do pagamento
        pedido.status_pagamento = 'pago' if request.form.get('status_pagamento') else 'pendente'
        
        db.session.commit()
        
        flash('Pagamento atualizado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao atualizar pagamento: {str(e)}', 'danger')
    
    return redirect(url_for('pedidos.detalhe_pedido', pedido_id=pedido.id))


@pedidos_bp.route('/toggle-pagamento/<int:pedido_id>', methods=['POST'])
@login_required
def atualizar_status_pagamento_rapido(pedido_id):
    """Atualiza status de pagamento rapidamente (toggle)"""
    pedido = Pedido.query.get_or_404(pedido_id)
    
    try:
        # Toggle status de pagamento
        pedido.status_pagamento = 'pago' if pedido.status_pagamento == 'pendente' else 'pendente'
        
        db.session.commit()
        
        return jsonify({'success': True, 'novo_status': pedido.status_pagamento})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    


@pedidos_bp.route("/buscar-enderecos")
@login_required
def buscar_enderecos():
    termo = request.args.get('q', '')

    enderecos = (
        Pedido.query
        .filter(Pedido.endereco_cliente.ilike(f"%{termo}%"))
        .distinct()
        .limit(4)
        .all()
    )

    
    lista_set = set([pedido.endereco_cliente for pedido in enderecos])
    print(f"Endereços encontrados para '{termo}': {lista_set}")
    lista = list(lista_set)[:5]  # Limita a 5 endereços únicos

    return jsonify(lista)


@pedidos_bp.route('/buscar-clientes')
@login_required
def buscar_clientes():
    termo = request.args.get('q', '')

    clientes = (
        Pedido.query
        .filter(Pedido.nome_cliente.ilike(f"%{termo}%"))
        .distinct()
        .limit(2)
        .all()
    )

    lista = [pedido.nome_cliente for pedido in clientes]
    set_lista = set(lista)  # Remove duplicatas
    
    return jsonify(list(set_lista))



@pedidos_bp.route('/marcar-recebido/<int:id_pedido>', methods=['POST'])
def marcar_recebido(id_pedido):
    """Marca pedido como recebido (cliente)"""
    print(f"Recebendo confirmação para código: {id_pedido}")
    try:
        pedido = Pedido.query.filter(Pedido.id == id_pedido).first()
        print(f"Pedido encontrado: {pedido}")
        if not pedido:
            return jsonify({'success': False, 'message': 'Código não encontrado!'}), 404
        
        if pedido.status == 'entregue':
            return jsonify({'success': False, 'message': 'Este pedido já foi entregue!'}), 400
        
        # Atualiza status
        from datetime import datetime
        from app.models import agora_brasil

        pedido.status = 'entregue'
        pedido.data_entrega = agora_brasil()
        db.session.commit()
        db.session.refresh(pedido)  # Atualiza o objeto pedido com os dados do banco
        # Registra entrega
        from app.models import Entrega
        entrega = Entrega(
            pedido_id=pedido.id,
            usuario_id=pedido.usuario_id,
            observacao='Confirmado pelo cliente via botão'
        )
        db.session.add(entrega)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Recebimento confirmado!'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': 'Erro ao confirmar recebimento'}), 500



