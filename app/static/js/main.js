// main.js - Funções principais otimizadas

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Sistema pronto!');
    
    // Auto-fechar alertas após 5 segundos
    setTimeout(function() {
        document.querySelectorAll('.alert').forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Prevenir zoom em inputs no iOS
    document.querySelectorAll('input, select, textarea').forEach(function(element) {
        element.style.fontSize = '16px';
    });
});

// Função para confirmar ações no mobile
window.confirmarAcao = function(mensagem) {
    return confirm(mensagem || 'Tem certeza?');
};

// Função para formatar telefone
window.formatarTelefone = function(telefone) {
    return telefone.replace(/\D/g, '')
        .replace(/^(\d{2})(\d)/g, '($1) $2')
        .replace(/(\d)(\d{4})$/, '$1-$2');
};