// MatchPet - sessão do adotante e menu comum às telas da Sprint 2.
// O login (POST /login) devolve um token; ele fica no sessionStorage desta aba
// e vai no cabeçalho Authorization das ações que exigem adotante autenticado (HU05 e HU06).

// Tela aberta pelo http.server (porta 5500): API em localhost:8000.
// Tela aberta pela própria API (Codespaces ou porta 8000): mesmo endereço da tela.
const API_URL = window.location.port === "5500" ? "http://localhost:8000" : window.location.origin;

const Sessao = {
  obter() {
    try {
      return JSON.parse(sessionStorage.getItem("matchpet_sessao") || "null");
    } catch {
      return null;
    }
  },
  salvar(dados) {
    sessionStorage.setItem("matchpet_sessao", JSON.stringify(dados));
  },
  sair() {
    sessionStorage.removeItem("matchpet_sessao");
    window.location.href = "inicio.html";
  },
  // Telas do adotante: sem login, leva para a tela de login e volta depois.
  exigir() {
    const s = Sessao.obter();
    if (!s) {
      const volta = encodeURIComponent(window.location.pathname.split("/").pop() + window.location.search);
      window.location.href = `login.html?voltar=${volta}`;
      return null;
    }
    return s;
  },
  cabecalho() {
    const s = Sessao.obter();
    return s ? { Authorization: `Bearer ${s.token}` } : {};
  },
};

// Barra do topo, igual em todas as telas: marca à esquerda e os passos do fluxo à direita.
// area = "responsavel" mostra as telas do abrigo; senão, as do adotante (logado ou não).
function montarMenu(ativo, area) {
  const s = Sessao.obter();
  const barra = document.createElement("header");
  barra.className = "topbar";

  const marca = document.createElement("a");
  marca.className = "marca";
  marca.href = "inicio.html";
  marca.innerHTML = '<span aria-hidden="true">🐾</span> MatchPet';
  if (area === "responsavel") {
    const tag = document.createElement("small");
    tag.textContent = "Área do responsável";
    marca.append(tag);
  }

  const nav = document.createElement("nav");
  nav.className = "menu";
  nav.setAttribute("aria-label", "Navegação principal");
  let itens;
  if (area === "responsavel") {
    itens = [
      ["animais", "animais.html", "Animais"],
      ["gestao", "gestao.html", "Pedidos e acompanhamento"],
    ];
  } else if (s) {
    itens = [
      ["perfil", `perfil.html?id=${s.adotante_id}`, "Meus dados"],
      ["perfil-adocao", `perfil-adocao.html?id=${s.adotante_id}`, "Perfil de adoção"],
      ["compatibilidade", "compatibilidade.html", "Animais compatíveis"],
      ["minhas-adocoes", "minhas-adocoes.html", "Minhas adoções"],
    ];
  } else {
    itens = [
      ["disponiveis", "animais-disponiveis.html", "Animais"],
      ["login", "login.html", "Entrar"],
      ["cadastro", "index.html", "Criar cadastro"],
    ];
  }
  for (const [chave, href, texto] of itens) {
    const a = document.createElement("a");
    a.href = href;
    a.textContent = texto;
    if (chave === ativo) {
      a.className = "ativo";
      a.setAttribute("aria-current", "page");
    }
    nav.append(a);
  }
  if (area === "responsavel") {
    const sair = document.createElement("a");
    sair.href = "inicio.html";
    sair.className = "sair";
    sair.textContent = "Sair da área";
    nav.append(sair);
  } else if (s) {
    const sair = document.createElement("button");
    sair.type = "button";
    sair.className = "sair";
    sair.textContent = `Sair (${s.nome_completo.split(" ")[0]})`;
    sair.addEventListener("click", Sessao.sair);
    nav.append(sair);
  }
  barra.append(marca, nav);
  document.body.prepend(barra);
}

const ROTULOS_MP = {
  cao: "Cão", gato: "Gato",
  pequeno: "Pequeno", medio: "Médio", grande: "Grande",
  baixo: "Baixo", alto: "Alto", baixa: "Baixa", media: "Média", alta: "Alta",
  pendente: "Aguardando análise", aprovada: "Adoção concluída", recusada: "Não aprovada",
};
const rotuloMP = (v) => ROTULOS_MP[v] ?? v;

function formatarDataHoraMP(iso) {
  const data = new Date(iso);
  if (Number.isNaN(data.getTime())) return iso;
  return data.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

function mensagemMP(el, texto, tipo) {
  el.textContent = texto;
  el.className = `feedback ${tipo || ""}`;
}

// Coloca a foto do animal à esquerda do card (ou um ícone, se não houver foto)
// e move o conteúdo atual do card para a coluna da direita.
function comFoto(li, fotoUrl, especie, nome) {
  const corpo = document.createElement("div");
  corpo.className = "card-corpo";
  corpo.append(...li.childNodes);
  let midia;
  if (fotoUrl) {
    midia = document.createElement("img");
    midia.src = `${API_URL}${fotoUrl}`;
    midia.alt = nome ? `Foto de ${nome}` : "Foto do animal";
    midia.loading = "lazy";
  } else {
    midia = document.createElement("div");
    midia.setAttribute("aria-hidden", "true");
    midia.textContent = especie === "gato" ? "🐱" : "🐶";
  }
  midia.classList.add("card-foto");
  li.classList.add("com-foto");
  li.append(midia, corpo);
  return li;
}
