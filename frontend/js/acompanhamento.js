// MatchPet - HU06: histórico de acompanhamento (usado pelo adotante e pelo responsável).
// GET /solicitacoes/{id}/acompanhamentos -> atualizações da mais recente para a mais antiga.

async function montarHistorico(solicitacaoId) {
  const caixa = document.createElement("div");
  caixa.className = "historico";
  try {
    const r = await fetch(`${API_URL}/solicitacoes/${solicitacaoId}/acompanhamentos`);
    if (!r.ok) throw new Error(r.status);
    const itens = await r.json();
    if (!itens.length) {
      const vazio = document.createElement("p");
      vazio.className = "dica";
      vazio.textContent = "Nenhuma atualização enviada ainda.";
      caixa.append(vazio);
      return caixa;
    }
    for (const item of itens) {
      const fig = document.createElement("figure");
      const img = document.createElement("img");
      img.src = `${API_URL}${item.foto_url}`;
      img.alt = `Foto enviada em ${formatarDataHoraMP(item.criado_em)}`;
      img.loading = "lazy";
      const legenda = document.createElement("figcaption");
      const data = document.createElement("b");
      data.textContent = formatarDataHoraMP(item.criado_em);
      const texto = document.createElement("span");
      texto.textContent = item.descricao;
      legenda.append(data, texto);
      fig.append(img, legenda);
      caixa.append(fig);
    }
  } catch (e) {
    const erro = document.createElement("p");
    erro.className = "feedback erro";
    erro.textContent = "Não foi possível carregar o histórico.";
    caixa.append(erro);
    console.error(e);
  }
  return caixa;
}
