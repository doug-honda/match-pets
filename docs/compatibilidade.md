# Algoritmo de compatibilidade (HU04)

> **Status: implementada na Sprint 2 (HU04).** Os pesos ficam na tabela `criterio_compatibilidade` e podem ser ajustados pela PO sem mudar o código. O teste `backend/tests/test_hu04_compatibilidade.py` confere o exemplo calculado abaixo.

## Ideia geral

O cálculo acontece em duas etapas:

1. **Filtros eliminatórios.** Removem os animais que não podem ir para aquele lar, por exemplo um animal que não convive com crianças numa casa com crianças. Esses animais não aparecem na lista.
2. **Pontuação de 0 a 100.** Os animais que passaram pelos filtros recebem pontos em cinco critérios. Quanto maior a nota, mais compatível o animal é com o adotante.

A regra é fixa, sem aprendizado de máquina. Assim, cada nota pode ser explicada ao adotante e testada nos critérios de aceite.

## Dados necessários

### Perfil do adotante (HU03)

| Campo | Valores possíveis |
|---|---|
| Tipo de moradia | apartamento · casa sem quintal · casa com quintal |
| Há crianças na casa? | sim · não |
| Há outros animais na casa? | sim · não |
| Nível de atividade do adotante | baixo · médio · alto |
| Horas por dia que o animal ficará sozinho | até 4 h · de 4 a 8 h · mais de 8 h |
| Já teve animal de estimação? | sim · não |
| Espécie preferida | cão · gato · indiferente |
| Porte preferido | pequeno · médio · grande · indiferente |

Todos os campos são obrigatórios. Sem eles, o cálculo não é feito (cenário 3 da HU04).

### Cadastro do animal (HU02)

| Campo | Valores possíveis |
|---|---|
| Espécie | cão · gato |
| Porte | pequeno · médio · grande |
| Nível de energia | baixo · médio · alto |
| Convive bem com crianças? | sim · não |
| Convive bem com outros animais? | sim · não |
| Tolerância a ficar sozinho | baixa · média · alta |
| Exige tutor com experiência? | sim · não |
| Disponível para adoção? | sim · não |

## Etapa 1: filtros eliminatórios

Um animal é **removido** da lista quando qualquer uma destas condições for verdadeira:

| Filtro | Condição para eliminar |
|---|---|
| Disponibilidade | o animal não está disponível |
| Espécie | o adotante escolheu uma espécie e o animal é de outra |
| Crianças | há crianças na casa e o animal não convive bem com crianças |
| Outros animais | há outros animais na casa e o animal não convive bem com eles |

## Etapa 2: pontuação (0 a 100)

| Critério | Peso | Como pontua |
|---|---|---|
| **A. Espaço × porte** | 30 | Ver tabela A. Para **gatos**, vale sempre 30, já que eles se adaptam a qualquer tipo de moradia. |
| **B. Atividade do adotante × energia do animal** | 25 | Mesmo nível: 25 · um nível de diferença: 12 · dois níveis: 0 |
| **C. Tempo sozinho × tolerância do animal** | 20 | Ver tabela C |
| **D. Experiência** | 15 | O animal não exige experiência: 15 · exige e o adotante já teve animal: 15 · exige e o adotante nunca teve: 0 |
| **E. Porte preferido** | 10 | Indiferente ou mesmo porte: 10 · porte vizinho (ex.: pequeno × médio): 5 · porte oposto (pequeno × grande): 0 |

**Tabela A: espaço × porte (só para cães)**

| Moradia \ Porte | Pequeno | Médio | Grande |
|---|---|---|---|
| Apartamento | 30 | 15 | 0 |
| Casa sem quintal | 30 | 30 | 15 |
| Casa com quintal | 30 | 30 | 30 |

**Tabela C: horas sozinho × tolerância**

