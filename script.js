/* ===== MERCADO FAMÍLIA GAMA – script.js ===== */

/* ---------- NAVEGAÇÃO ENTRE PÁGINAS ---------- */
function toggleMenu() {
  document.getElementById('navLinks').classList.toggle('open');
}

/* ---------- FILTRO DE PRODUTOS ---------- */
function filterProd(cat, btn) {
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.produto-card').forEach(card => {
    card.style.display = (cat === 'todos' || card.dataset.cat === cat) ? '' : 'none';
  });
}

/* ---------- FORMULÁRIO DE CONTATO ---------- */
function enviarFormulario() {
  const nome     = document.getElementById('nome').value.trim();
  const email    = document.getElementById('email').value.trim();
  const assunto  = document.getElementById('assunto').value;
  const mensagem = document.getElementById('mensagem').value.trim();

  if (!nome || !email || !assunto || !mensagem) {
    alert('Por favor, preencha todos os campos obrigatórios (*).');
    return;
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    alert('Por favor, informe um e-mail válido.');
    return;
  }

  document.getElementById('sucessoMsg').style.display = 'block';
  ['nome','email','telefone','assunto','mensagem'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = '';
  });

  setTimeout(() => {
    const msg = document.getElementById('sucessoMsg');
    if (msg) msg.style.display = 'none';
  }, 5000);
}

/* ---------- FORMULÁRIO TRABALHE CONOSCO (multi-step) ---------- */

// Mapeamento de área → subareas
const subareasPorArea = {
  escritorio: {
    label: 'Escritório',
    opcoes: [
      { value: 'ti',         label: '💻 Desenvolvedor de TI' },
      { value: 'marketing',  label: '📣 Marketing & Redes Sociais' },
      { value: 'financeiro', label: '💰 Financeiro / Contabilidade' },
      { value: 'rh',         label: '👥 Recursos Humanos' },
      { value: 'compras',    label: '🛒 Compras & Suprimentos' },
      { value: 'adm',        label: '📋 Assistente Administrativo' },
    ]
  },
  unidade: {
    label: 'Trabalhar na Unidade',
    opcoes: [
      { value: 'caixa',      label: '🖥️ Operador(a) de Caixa' },
      { value: 'repositor',  label: '📦 Repositor(a) de Produtos' },
      { value: 'faxineiro',  label: '🧹 Auxiliar de Limpeza' },
      { value: 'acougue',    label: '🥩 Auxiliar de Açougue' },
      { value: 'hortifruti', label: '🥦 Auxiliar de Hortifruti' },
      { value: 'padaria',    label: '🍞 Auxiliar de Padaria' },
      { value: 'seguranca',  label: '🛡️ Segurança Patrimonial' },
      { value: 'estoque',    label: '🏭 Auxiliar de Estoque' },
    ]
  },
  logistica: {
    label: 'Logística & Entregas',
    opcoes: [
      { value: 'motorista',  label: '🚚 Motorista Entregador' },
      { value: 'ajudante',   label: '📬 Ajudante de Entrega' },
      { value: 'separacao',  label: '📋 Separador de Pedidos' },
    ]
  },
  gerencia: {
    label: 'Gerência & Supervisão',
    opcoes: [
      { value: 'gerente',    label: '🏆 Gerente de Loja' },
      { value: 'supervisor', label: '📊 Supervisor de Setor' },
      { value: 'lider',      label: '⭐ Líder de Equipe' },
    ]
  }
};

let stepAtual = 1;
const totalSteps = 3;

function atualizarSteps() {
  // Atualiza os indicadores visuais
  document.querySelectorAll('.step').forEach((el, i) => {
    const num = i + 1;
    el.classList.remove('active', 'done');
    if (num < stepAtual) el.classList.add('done');
    if (num === stepAtual) el.classList.add('active');
  });

  document.querySelectorAll('.step-line').forEach((el, i) => {
    el.classList.toggle('done', i + 1 < stepAtual);
  });

  // Mostra apenas o step atual
  document.querySelectorAll('.form-step').forEach((el, i) => {
    el.classList.toggle('active', i + 1 === stepAtual);
  });

  // Botão voltar
  const btnVoltar = document.getElementById('btnVoltar');
  if (btnVoltar) btnVoltar.style.display = stepAtual > 1 ? 'inline-block' : 'none';
}

