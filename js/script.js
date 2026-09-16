/* ===== MERCADO FAMÍLIA GAMA – script.js ===== */

/* ══════════════════════════════════════════════
   CARRINHO (localStorage)
══════════════════════════════════════════════ */
const CART_KEY = 'gama_carrinho';
const FRETE_KEY = 'gama_frete';

function lerCarrinho() {
  try { return JSON.parse(localStorage.getItem(CART_KEY)) || []; }
  catch { return []; }
}

function salvarCarrinho(itens) {
  localStorage.setItem(CART_KEY, JSON.stringify(itens));
}

function totalItens(itens) {
  return itens.reduce((s, i) => s + i.qty, 0);
}

/* Badge no header – atualiza em todas as páginas */
function atualizarBadge() {
  const count = totalItens(lerCarrinho());
  document.querySelectorAll('#cartBadge').forEach(b => {
    b.textContent = count;
    b.classList.remove('bump');
    void b.offsetWidth;
    b.classList.add('bump');
    setTimeout(() => b.classList.remove('bump'), 350);
  });
}

/* Adicionar produto ao carrinho */
function addCarrinho(btn) {
  const card = btn.closest('.produto-card');
  if (!card) return;

  const id = card.dataset.id;
  const nome = card.dataset.nome;
  const preco = parseFloat(card.dataset.preco);
  const unidade = card.dataset.unidade || '/un';
  const marca = card.querySelector('.produto-marca')?.textContent || '';
  const emoji = card.querySelector('.produto-thumb')?.textContent.trim() || '🛒';

  let itens = lerCarrinho();
  const idx = itens.findIndex(i => i.id === id);
  if (idx >= 0) itens[idx].qty += 1;
  else itens.push({ id, nome, preco, unidade, marca, emoji, qty: 1 });

  salvarCarrinho(itens);
  atualizarBadge();
  mostrarToast(`✅ "${nome}" adicionado ao carrinho!`);

  btn.textContent = '✔ Adicionado!';
  btn.classList.add('adicionado');
  setTimeout(() => {
    btn.textContent = '🛒 Adicionar ao Carrinho';
    btn.classList.remove('adicionado');
  }, 1500);
}

function mostrarToast(msg) {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(window._toastTimer);
  window._toastTimer = setTimeout(() => t.classList.remove('show'), 2800);
}

/* ══════════════════════════════════════════════
   PÁGINA DO CARRINHO – renderização
══════════════════════════════════════════════ */
function fmt(v) {
  return 'R$ ' + v.toFixed(2).replace('.', ',');
}

function atualizarResumo() {
  const itens = lerCarrinho();
  const subtotal = itens.reduce((s, i) => s + i.preco * i.qty, 0);

  const elSub = document.getElementById('resumoSubtotal');
  const elFrete = document.getElementById('resumoFrete');
  const elTotal = document.getElementById('resumoTotal');
  const btnFin = document.getElementById('btnFinalizar');

  if (elSub) elSub.textContent = fmt(subtotal);

  // Recupera frete já calculado (se houver)
  const freteInfo = lerFreteCalc();
  let freteTxt = 'Calcule acima';
  let freteVal = 0;
  let freteColor = '#888';

  if (freteInfo !== null) {
    if (freteInfo === 0) {
      freteTxt = 'Grátis 🎉';
      freteColor = 'var(--verde)';
    } else if (freteInfo === -1) {
      freteTxt = 'Sob consulta';
      freteColor = 'var(--vermelho)';
    } else {
      freteVal = freteInfo;
      freteTxt = fmt(freteInfo);
      freteColor = '#e65100';
    }
  }

  if (elFrete) { elFrete.textContent = freteTxt; elFrete.style.color = freteColor; }

  const total = subtotal + (freteVal || 0);
  if (elTotal) elTotal.textContent = fmt(total);

  // Libera finalizar só se houver itens E frete calculado (exceto "sob consulta")
  if (btnFin) {
    const podeFinalizarFrete = freteInfo !== null && freteInfo !== -1;
    btnFin.disabled = itens.length === 0 || !podeFinalizarFrete;
  }
}