| Horas sozinho \ Tolerância | Baixa | Média | Alta |
|---|---|---|---|
| Até 4 h | 20 | 20 | 20 |
| De 4 a 8 h | 0 | 10 | 20 |
| Mais de 8 h | 0 | 0 | 10 |

**Nota final** = A + B + C + D + E

## Ordenação e destaque

- A lista é exibida em **ordem decrescente de nota**.
- Em caso de empate, aparece primeiro o animal cadastrado há mais tempo, que está esperando adoção há mais tempo.
- Cada animal recebe uma faixa, mostrada como selo no card:
  - **Alta compatibilidade**: nota de 75 a 100. É o **destaque** do cenário 2 da HU04.
  - **Média compatibilidade**: nota de 50 a 74.
  - **Baixa compatibilidade**: nota abaixo de 50.

## Exemplo calculado

**Adotante:** mora em apartamento, sem crianças, **tem outro animal**, nível de atividade médio, deixa o animal sozinho de 4 a 8 h, nunca teve animal, espécie indiferente, prefere porte pequeno.

| Animal | Características | Filtro | A | B | C | D | E | **Nota** | Faixa |
|---|---|---|---|---|---|---|---|---|---|
| Mel | cão, pequeno, energia média, tolerância alta, não exige experiência | passa | 30 | 25 | 20 | 15 | 10 | **100** | Alta |
| Nina | gata, pequena, energia baixa, tolerância alta, não exige experiência | passa | 30 | 12 | 20 | 15 | 10 | **87** | Alta |
| Luna | cão, médio, energia alta, tolerância média, não exige experiência | passa | 15 | 12 | 10 | 15 | 5 | **57** | Média |
| Thor | cão, grande, energia alta, tolerância média, exige experiência | passa | 0 | 12 | 10 | 0 | 0 | **22** | Baixa |
| Bob | cão, médio, **não convive com outros animais** | **eliminado** | – | – | – | – | – | – | – |

Ordem exibida: **Mel (100) → Nina (87) → Luna (57) → Thor (22)**. Bob não aparece. Mel e Nina recebem o selo de destaque.

## Texto sugerido para o card da HU04 no Trello

```
Regra de cálculo: ver docs/compatibilidade.md no GitHub.
1) Filtros eliminatórios: disponibilidade, espécie preferida, crianças, outros animais.
2) Nota 0–100 = Espaço×porte (30) + Atividade×energia (25) + Tempo sozinho×tolerância (20)
   + Experiência (15) + Porte preferido (10).
3) Faixas: Alta ≥ 75 (destacada) · Média 50–74 · Baixa < 50.

Cenário 1 - Compatibilidade calculada
Dado que o adotante possui perfil completo e existem animais disponíveis;
Quando acessar a consulta de animais;
Então o sistema deverá exibir, para cada animal que passou nos filtros, a nota de 0 a 100
calculada pela regra acima e a faixa correspondente.
Exemplo: adotante em apartamento com atividade média e animal "Mel" (cão pequeno,
energia média, tolerância alta, não exige experiência) → nota 100, faixa Alta.

Cenário 2 - Animais ordenados e destacados
Dado que existem dois ou mais animais com notas diferentes;
Quando o adotante visualizar os resultados;
Então o sistema deverá listá-los da maior para a menor nota e exibir o selo
"Alta compatibilidade" nos animais com nota igual ou maior que 75.
Animais eliminados pelos filtros não devem aparecer na lista.

Cenário 3 - Perfil insuficiente
Dado que falta alguma informação obrigatória no perfil do adotante;
Quando ele tentar consultar a compatibilidade;
Então o sistema deverá impedir o cálculo e indicar quais campos do perfil precisam ser preenchidos.
```

## Impacto nas outras histórias

- **HU02 (Cadastro do animal):** o formulário precisa ter os 8 campos da tabela "Cadastro do animal".
- **HU03 (Perfil do adotante):** o formulário precisa ter os 8 campos da tabela "Perfil do adotante". Este documento cumpre a tarefa "Definir dados e regras do perfil".