function avancarStep() {
  if (!validarStep(stepAtual)) return;
  if (stepAtual < totalSteps) {
    stepAtual++;
    atualizarSteps();
    window.scrollTo({ top: document.querySelector('.candidatura-card').offsetTop - 100, behavior: 'smooth' });
  }
}

function voltarStep() {
  if (stepAtual > 1) {
    stepAtual--;
    atualizarSteps();
  }
}

function validarStep(step) {
  if (step === 1) {
    const nome  = document.getElementById('tc-nome')?.value.trim();
    const nasc  = document.getElementById('tc-nascimento')?.value;
    const email = document.getElementById('tc-email')?.value.trim();
    const tel   = document.getElementById('tc-telefone')?.value.trim();

    if (!nome || !nasc || !email || !tel) {
      mostrarErro('Por favor, preencha todos os campos obrigatórios do Passo 1.');
      return false;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      mostrarErro('Por favor, informe um e-mail válido.');
      return false;
    }
    // Validação de idade mínima (16 anos)
    const nascDate = new Date(nasc);
    const hoje = new Date();
    const idade = hoje.getFullYear() - nascDate.getFullYear();
    if (idade < 16) {
      mostrarErro('A idade mínima para candidatura é de 16 anos.');
      return false;
    }
    esconderErro();
    return true;
  }

  if (step === 2) {
    const area = document.getElementById('tc-area')?.value;
    if (!area) {
      mostrarErro('Por favor, selecione uma área de interesse.');
      return false;
    }
    const checks = document.querySelectorAll('.subarea-check input[type="checkbox"]:checked');
    if (checks.length === 0) {
      mostrarErro('Por favor, selecione pelo menos uma função de interesse.');
      return false;
    }
    esconderErro();
    return true;
  }

  return true;
}

function mostrarErro(msg) {
  const el = document.getElementById('erroMsg');
  if (el) { el.textContent = '⚠️ ' + msg; el.style.display = 'block'; }
  else alert(msg);
}

function esconderErro() {
  const el = document.getElementById('erroMsg');
  if (el) el.style.display = 'none';
}

function onAreaChange() {
  const area = document.getElementById('tc-area')?.value;
  const wrapper = document.getElementById('subarea-wrapper');
  const container = document.getElementById('subareas-container');
  if (!wrapper || !container) return;

  if (!area || !subareasPorArea[area]) {
    wrapper.classList.remove('visible');
    container.innerHTML = '';
    return;
  }

  const dados = subareasPorArea[area];
  container.innerHTML = dados.opcoes.map(op => `
    <label class="subarea-check">
      <input type="checkbox" name="funcao" value="${op.value}">
      ${op.label}
    </label>
  `).join('');

  wrapper.classList.add('visible');
}

function enviarCandidatura() {
  if (!validarStep(3)) return;

  const nome  = document.getElementById('tc-nome')?.value.trim();
  const area  = document.getElementById('tc-area')?.value;
  const checks = [...document.querySelectorAll('.subarea-check input[type="checkbox"]:checked')]
    .map(c => c.parentElement.textContent.trim()).join(', ');

  // Esconde o formulário e mostra confirmação
  document.getElementById('formCandidatura').style.display = 'none';
  const sucesso = document.getElementById('sucessoCandidatura');
  if (sucesso) {
    sucesso.style.display = 'block';
    const nomeEl = document.getElementById('sucesso-nome');
    if (nomeEl) nomeEl.textContent = nome;
    const funcEl = document.getElementById('sucesso-funcoes');
    if (funcEl) funcEl.textContent = checks;
  }
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Inicialização ao carregar a página
document.addEventListener('DOMContentLoaded', () => {
  // Inicializa steps do form trabalhe conosco (se existir)
  if (document.querySelector('.progress-steps')) {
    atualizarSteps();
  }
});