function renderCarrinho() {
  const lista = document.getElementById('listaItens');
  const acoes = document.getElementById('carrinhoAcoes');
  if (!lista) return;

  const itens = lerCarrinho();

  if (itens.length === 0) {
    lista.innerHTML = `
      <div class="carrinho-vazio">
        <div class="vazio-icon">🛒</div>
        <h3>CARRINHO VAZIO</h3>
        <p>Você ainda não adicionou nenhum produto.<br>Explore nossa loja e encontre o que precisa!</p>
        <a class="btn-continuar" href="produtos.html" style="padding:13px 28px;border-radius:10px;font-size:0.97rem;">
          🛍️ Ver Produtos
        </a>
      </div>`;
    if (acoes) acoes.style.display = 'none';
    atualizarResumo();
    return;
  }

  lista.innerHTML = itens.map(item => `
    <div class="item-card" data-id="${item.id}">
      <div class="item-thumb">${item.emoji}</div>
      <div class="item-info">
        <div class="item-marca">${item.marca}</div>
        <div class="item-nome">${item.nome}</div>
        <div class="item-unitario">${fmt(item.preco)}${item.unidade} cada</div>
      </div>
      <div class="item-qty">
        <button class="qty-btn" onclick="alterarQty('${item.id}', -1)" title="Diminuir">−</button>
        <span class="qty-num">${item.qty}</span>
        <button class="qty-btn" onclick="alterarQty('${item.id}', +1)" title="Aumentar">+</button>
      </div>
      <div class="item-subtotal">${fmt(item.preco * item.qty)}</div>
      <button class="btn-remover" onclick="removerItem('${item.id}')" title="Remover">✕</button>
    </div>
  `).join('');

  if (acoes) acoes.style.display = 'flex';
  atualizarResumo();
}

function alterarQty(id, delta) {
  let itens = lerCarrinho();
  const idx = itens.findIndex(i => i.id === id);
  if (idx < 0) return;
  itens[idx].qty += delta;
  if (itens[idx].qty <= 0) itens.splice(idx, 1);
  salvarCarrinho(itens);
  atualizarBadge();
  renderCarrinho();
}

function removerItem(id) {
  salvarCarrinho(lerCarrinho().filter(i => i.id !== id));
  atualizarBadge();
  renderCarrinho();
}

function limparCarrinho() {
  if (!confirm('Tem certeza que deseja esvaziar o carrinho?')) return;
  salvarCarrinho([]);
  limparFreteCalc();
  atualizarBadge();
  renderCarrinho();
}

function finalizarPedido() {
  const modal = document.getElementById('modalSucesso');
  if (modal) {
    modal.classList.add('show');
    salvarCarrinho([]);
    limparFreteCalc();
    atualizarBadge();
  }
}

/* ══════════════════════════════════════════════
   CALCULADORA DE FRETE
   Loja: Taboão da Serra/SP  (-23.6080, -46.7550)
   Regra: gratuito até 3 km; R$2,50 por cada 3 km acima
══════════════════════════════════════════════ */
const LOJA_LAT = -23.6080;
const LOJA_LNG = -46.7550;
const FRETE_FAIXA_KM = 3;      // km por faixa
const FRETE_VALOR_FAIXA = 2.50;   // R$ por faixa adicional
const FRETE_MAX_KM = 15;     // acima disso: sob consulta

