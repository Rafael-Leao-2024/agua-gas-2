// utils.js - Funções utilitárias

/**
 * Formata valor para moeda brasileira
 * @param {number} valor - Valor a ser formatado
 * @returns {string} Valor formatado
 */
function formatarMoeda(valor) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(valor);
}

/**
 * Formata data para padrão brasileiro
 * @param {string} data - Data em formato ISO
 * @returns {string} Data formatada
 */
function formatarData(data) {
    if (!data) return '';
    return new Date(data).toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Exibe mensagem de confirmação
 * @param {string} mensagem - Mensagem a ser exibida
 * @returns {boolean} Confirmação do usuário
 */
function confirmarAcao(mensagem = 'Tem certeza que deseja realizar esta ação?') {
    return confirm(mensagem);
}

/**
 * Exibe notificação toast
 * @param {string} mensagem - Mensagem a ser exibida
 * @param {string} tipo - Tipo da mensagem (success, error, warning, info)
 */
function mostrarNotificacao(mensagem, tipo = 'info') {
    // Cria elemento toast
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${tipo} border-0 position-fixed bottom-0 end-0 m-3`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    toast.style.zIndex = '9999';
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${mensagem}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Inicializa e mostra toast
    const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
    bsToast.show();
    
    // Remove elemento após fechar
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}