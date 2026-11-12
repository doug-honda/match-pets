// MatchPet - Cadastro do Adotante
// Integração da interface com a API (FastAPI)


const form = document.getElementById("form-adotante");
const feedback = document.getElementById("feedback");
const btnEnviar = document.getElementById("btn-enviar");

function limparErros() {
  document.querySelectorAll(".erro").forEach((el) => (el.textContent = ""));
  feedback.textContent = "";
  feedback.className = "feedback";
}

function mostrarErroCampo(campo, mensagem) {
  const el = document.querySelector(`[data-erro="${campo}"]`);
  if (el) el.textContent = mensagem;
}

function validarFormulario(dados) {
  let valido = true;

  if (!dados.nome_completo.trim()) {
    mostrarErroCampo("nome_completo", "Informe o nome completo.");
    valido = false;
  }

  const cpfNumeros = dados.cpf.replace(/\D/g, "");
  if (cpfNumeros.length !== 11) {
    mostrarErroCampo("cpf", "CPF deve conter 11 dígitos.");
    valido = false;
  }

  if (!/^\S+@\S+\.\S+$/.test(dados.email)) {
    mostrarErroCampo("email", "E-mail inválido.");
    valido = false;
  }

  const telNumeros = dados.telefone.replace(/\D/g, "");
  if (telNumeros.length < 10 || telNumeros.length > 11) {
    mostrarErroCampo("telefone", "Telefone inválido.");
    valido = false;
  }

  if (dados.senha.length < 8) {
    mostrarErroCampo("senha", "A senha deve ter ao menos 8 caracteres.");
    valido = false;
  }

  const cepNumeros = dados.cep.replace(/\D/g, "");
  if (cepNumeros.length !== 8) {
    mostrarErroCampo("cep", "CEP deve conter 8 dígitos.");
    valido = false;
  }

  if (!dados.data_nascimento) {
    mostrarErroCampo("data_nascimento", "Informe a data de nascimento.");
    valido = false;
  }

  const obrigatoriosEndereco = {
    logradouro: "Informe o logradouro.",
    numero: "Informe o número.",
    bairro: "Informe o bairro.",
    cidade: "Informe a cidade.",
  };
  for (const [campo, mensagem] of Object.entries(obrigatoriosEndereco)) {
    if (!dados[campo].trim()) {
      mostrarErroCampo(campo, mensagem);
      valido = false;
    }
  }

  if (!/^[A-Za-z]{2}$/.test(dados.estado.trim())) {
    mostrarErroCampo("estado", "Use a sigla (ex.: SP).");
    valido = false;
  }

  return valido;
}

// Traduz a resposta de erro da API em mensagens na tela.
// Erro 422 (validação do FastAPI) chega como lista: cada item aponta o campo em "loc".
function mostrarErroApi(corpo) {
  const detalhe = corpo && corpo.detail;

  if (Array.isArray(detalhe)) {
    detalhe.forEach((erro) => {
      const campo = Array.isArray(erro.loc) ? erro.loc[erro.loc.length - 1] : null;
      const mensagem = (erro.msg || "Valor inválido.").replace(/^Value error, /, "");
      if (campo) mostrarErroCampo(campo, mensagem);
    });
    return "Corrija os campos destacados antes de continuar.";
  }

  if (detalhe && typeof detalhe === "object" && detalhe.campo) {
    mostrarErroCampo(detalhe.campo, detalhe.mensagem);
    return detalhe.mensagem;
  }

  return typeof detalhe === "string" ? detalhe : "Não foi possível concluir o cadastro.";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  limparErros();

  const formData = new FormData(form);
  const dados = Object.fromEntries(formData.entries());

  if (!validarFormulario(dados)) {
    feedback.textContent = "Corrija os campos destacados antes de continuar.";
    feedback.classList.add("erro");
    return;
  }

  btnEnviar.disabled = true;
  btnEnviar.textContent = "Enviando...";

  try {
    const resposta = await fetch(`${API_URL}/adotantes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    });

    // Um erro 500 pode vir sem JSON; nesse caso, segue com corpo vazio.
    const corpo = await resposta.json().catch(() => ({}));

    if (!resposta.ok) {
      feedback.textContent = mostrarErroApi(corpo);
      feedback.classList.add("erro");
      return;
    }

    feedback.textContent = `Cadastro criado com sucesso! Bem-vindo(a), ${corpo.nome_completo}.`;
    feedback.classList.add("sucesso");
    form.reset();

    // Já entra na conta com o e-mail e a senha recém-cadastrados, para o adotante
    // seguir pelo menu sem precisar fazer login de novo.
    try {
      const login = await fetch(`${API_URL}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: dados.email, senha: dados.senha }),
      });
      if (login.ok) Sessao.salvar(await login.json());
    } catch (erroLogin) {
      console.error(erroLogin);
    }

    // Leva o adotante ao próprio perfil (CA1 da HU01) depois de ler a mensagem.
    setTimeout(() => {
      window.location.href = `perfil.html?id=${encodeURIComponent(corpo.id)}`;
    }, 1500);
  } catch (erro) {
    feedback.textContent = "Erro de conexão com o servidor. Tente novamente.";
    feedback.classList.add("erro");
    console.error(erro);
  } finally {
    btnEnviar.disabled = false;
    btnEnviar.textContent = "Criar cadastro";
  }
});

// Máscaras simples de digitação
document.getElementById("cpf").addEventListener("input", (e) => {
  e.target.value = e.target.value
    .replace(/\D/g, "")
    .slice(0, 11)
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d{1,2})$/, "$1-$2");
});

document.getElementById("cep").addEventListener("input", (e) => {
  e.target.value = e.target.value
    .replace(/\D/g, "")
    .slice(0, 8)
    .replace(/(\d{5})(\d)/, "$1-$2");
});
