"""HU04 - Compatibilidade entre adotante e animal: um teste por cenário dos critérios de aceite.
Usa o exemplo calculado em docs/compatibilidade.md (Mel 100, Nina 87, Luna 57, Thor 22, Bob eliminado)."""
from conftest import dados_adotante, dados_animal, dados_perfil

PERFIL_EXEMPLO = dados_perfil(
    tipo_moradia="apartamento", tem_criancas=False, tem_outros_animais=True, nivel_atividade="medio",
    horas_sozinho="4_a_8", ja_teve_pet=False, especie_preferida="indiferente", porte_preferido="pequeno",
)
ANIMAIS_EXEMPLO = [
    # Cadastrados fora da ordem da nota, para provar que a API ordena.
    dados_animal(nome="Thor", especie="cao", porte="grande", nivel_energia="alto", tolerancia_sozinho="media", exige_experiencia=True),
    dados_animal(nome="Luna", especie="cao", porte="medio", nivel_energia="alto", tolerancia_sozinho="media", exige_experiencia=False),
    dados_animal(nome="Nina", especie="gato", porte="pequeno", nivel_energia="baixo", tolerancia_sozinho="alta", exige_experiencia=False),
    dados_animal(nome="Mel", especie="cao", porte="pequeno", nivel_energia="medio", tolerancia_sozinho="alta", exige_experiencia=False),
    dados_animal(nome="Bob", especie="cao", porte="medio", convive_outros_animais=False),
    dados_animal(nome="Rex", disponivel=False),
]


def preparar(client, perfil=PERFIL_EXEMPLO):
    adotante_id = client.post("/adotantes", json=dados_adotante()).json()["id"]
    if perfil is not None:
        client.put(f"/adotantes/{adotante_id}/perfil", json=perfil)
    for animal in ANIMAIS_EXEMPLO:
        client.post("/animais", json=animal)
    return adotante_id


def test_criterios_e_pesos_ficam_no_banco(client):
    criterios = client.get("/criterios-compatibilidade").json()

    assert len(criterios) == 9
    assert sum(c["tipo"] == "eliminatorio" for c in criterios) == 4
    assert sum(c["peso"] for c in criterios if c["tipo"] == "pontuacao") == 100


def test_cenario1_compatibilidade_calculada_para_cada_animal(client):
    adotante_id = preparar(client)

    resposta = client.get(f"/adotantes/{adotante_id}/compatibilidade")

    assert resposta.status_code == 200
    notas = {r["animal"]["nome"]: r["nota"] for r in resposta.json()["animais"]}
    assert notas == {"Mel": 100, "Nina": 87, "Luna": 57, "Thor": 22}
    mel = resposta.json()["animais"][0]
    assert mel["pontos_por_criterio"] == {
        "espaco_porte": 30, "atividade_energia": 25, "sozinho_tolerancia": 20, "experiencia": 15, "porte_preferido": 10,
    }


def test_cenario2_animais_ordenados_e_mais_compativeis_destacados(client):
    adotante_id = preparar(client)

    corpo = client.get(f"/adotantes/{adotante_id}/compatibilidade").json()

    assert [r["animal"]["nome"] for r in corpo["animais"]] == ["Mel", "Nina", "Luna", "Thor"]
    assert [r["faixa"] for r in corpo["animais"]] == ["alta", "alta", "media", "baixa"]
    assert [r["destaque"] for r in corpo["animais"]] == [True, True, False, False]
    # Bob (não convive com outros animais) e Rex (indisponível) são eliminados pelos filtros.
    assert corpo["eliminados"] == 2


def test_cenario3_perfil_incompleto_bloqueia_o_calculo(client):
    adotante_id = preparar(client, perfil=None)

    resposta = client.get(f"/adotantes/{adotante_id}/compatibilidade")

    assert resposta.status_code == 409
    detalhe = resposta.json()["detail"]
    assert "perfil" in detalhe["mensagem"].lower()
    assert set(detalhe["campos_faltando"]) == set(PERFIL_EXEMPLO)


def test_filtros_de_especie_e_criancas(client):
    adotante_id = preparar(client, perfil=dados_perfil(especie_preferida="gato", tem_criancas=True, tem_outros_animais=False))
    client.post("/animais", json=dados_animal(nome="Mia", especie="gato", convive_criancas=False))

    nomes = [r["animal"]["nome"] for r in client.get(f"/adotantes/{adotante_id}/compatibilidade").json()["animais"]]

    assert nomes == ["Nina"]  # só gatos, e Mia não convive com crianças


def test_peso_alterado_no_banco_muda_a_nota(client):
    """Prova que o cálculo lê os pesos do banco: zerar 'porte preferido' tira 5 pontos da Luna."""
    from main import app
    from database import get_db
    import models

    adotante_id = preparar(client)
    client.get("/criterios-compatibilidade")
    db = next(app.dependency_overrides[get_db]())
    db.query(models.CriterioCompatibilidade).filter_by(codigo="porte_preferido").update({"peso": 0})
    db.commit()

    notas = {r["animal"]["nome"]: r["nota"] for r in client.get(f"/adotantes/{adotante_id}/compatibilidade").json()["animais"]}

    assert notas["Luna"] == 52
