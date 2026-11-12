"""
Cálculo de compatibilidade entre adotante e animal (HU04).

Regra definida em docs/compatibilidade.md, com 9 critérios:
- 4 eliminatórios: disponibilidade, espécie, crianças e outros animais;
- 5 de pontuação, que somam até 100: espaço x porte (30), atividade x energia (25),
  tempo sozinho x tolerância (20), experiência (15) e porte preferido (10).

Os pesos vêm da tabela criterio_compatibilidade. Cada critério de pontuação devolve
uma fração de 0 a 1 que é multiplicada pelo peso.
"""
from sqlalchemy.orm import Session

import models

CRITERIOS_PADRAO = [
    ("disponibilidade", "Disponibilidade", "eliminatorio", 0,
     "Animal indisponível não aparece na lista."),
    ("especie", "Espécie preferida", "eliminatorio", 0,
     "Se o adotante escolheu cão ou gato, animais da outra espécie não aparecem."),
    ("criancas", "Convivência com crianças", "eliminatorio", 0,
     "Casa com crianças: animais que não convivem bem com crianças não aparecem."),
    ("outros_animais", "Convivência com outros animais", "eliminatorio", 0,
     "Casa com outros animais: animais que não convivem bem com eles não aparecem."),
    ("espaco_porte", "Espaço x porte", "pontuacao", 30,
     "Tipo de moradia comparado ao porte do cão. Gatos pontuam o máximo."),
    ("atividade_energia", "Atividade x energia", "pontuacao", 25,
     "Nível de atividade do adotante comparado ao nível de energia do animal."),
    ("sozinho_tolerancia", "Tempo sozinho x tolerância", "pontuacao", 20,
     "Horas que o animal ficará sozinho comparadas à tolerância dele."),
    ("experiencia", "Experiência", "pontuacao", 15,
     "Animal que exige experiência pontua só se o adotante já teve animal."),
    ("porte_preferido", "Porte preferido", "pontuacao", 10,
     "Porte do animal comparado ao porte que o adotante prefere."),
]

NIVEIS = {"baixo": 0, "medio": 1, "alto": 2}
PORTES = {"pequeno": 0, "medio": 1, "grande": 2}

# Tabela A (só cães): moradia x porte, como fração do peso.
ESPACO_PORTE = {
    "apartamento": {"pequeno": 1.0, "medio": 0.5, "grande": 0.0},
    "casa_sem_quintal": {"pequeno": 1.0, "medio": 1.0, "grande": 0.5},
    "casa_com_quintal": {"pequeno": 1.0, "medio": 1.0, "grande": 1.0},
}
# Tabela C: horas sozinho x tolerância.
SOZINHO_TOLERANCIA = {
    "ate_4": {"baixa": 1.0, "media": 1.0, "alta": 1.0},
    "4_a_8": {"baixa": 0.0, "media": 0.5, "alta": 1.0},
    "mais_de_8": {"baixa": 0.0, "media": 0.0, "alta": 0.5},
}
# B: mesmo nível = 25 de 25; um nível de diferença = 12 de 25; dois níveis = 0.
ATIVIDADE_ENERGIA = {0: 1.0, 1: 12 / 25, 2: 0.0}
# E: mesmo porte (ou indiferente) = 10; porte vizinho = 5; oposto = 0.
PORTE_PREFERIDO = {0: 1.0, 1: 0.5, 2: 0.0}

FAIXA_ALTA = 75
FAIXA_MEDIA = 50


def garantir_criterios(db: Session) -> list[models.CriterioCompatibilidade]:
    """Cria os critérios padrão na primeira vez e devolve os critérios do banco."""
    criterios = db.query(models.CriterioCompatibilidade).order_by(models.CriterioCompatibilidade.id).all()
    if criterios:
        return criterios
    for codigo, nome, tipo, peso, descricao in CRITERIOS_PADRAO:
        db.add(models.CriterioCompatibilidade(codigo=codigo, nome=nome, tipo=tipo, peso=peso, descricao=descricao))
    db.commit()
    return db.query(models.CriterioCompatibilidade).order_by(models.CriterioCompatibilidade.id).all()


def eliminado(perfil: models.PerfilAdotante, animal: models.Animal) -> bool:
    if not animal.disponivel:
        return True
    if perfil.especie_preferida != "indiferente" and perfil.especie_preferida != animal.especie:
        return True
    if perfil.tem_criancas and not animal.convive_criancas:
        return True
    if perfil.tem_outros_animais and not animal.convive_outros_animais:
        return True
    return False


def fracoes(perfil: models.PerfilAdotante, animal: models.Animal) -> dict[str, float]:
    if animal.especie == "gato":
        espaco = 1.0
    else:
        espaco = ESPACO_PORTE[perfil.tipo_moradia][animal.porte]

    atividade = ATIVIDADE_ENERGIA[abs(NIVEIS[perfil.nivel_atividade] - NIVEIS[animal.nivel_energia])]
    sozinho = SOZINHO_TOLERANCIA[perfil.horas_sozinho][animal.tolerancia_sozinho]
    experiencia = 1.0 if (not animal.exige_experiencia or perfil.ja_teve_pet) else 0.0

    if perfil.porte_preferido == "indiferente":
        porte = 1.0
    else:
        porte = PORTE_PREFERIDO[abs(PORTES[perfil.porte_preferido] - PORTES[animal.porte])]

    return {
        "espaco_porte": espaco,
        "atividade_energia": atividade,
        "sozinho_tolerancia": sozinho,
        "experiencia": experiencia,
        "porte_preferido": porte,
    }


def faixa(nota: int) -> str:
    if nota >= FAIXA_ALTA:
        return "alta"
    if nota >= FAIXA_MEDIA:
        return "media"
    return "baixa"


def calcular(perfil: models.PerfilAdotante, animais: list[models.Animal], criterios) -> tuple[list[dict], int]:
    """Devolve os animais compatíveis, do maior para o menor, e quantos foram eliminados.
    Empate: aparece antes quem foi cadastrado primeiro (espera há mais tempo)."""
    pesos = {c.codigo: c.peso for c in criterios if c.tipo == "pontuacao"}
    resultado, eliminados = [], 0
    for animal in animais:
        if eliminado(perfil, animal):
            eliminados += 1
            continue
        pontos = {codigo: round(fracao * pesos.get(codigo, 0)) for codigo, fracao in fracoes(perfil, animal).items()}
        nota = sum(pontos.values())
        resultado.append({
            "animal": animal,
            "nota": nota,
            "faixa": faixa(nota),
            "destaque": nota >= FAIXA_ALTA,
            "pontos_por_criterio": pontos,
        })
    resultado.sort(key=lambda r: (-r["nota"], r["animal"].id))
    return resultado, eliminados
