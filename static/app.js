// app.js - Comportamentos compartilhados do LojaOS
// Mantem a interface reativa sem depender de frameworks pesados.

document.addEventListener('DOMContentLoaded', () => {
  ativarListasDinamicas();
  ativarAutoDismissFlash();
  ativarSpinnerBotoes();
  ativarFocoAcessivel();
});

// Adiciona/remove linhas de item em telas com listas dinamicas
// (venda, pedido). Usa data-attributes para nao duplicar codigo.
function ativarListasDinamicas() {
  document.querySelectorAll('[data-lista-itens]').forEach((container) => {
    const addBtn = document.querySelector(`[data-add-item="${container.dataset.listaItens}"]`);
    if (addBtn) {
      addBtn.addEventListener('click', () => {
        const template = container.firstElementChild;
        const clone = template.cloneNode(true);
        const qtdInput = clone.querySelector('input[type="number"]');
        if (qtdInput) qtdInput.value = 1;
        clone.style.opacity = '0';
        container.appendChild(clone);
        requestAnimationFrame(() => {
          clone.style.transition = 'opacity 0.25s ease';
          clone.style.opacity = '1';
        });
      });
    }
    container.addEventListener('click', (e) => {
      if (e.target.classList.contains('btn-remove-item') && container.children.length > 1) {
        const item = e.target.closest('.venda-item');
        item.style.transition = 'opacity 0.2s ease, transform 0.2s ease';
        item.style.opacity = '0';
        item.style.transform = 'translateX(-6px)';
        setTimeout(() => item.remove(), 180);
      }
    });
  });
}

// Some automaticamente com os alertas de sucesso/erro apos alguns segundos
function ativarAutoDismissFlash() {
  document.querySelectorAll('.flash').forEach((el, i) => {
    setTimeout(() => {
      el.style.transition = 'opacity 0.4s ease, transform 0.4s ease, max-height 0.4s ease, margin 0.4s ease, padding 0.4s ease';
      el.style.opacity = '0';
      el.style.transform = 'translateY(-6px)';
      el.style.maxHeight = '0';
      el.style.margin = '0';
      el.style.padding = '0 16px';
      el.style.overflow = 'hidden';
      setTimeout(() => el.remove(), 420);
    }, 5000 + i * 300);
  });
}

// Mostra um spinner discreto no botao ao enviar um formulario,
// evitando duplo clique e dando feedback visual imediato.
function ativarSpinnerBotoes() {
  document.querySelectorAll('form').forEach((form) => {
    form.addEventListener('submit', () => {
      const btn = form.querySelector('button[type="submit"]');
      if (btn && !btn.disabled) {
        btn.dataset.textoOriginal = btn.innerHTML;
        btn.innerHTML = '<span class="spinner"></span> Enviando...';
        btn.disabled = true;
        btn.style.opacity = '0.75';
        btn.style.cursor = 'wait';
      }
    });
  });
}

// Melhora o indicador de foco via teclado (acessibilidade), sem
// exibir o anel de foco quando a interacao e via mouse.
function ativarFocoAcessivel() {
  document.body.addEventListener('mousedown', () => document.body.classList.add('usando-mouse'));
  document.body.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') document.body.classList.remove('usando-mouse');
  });
}
