// pedidos.js - Funções relacionadas a pedidos

/**
 * Carrega resumo dos pedidos para o dashboard
 */
function carregarResumo() {
    fetch('/pedidos/api/resumo')
        .then(response => response.json())
        .then(data => {
            document.getElementById('contador-processo').textContent = data.processos;
            document.getElementById('contador-caminho').textContent = data.caminho;
            document.getElementById('contador-entregue').textContent = data.entregues;
            document.getElementById('total-hoje').textContent = formatarMoeda(data.total_hoje);
        })
        .catch(error => {
            console.error('Erro ao carregar resumo:', error);
        });
}

/**
 * Carrega últimos pedidos para o dashboard
 */
function carregarUltimosPedidos() {
    fetch('/pedidos/api/ultimos')
        .then(response => response.json())
        .then(pedidos => {
            const tbody = document.getElementById('tabela-ultimos-pedidos');
            tbody.innerHTML = '';
            
            pedidos.forEach(pedido => {
                const tr = document.createElement('tr');
                
                // Define classe de status
                let statusClass = '';
                let statusIcon = '';
                if (pedido.status === 'processo') {
                    statusClass = 'bg-warning';
                    statusIcon = 'bi-clock';
                } else if (pedido.status === 'caminho') {
                    statusClass = 'bg-info';
                    statusIcon = 'bi-truck';
                } else {
                    statusClass = 'bg-success';
                    statusIcon = 'bi-check-circle';
                }
                
                tr.innerHTML = `
                    <td><span class="badge bg-secondary">${pedido.codigo}</span></td>
                    <td>${pedido.cliente}</td>
                    <td>${pedido.produto}</td>
                    <td>${pedido.volumes}</td>
                    <td><span class="badge ${statusClass}"><i class="bi ${statusIcon}"></i> ${pedido.status}</span></td>
                    <td>${formatarData(pedido.data)}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-info" onclick="compartilharWhatsApp(${pedido.id})">
                            <i class="bi bi-whatsapp"></i>
                        </button>
                    </td>
                `;
                
                tbody.appendChild(tr);
            });
        })
        .catch(error => {
            console.error('Erro ao carregar últimos pedidos:', error);
        });
}

/**
 * Atualiza status do pedido
 * @param {number} pedidoId - ID do pedido
 * @param {string} novoStatus - Novo status
 */
function atualizarStatus(pedidoId, novoStatus) {
    if (!confirmarAcao(`Deseja alterar o status para "${novoStatus}"?`)) {
        // Reverte select
        event.target.value = event.target.getAttribute('data-status-anterior');
        return;
    }
    
    fetch(`/pedidos/status/${pedidoId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: novoStatus })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            mostrarNotificacao('Status atualizado com sucesso!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            mostrarNotificacao('Erro ao atualizar status', 'danger');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        mostrarNotificacao('Erro ao atualizar status', 'danger');
    });
}

/**
 * Compartilha pedido no WhatsApp
 * @param {number} pedidoId - ID do pedido
 */
function compartilharWhatsApp(pedidoId) {
    fetch(`/pedidos/whatsapp-link/${pedidoId}`)
        .then(response => response.json())
        .then(data => {
            // Abre link do WhatsApp em nova janela
            window.location.href = data.link; // 👈 MUDAR AQUI;
        })
        .catch(error => {
            console.error('Erro ao gerar link:', error);
            mostrarNotificacao('Erro ao gerar link do WhatsApp', 'danger');
        });
}

/**
 * Exclui pedido
 * @param {number} pedidoId - ID do pedido
 */
function excluirPedido(pedidoId) {
    if (!confirmarAcao('Deseja realmente excluir este pedido? Esta ação não pode ser desfeita.')) {
        return;
    }
    
    fetch(`/pedidos/excluir/${pedidoId}`, {
        method: 'POST'
    })
    .then(response => {
        if (response.redirected) {
            mostrarNotificacao('Pedido excluído com sucesso!', 'success');
            setTimeout(() => window.location.href = response.url, 1000);
        } else {
            mostrarNotificacao('Erro ao excluir pedido', 'danger');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        mostrarNotificacao('Erro ao excluir pedido', 'danger');
    });
}