/* Haversine – distância em km entre dois pontos */
function haversine(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

/* Calcula o valor do frete dado a distância em km */
function calcularValorFrete(km) {
  if (km <= FRETE_FAIXA_KM) return 0;                     // Grátis até 3 km
  if (km > FRETE_MAX_KM) return -1;                     // Sob consulta
  const faixasExtras = Math.ceil((km - FRETE_FAIXA_KM) / FRETE_FAIXA_KM);
  return faixasExtras * FRETE_VALOR_FAIXA;
}


/* Salva o resultado do frete calculado */
function salvarFreteCalc(valor) {
  localStorage.setItem(FRETE_KEY, JSON.stringify(valor));
}
function lerFreteCalc() {
  const v = localStorage.getItem(FRETE_KEY);
  if (v === null) return null;
  try { return JSON.parse(v); } catch { return null; }
}
function limparFreteCalc() {
  localStorage.removeItem(FRETE_KEY);
}


/* Função principal chamada pelo botão */
async function calcularFrete() {
  const input = document.getElementById('freteEndereco');
  const resultado = document.getElementById('freteResultado');
  const btn = document.getElementById('btnCalcular');

  const endereco = input?.value.trim();
  if (!endereco) {
    mostrarResultadoFrete('erro', '⚠️ Por favor, digite seu endereço antes de calcular.');
    return;
  }

  // Loading
  btn.disabled = true;
  btn.textContent = '⏳ Buscando...';
  mostrarResultadoFrete('', '');
  if (resultado) resultado.style.display = 'none';

  try {
    // Geocoding via Nominatim (OpenStreetMap) – gratuito, sem API key
    const query = encodeURIComponent(endereco + ', Brasil');
    const url = `https://nominatim.openstreetmap.org/search?q=${query}&format=json&limit=1`;

    const resp = await fetch(url, {
      headers: { 'Accept-Language': 'pt-BR', 'User-Agent': 'MercadoFamiliaGama/1.0' }
    });

    if (!resp.ok) throw new Error('Falha na requisição');

    const data = await resp.json();

    if (!data || data.length === 0) {
      mostrarResultadoFrete('erro', '❌ Endereço não encontrado. Tente incluir a cidade ou CEP.');
      return;
    }

    const { lat, lon, display_name } = data[0];
    const km = haversine(LOJA_LAT, LOJA_LNG, parseFloat(lat), parseFloat(lon));
    const kmArredondado = Math.round(km * 10) / 10;
    const valorFrete = calcularValorFrete(km);

    // Salva para usar no resumo
    salvarFreteCalc(valorFrete);

    // Monta mensagem
    let tipo, msg;
    if (valorFrete === 0) {
      tipo = 'gratis';
      msg = `🎉 <strong>Frete Grátis!</strong> Seu endereço está a apenas <strong>${kmArredondado} km</strong> da nossa loja.<br>
              <span class="frete-distancia">📍 ${display_name}</span>`;
    } else if (valorFrete === -1) {
      tipo = 'erro';
      msg = `📞 <strong>Entrega sob consulta.</strong> Seu endereço está a <strong>${kmArredondado} km</strong> da loja — acima de ${FRETE_MAX_KM} km.<br>
              Entre em contato para verificar a disponibilidade.<br>
              <span class="frete-distancia">📍 ${display_name}</span>`;
    } else {
      tipo = 'pago';
      msg = `🚚 <strong>Frete: ${fmt(valorFrete)}</strong> — Distância de <strong>${kmArredondado} km</strong> da nossa loja.<br>
              <span class="frete-distancia">📍 ${display_name}</span>`;
    }

    mostrarResultadoFrete(tipo, msg);
    atualizarResumo();

  } catch (err) {
    console.error(err);
    mostrarResultadoFrete('erro', '❌ Não foi possível calcular o frete. Verifique o endereço ou tente novamente.');
  } finally {
    btn.disabled = false;
    btn.textContent = '📍 Calcular';
  }
}

function mostrarResultadoFrete(tipo, msg) {
  const el = document.getElementById('freteResultado');
  if (!el) return;
  el.className = 'frete-resultado';
  if (tipo) {
    el.classList.add(tipo);
    el.innerHTML = msg;
    el.style.display = 'block';
  } else {
    el.style.display = 'none';
  }
}

/* ══════════════════════════════════════════════
   NAVEGAÇÃO
══════════════════════════════════════════════ */
function toggleMenu() {
  document.getElementById('navLinks').classList.toggle('open');
}

/* ══════════════════════════════════════════════
   FILTRO DE PRODUTOS
══════════════════════════════════════════════ */
function filterProd(cat, btn) {
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.produto-card').forEach(card => {
    card.style.display = (cat === 'todos' || card.dataset.cat === cat) ? '' : 'none';
  });
}

/* ══════════════════════════════════════════════
   FORMULÁRIO DE CONTATO
══════════════════════════════════════════════ */
function enviarFormulario() {
  const nome = document.getElementById('nome').value.trim();
  const email = document.getElementById('email').value.trim();
  const assunto = document.getElementById('assunto').value;
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
  ['nome', 'email', 'telefone', 'assunto', 'mensagem'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = '';
  });
  setTimeout(() => {
    const msg = document.getElementById('sucessoMsg');
    if (msg) msg.style.display = 'none';
  }, 5000);
}

