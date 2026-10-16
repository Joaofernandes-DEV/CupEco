"""Nota da luta (J14, D32)."""

from dataclasses import replace
from importlib import resources

import pytest

from cupeco.dominio.batalha import Batalha, carregar_arena
from cupeco.dominio.chefe import carregar_chefe
from cupeco.dominio.comandos import NENHUM
from cupeco.dominio.dados import PACOTE_CONTEUDO, DadosInvalidos
from cupeco.dominio.modos import Modo
from cupeco.dominio.nota import (
    Desempenho,
    Letra,
    TemposChefe,
    calcular_nota,
    carregar_regras_nota,
    desempenho_da,
    validar_regras_nota,
)

REGRAS = carregar_regras_nota()
MINUTO = 3600  # quadros
PERFEITA = Desempenho("dom_obsolescencio", 90 * 60, 3, 3, 2, Modo.NORMAL)
MINIMA = Desempenho("dom_obsolescencio", 10 * MINUTO, 1, 0, 0, Modo.NORMAL)


def test_regras_do_jogo():
    assert REGRAS.pontos_tempo == (20, 15, 10) and REGRAS.pontos_tempo_acima == 5
    assert REGRAS.limites_de("dom_obsolescencio") == (2 * MINUTO, 3 * MINUTO, 4 * MINUTO)
    assert [letra.letra for letra in REGRAS.letras] == ["A+", "A", "B", "C", "D"]


def test_todo_chefe_tem_tempos_na_nota():
    pasta = resources.files(PACOTE_CONTEUDO).joinpath("chefes")
    nomes = [a.name.removesuffix(".toml") for a in pasta.iterdir() if a.name.endswith(".toml")]
    assert nomes
    for nome in nomes:
        carregar_chefe(nome)
        assert REGRAS.limites_de(nome)


def test_luta_perfeita_tira_a_mais():
    nota = calcular_nota(PERFEITA)
    assert (nota.letra, nota.pontos) == ("A+", 100)
    assert (nota.pontos_tempo, nota.pontos_vida, nota.pontos_triagens, nota.pontos_super) == (
        20,
        30,
        30,
        20,
    )


def test_luta_minima_tira_d():
    nota = calcular_nota(MINIMA)
    assert (nota.letra, nota.pontos) == ("D", 15)  # 5 do tempo + 10 de uma vida


@pytest.mark.parametrize(
    ("quadros", "pontos"),
    [
        (1, 20),
        (2 * MINUTO, 20),  # no limite ainda conta a faixa
        (2 * MINUTO + 1, 15),
        (3 * MINUTO, 15),
        (4 * MINUTO, 10),
        (4 * MINUTO + 1, 5),
    ],
)
def test_faixas_de_tempo(quadros, pontos):
    assert calcular_nota(replace(PERFEITA, quadros=quadros)).pontos_tempo == pontos


def test_triagens_e_supers_tem_maximo():
    nota = calcular_nota(replace(PERFEITA, triagens_certas=12, supers=5))
    assert (nota.pontos_triagens, nota.pontos_super, nota.pontos) == (30, 20, 100)
    nota = calcular_nota(replace(PERFEITA, triagens_certas=1, supers=1))
    assert (nota.pontos_triagens, nota.pontos_super) == (10, 10)


@pytest.mark.parametrize(
    ("total_sem_tempo", "letra"),
    [(75, "A+"), (74, "A"), (65, "A"), (64, "B"), (50, "B"), (49, "C"), (30, "C"), (29, "D")],
)
def test_limites_das_letras(total_sem_tempo, letra):
    """Com 20 pontos de tempo, o total fica exatamente no limite de cada letra."""
    regras = replace(REGRAS, pontos_por_vida=1)
    desempenho = replace(PERFEITA, vida=total_sem_tempo, triagens_certas=0, supers=0)
    assert calcular_nota(desempenho, regras).letra == letra


def test_o_modo_fica_ao_lado_e_o_simples_nao_tem_teto():
    normal = calcular_nota(PERFEITA)
    simples = calcular_nota(replace(PERFEITA, modo=Modo.SIMPLES))
    assert simples.modo is Modo.SIMPLES and normal.modo is Modo.NORMAL
    assert (simples.letra, simples.pontos) == (normal.letra, normal.pontos)


def test_chefe_sem_tempos():
    with pytest.raises(DadosInvalidos, match="falta o chefe 'baron'"):
        calcular_nota(replace(PERFEITA, chefe="baron"))


# --- da batalha ----------------------------------------------------------------------


def vencer(modo):
    batalha = Batalha(1, carregar_arena("dom"), carregar_chefe("dom_obsolescencio"), modo)
    for _ in range(10):
        batalha.atualizar(NENHUM)
    chefe = batalha.chefe
    while not chefe.derrotado:
        chefe.levar_dano(chefe.vida)
        while chefe.em_transicao:
            batalha.atualizar(NENHUM)
    return batalha


@pytest.mark.parametrize("modo", list(Modo))
def test_nota_de_uma_luta_vencida(modo):
    batalha = vencer(modo)
    batalha.jogador.vida = 3  # a vida não depende dos ataques que a Dara levou no caminho
    batalha.jogador.estatisticas.triagens_certas = 2
    batalha.jogador.estatisticas.triagens_outra_cor = 5  # não valem pontos
    batalha.jogador.estatisticas.supers = 1
    desempenho = desempenho_da(batalha, "dom_obsolescencio")
    assert desempenho == Desempenho("dom_obsolescencio", batalha.quadro, 3, 2, 1, modo)
    nota = calcular_nota(desempenho)
    assert (nota.letra, nota.pontos, nota.modo) == ("B", 80, modo)  # 20 + 30 + 20 + 10


def test_sem_vitoria_nao_ha_nota():
    batalha = Batalha(1, carregar_arena("dom"), carregar_chefe("dom_obsolescencio"))
    with pytest.raises(ValueError, match="vitória"):
        desempenho_da(batalha, "dom_obsolescencio")


# --- dados inválidos -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("alteracao", "mensagem"),
    [
        ({"pontos_por_vida": 0}, "precisam ser positivos"),
        ({"pontos_tempo_acima": -1}, "precisam ser positivos"),
        ({"pontos_tempo": (10, 15, 20)}, "sem aumentar"),
        ({"pontos_tempo_acima": 30}, "sem aumentar"),
        ({"pontos_tempo": ()}, "sem aumentar"),
        ({"tempos": (TemposChefe("x", (1, 2)),)}, "um limite para cada faixa"),
        ({"tempos": (TemposChefe("x", (3, 2, 1)),)}, "positivos e crescentes"),
        ({"tempos": (TemposChefe("x", (0, 2, 3)),)}, "positivos e crescentes"),
        ({"tempos": (TemposChefe("x", (1, 2, 3)),) * 2}, "chefe repetido"),
        ({"letras": (Letra("A", 50), Letra("A", 0))}, "sem repetição"),
        ({"letras": (Letra("A", 50), Letra("B", 60), Letra("C", 0))}, "decrescentes"),
        ({"letras": (Letra("A", 50), Letra("B", 10))}, "o último em 0"),
        ({"letras": (Letra("A+", 101), Letra("D", 0))}, r"exige mais que o máximo \(100\)"),
    ],
)
def test_regras_invalidas(alteracao, mensagem):
    with pytest.raises(DadosInvalidos, match=mensagem):
        validar_regras_nota(replace(REGRAS, **alteracao), vida_maxima=3)
