"""HU03 - Perfil do adotante: um teste por cenário dos critérios de aceite."""
from conftest import campos_com_erro, dados_adotante, dados_perfil


def criar_adotante(client):
    return client.post("/adotantes", json=dados_adotante()).json()["id"]


def test_cenario1_perfil_completo_e_salvo(client):
    adotante_id = criar_adotante(client)

    resposta = client.put(f"/adotantes/{adotante_id}/perfil", json=dados_perfil())

    assert resposta.status_code == 200
    salvo = client.get(f"/adotantes/{adotante_id}/perfil").json()
    for campo, valor in dados_perfil().items():
        assert salvo[campo] == valor


def test_cenario2_perfil_com_campo_ausente_bloqueia_e_nada_e_gravado(client):
    adotante_id = criar_adotante(client)
    dados = dados_perfil()
    del dados["horas_sozinho"]

    resposta = client.put(f"/adotantes/{adotante_id}/perfil", json=dados)

    assert resposta.status_code == 422
    assert "horas_sozinho" in campos_com_erro(resposta)
    assert client.get(f"/adotantes/{adotante_id}/perfil").status_code == 404


def test_cenario2_perfil_com_valor_fora_das_opcoes_bloqueia_e_nada_e_gravado(client):
    adotante_id = criar_adotante(client)

    resposta = client.put(f"/adotantes/{adotante_id}/perfil", json=dados_perfil(tipo_moradia="castelo"))

    assert resposta.status_code == 422
    assert "tipo_moradia" in campos_com_erro(resposta)
    assert client.get(f"/adotantes/{adotante_id}/perfil").status_code == 404


def test_cenario3_atualizar_perfil_substitui_os_dados_no_mesmo_registro(client):
    adotante_id = criar_adotante(client)
    client.put(f"/adotantes/{adotante_id}/perfil", json=dados_perfil())

    resposta = client.put(
        f"/adotantes/{adotante_id}/perfil",
        json=dados_perfil(tipo_moradia="casa_com_quintal", tem_criancas=True),
    )

    assert resposta.status_code == 200
    salvo = client.get(f"/adotantes/{adotante_id}/perfil").json()
    assert salvo["tipo_moradia"] == "casa_com_quintal"
    assert salvo["tem_criancas"] is True
    assert salvo["adotante_id"] == adotante_id


def test_perfil_de_adotante_inexistente_retorna_404(client):
    assert client.put("/adotantes/999/perfil", json=dados_perfil()).status_code == 404
    assert client.get("/adotantes/999/perfil").status_code == 404