/* ══════════════════════════════════════════════
   TRABALHE CONOSCO (multi-step)
══════════════════════════════════════════════ */
const subareasPorArea = {
  escritorio: {
    label: 'Escritório',
    opcoes: [
      { value: 'ti', label: '💻 Desenvolvedor de TI' },
      { value: 'marketing', label: '📣 Marketing & Redes Sociais' },
      { value: 'financeiro', label: '💰 Financeiro / Contabilidade' },
      { value: 'rh', label: '👥 Recursos Humanos' },
      { value: 'compras', label: '🛒 Compras & Suprimentos' },
      { value: 'adm', label: '📋 Assistente Administrativo' },
    ]
  },
  unidade: {
    label: 'Trabalhar na Unidade',
    opcoes: [
      { value: 'caixa', label: '🖥️ Operador(a) de Caixa' },
      { value: 'repositor', label: '📦 Repositor(a) de Produtos' },
      { value: 'faxineiro', label: '🧹 Auxiliar de Limpeza' },
      { value: 'acougue', label: '🥩 Auxiliar de Açougue' },
      { value: 'hortifruti', label: '🥦 Auxiliar de Hortifruti' },
      { value: 'padaria', label: '🍞 Auxiliar de Padaria' },
      { value: 'seguranca', label: '🛡️ Segurança Patrimonial' },
      { value: 'estoque', label: '🏭 Auxiliar de Estoque' },
    ]
  },
  logistica: {
    label: 'Logística & Entregas',
    opcoes: [
      { value: 'motorista', label: '🚚 Motorista Entregador' },
      { value: 'ajudante', label: '📬 Ajudante de Entrega' },
      { value: 'separacao', label: '📋 Separador de Pedidos' },
    ]
  },
  gerencia: {
    label: 'Gerência & Supervisão',
    opcoes: [
      { value: 'gerente', label: '🏆 Gerente de Loja' },
      { value: 'supervisor', label: '📊 Supervisor de Setor' },
      { value: 'lider', label: '⭐ Líder de Equipe' },
    ]
  }
};

let stepAtual = 1;
const totalSteps = 3;

function atualizarSteps() {
  document.querySelectorAll('.step').forEach((el, i) => {
    const num = i + 1;
    el.classList.remove('active', 'done');
    if (num < stepAtual) el.classList.add('done');
    if (num === stepAtual) el.classList.add('active');
  });
  document.querySelectorAll('.step-line').forEach((el, i) => {
    el.classList.toggle('done', i + 1 < stepAtual);
  });
  document.querySelectorAll('.form-step').forEach((el, i) => {
    el.classList.toggle('active', i + 1 === stepAtual);
  });
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
  if (stepAtual > 1) { stepAtual--; atualizarSteps(); }
}

function validarStep(step) {
  if (step === 1) {
    const nome = document.getElementById('tc-nome')?.value.trim();
    const nasc = document.getElementById('tc-nascimento')?.value;
    const email = document.getElementById('tc-email')?.value.trim();
    const tel = document.getElementById('tc-telefone')?.value.trim();
    if (!nome || !nasc || !email || !tel) { mostrarErro('Por favor, preencha todos os campos obrigatórios do Passo 1.'); return false; }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { mostrarErro('Por favor, informe um e-mail válido.'); return false; }
    const idade = new Date().getFullYear() - new Date(nasc).getFullYear();
    if (idade < 16) { mostrarErro('A idade mínima para candidatura é de 16 anos.'); return false; }
    esconderErro();
    return true;
  }
  if (step === 2) {
    const area = document.getElementById('tc-area')?.value;
    if (!area) { mostrarErro('Por favor, selecione uma área de interesse.'); return false; }
    const checks = document.querySelectorAll('.subarea-check input[type="checkbox"]:checked');
    if (checks.length === 0) { mostrarErro('Por favor, selecione pelo menos uma função de interesse.'); return false; }
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
  if (!area || !subareasPorArea[area]) { wrapper.classList.remove('visible'); container.innerHTML = ''; return; }
  const dados = subareasPorArea[area];
  container.innerHTML = dados.opcoes.map(op => `
    <label class="subarea-check">
      <input type="checkbox" name="funcao" value="${op.value}">${op.label}
    </label>`).join('');
  wrapper.classList.add('visible');
}

function enviarCandidatura() {
  if (!validarStep(3)) return;
  const nome = document.getElementById('tc-nome')?.value.trim();
  const checks = [...document.querySelectorAll('.subarea-check input[type="checkbox"]:checked')]
    .map(c => c.parentElement.textContent.trim()).join(', ');
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

/* ══════════════════════════════════════════════
   INICIALIZAÇÃO
══════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  atualizarBadge();

  // Página do carrinho
  if (document.getElementById('listaItens')) {
    renderCarrinho();

    // Restaura endereço e frete da sessão anterior (se houver)
    const freteInfo = lerFreteCalc();
    if (freteInfo !== null) {
      atualizarResumo();
      // Destaca faixa sem precisar recalcular
      // (não sabemos a distância exata sem refazer o geocoding, então apenas atualizamos o resumo)
    }
  }

  // Formulário trabalhe conosco
  if (document.querySelector('.progress-steps')) {
    atualizarSteps();
  }
});