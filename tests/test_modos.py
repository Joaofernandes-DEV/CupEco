"""Modos Normal e Simples (J13, D13, D31) e o aviso mínimo de cada modo (J6, D30)."""

import json
import random
from dataclasses import replace
from importlib import resources

import pytest

from cupeco.dominio.ataques import (
    AVISO_MINIMO_NORMAL,
    AVISO_MINIMO_SIMPLES,
    DadosAtaque,
    Roteiro,
    TipoAtaque,
)
from cupeco.dominio.batalha import Batalha, Replay, carregar_arena
from cupeco.dominio.chefe import Chefe, DadosChefe, DadosFase, carregar_chefe
from cupeco.dominio.comandos import NENHUM, Botao
from cupeco.dominio.dados import PACOTE_CONTEUDO, DadosInvalidos
from cupeco.dominio.modos import (
    DadosModo,
    Modo,
    TabelaModos,
    aplicar_modo,
    carregar_modos,
    disparos,
    validar_modos,
)

RAJADA = DadosAtaque(
    "raios",
    TipoAtaque.RAJADA,
    aviso=20,
    duracao=30,
    espera=15,
    intervalo=5,
    velocidade=6.0,
    origem=(1200.0, 600.0),
)
LEQUE = DadosAtaque(
    "leque",
    TipoAtaque.LEQUE,
    aviso=21,
    duracao=1,
    espera=10,
    velocidade=5.0,
    espalhamento=((1.0, 0.0), (0.965926, 0.258819), (0.965926, -0.258819)),
)
LEQUE_REPETIDO = replace(LEQUE, nome="leque duplo", duracao=20, intervalo=10)
MIRADO = DadosAtaque(
    "mirado", TipoAtaque.MIRADO, aviso=20, duracao=1, espera=10, velocidade=10.0, origem=(0.0, 0.0)
)
CHUVA = DadosAtaque(
    "chuva",
    TipoAtaque.CHUVA,
    aviso=30,
    duracao=1,
    espera=10,
    quantidade=4,
    velocidade=7.0,
    faixa=(100.0, 1100.0),
)
ZONA = DadosAtaque(
    "trilhas", TipoAtaque.ZONA, aviso=40, duracao=60, espera=20, area=(0.0, 600.0, 1280.0, 40.0)
)
INIMIGOS = DadosAtaque(
    "celulares",
    TipoAtaque.INIMIGOS,
    aviso=20,
    duracao=1,
    espera=30,
    quantidade=3,
    velocidade=3.0,
    vida_inimigo=4,
    origem=(1000.0, 300.0),
)
ATAQUES = (RAJADA, LEQUE, LEQUE_REPETIDO, MIRADO, CHUVA, ZONA, INIMIGOS)

CHEFE = DadosChefe(
    "Chefe de Teste",
    1000,
    60,
    True,
    (
        DadosFase("um", 100, 120, 160, ((1000, 500), (1100, 500)), 2.0, (RAJADA, LEQUE)),
        DadosFase("dois", 66, 80, 80, ((900, 300),), 3.0, (LEQUE_REPETIDO, INIMIGOS, MIRADO)),
        DadosFase("três", 33, 200, 100, ((800, 560),), 0.0, (CHUVA, ZONA)),
    ),
)
ARENA = replace(carregar_arena(), alvo=None, lancador=None)


def chefes_do_jogo():
    """Todos os chefes de `conteudo/chefes/` (o Dom entra no PR 4 da Fase 2)."""
    pasta = resources.files(PACOTE_CONTEUDO).joinpath("chefes")
    if not pasta.is_dir():
        return []
    nomes = sorted(
        a.name.removesuffix(".toml") for a in pasta.iterdir() if a.name.endswith(".toml")
    )
    return [carregar_chefe(nome) for nome in nomes]


def ataques_de(dados):
    return [ataque for fase in dados.fases for ataque in fase.ataques]


def quadros_sem_perigo(ataque):
    """Quadros desde o começo do aviso até o primeiro tiro, inimigo ou zona que machuca."""
    r = Roteiro((ataque,), random.Random(1))
    for quadro in range(ataque.aviso + ataque.duracao + 1):
        disparo, _ = r.atualizar((1000.0, 400.0), (200.0, 575.0))
        if disparo.projeteis or disparo.inimigos or r.zona_ativa is not None:
            return quadro
    raise AssertionError(f"{ataque.nome} não causou perigo")


def total_disparado(ataque):
    """Projéteis e inimigos que um ciclo do ataque solta."""
    r = Roteiro((ataque,), random.Random(1))
    total = 0
    for _ in range(ataque.aviso + ataque.duracao):
        disparo, _ = r.atualizar((1000.0, 400.0), (200.0, 575.0))
        total += len(disparo.projeteis) + len(disparo.inimigos)
    return total


def simples(ataque):
    """O ataque como fica no Simples, dentro de um chefe de uma fase só."""
    fase = DadosFase("única", 100, 50, 50, ((0, 0),), 1.0, (ataque,))
    return aplicar_modo(DadosChefe("x", 100, 10, False, (fase,)), Modo.SIMPLES).fases[0].ataques[0]


# --- tabela de modos -----------------------------------------------------------------


def test_modos_do_jogo():
    tabela = carregar_modos()
    assert tabela.de(Modo.NORMAL) == DadosModo(vida=100, projeteis=100, velocidade=100, aviso=100)
    assert tabela.de(Modo.SIMPLES) == DadosModo(vida=70, projeteis=70, velocidade=80, aviso=150)


NORMAL = DadosModo(100, 100, 100, 100)


@pytest.mark.parametrize(
    ("normal", "simples", "mensagem"),
    [
        (NORMAL, DadosModo(70, 0, 80, 150), "simples.projeteis: precisa ser positivo"),
        (NORMAL, DadosModo(70, 70, 80, 90), "simples.aviso: o aviso nunca diminui"),
        (DadosModo(100, 100, 100, 80), DadosModo(70, 70, 80, 150), "normal.aviso: o aviso nunca"),
        (NORMAL, DadosModo(120, 70, 80, 150), "simples.vida: o Simples não pode passar do Normal"),
        (NORMAL, DadosModo(70, 70, 110, 150), "simples.velocidade: o Simples não pode passar"),
        (DadosModo(100, 100, 100, 150), DadosModo(70, 70, 80, 120), "avisar menos que o Normal"),
    ],
)
def test_modos_invalidos(normal, simples, mensagem):
    with pytest.raises(DadosInvalidos, match=mensagem):
        validar_modos(TabelaModos(normal, simples))


# --- vida e fases (D13) --------------------------------------------------------------


def test_normal_nao_muda_nada():
    assert aplicar_modo(CHEFE, Modo.NORMAL) == CHEFE


def test_simples_tira_30_por_cento_da_vida_e_mantem_as_3_fases():
    dados = aplicar_modo(CHEFE, Modo.SIMPLES)
    assert dados.vida == 700
    assert [f.comeca_em for f in dados.fases] == [f.comeca_em for f in CHEFE.fases]
    assert [f.nome for f in dados.fases] == ["um", "dois", "três"]
    normal, facil = Chefe(CHEFE), Chefe(dados)
    assert facil.marcos == normal.marcos  # a barra da tela de derrota é a mesma (I6)
    assert [facil.limite_da_fase(i) for i in range(3)] == [700, 462, 231]


def test_simples_passa_pelas_3_fases_ate_a_derrota():
    chefe = Chefe(aplicar_modo(CHEFE, Modo.SIMPLES))
    fases_vistas = {chefe.fase}
    while not chefe.derrotado:
        chefe.levar_dano(1000)  # dano enorme: mesmo assim nenhuma fase é pulada
        fases_vistas.add(chefe.fase)
        while chefe.em_transicao:
            chefe.atualizar()
    assert fases_vistas == {0, 1, 2}


def test_chefe_que_perderia_uma_fase_no_simples_nem_carrega():
    fases = tuple(replace(fase, ataques=()) for fase in CHEFE.fases)
    pequeno = replace(CHEFE, vida=4, fases=fases)  # no Simples, 3 de vida: a fase 3 sumiria
    assert aplicar_modo(pequeno, Modo.NORMAL) == pequeno
    with pytest.raises(DadosInvalidos, match=r"fases\[2\].comeca_em: vida pequena demais"):
        aplicar_modo(pequeno, Modo.SIMPLES)


# --- aviso (J6, D30) -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("modo", "minimo"), [(Modo.NORMAL, AVISO_MINIMO_NORMAL), (Modo.SIMPLES, AVISO_MINIMO_SIMPLES)]
)
def test_todo_ataque_tem_o_aviso_minimo_do_modo(modo, minimo):
    """J6: pelo menos 20 quadros de aviso no Normal e 30 no Simples, nos dados e jogando."""
    assert minimo == {Modo.NORMAL: 20, Modo.SIMPLES: 30}[modo]
    chefes = [CHEFE, *chefes_do_jogo()]
    for dados in chefes:
        for ataque in ataques_de(aplicar_modo(dados, modo)):
            assert ataque.aviso >= minimo, (dados.nome, ataque.nome)
            assert quadros_sem_perigo(ataque) >= minimo, (dados.nome, ataque.nome)


def test_aviso_aumenta_50_por_cento_arredondado_para_cima():
    assert [simples(a).aviso for a in (RAJADA, LEQUE, CHUVA, ZONA)] == [30, 32, 45, 60]


def test_simples_com_aviso_curto_nao_carrega():
    tabela = TabelaModos(NORMAL, DadosModo(70, 70, 80, 120))  # 20 quadros viram só 24
    with pytest.raises(DadosInvalidos, match=r"pelo menos 30 quadros de aviso \(J6\)"):
        aplicar_modo(CHEFE, Modo.SIMPLES, tabela)


# --- velocidade ----------------------------------------------------------------------


def test_simples_deixa_projeteis_inimigos_e_chefe_20_por_cento_mais_lentos():
    dados = aplicar_modo(CHEFE, Modo.SIMPLES)
    for normal, facil in zip(CHEFE.fases, dados.fases, strict=True):
        assert facil.velocidade == pytest.approx(normal.velocidade * 0.8)
        for a, b in zip(normal.ataques, facil.ataques, strict=True):
            assert b.velocidade == pytest.approx(a.velocidade * 0.8)


# --- projéteis -----------------------------------------------------------------------


@pytest.mark.parametrize("ataque", ATAQUES, ids=lambda a: a.nome)
def test_simples_nunca_solta_mais_e_sempre_solta_algo(ataque):
    normal, facil = total_disparado(ataque), total_disparado(simples(ataque))
    assert facil <= normal
    assert (facil >= 1) == (normal >= 1)


def test_varios_disparos_ficam_mais_espacados():
    assert disparos(RAJADA) == 6
    assert disparos(simples(RAJADA)) == 4  # 6 × 0,7 ≈ 4
    assert (total_disparado(RAJADA), total_disparado(simples(RAJADA))) == (6, 4)
    assert simples(RAJADA).quantidade == RAJADA.quantidade


def test_disparo_unico_solta_menos_de_uma_vez():
    assert simples(CHUVA).quantidade == 3  # 4 × 0,7 ≈ 3
    assert simples(INIMIGOS).quantidade == 2  # celulares: 3 × 0,7 ≈ 2
    assert simples(MIRADO).quantidade == 1  # nunca menos que 1


def test_leque_mantem_o_formato_e_so_perde_disparos_repetidos():
    assert simples(LEQUE).espalhamento == LEQUE.espalhamento
    assert total_disparado(simples(LEQUE)) == 3
    assert total_disparado(LEQUE_REPETIDO) == 6
    assert total_disparado(simples(LEQUE_REPETIDO)) == 3


def test_zona_so_muda_o_aviso():
    assert replace(simples(ZONA), aviso=ZONA.aviso) == ZONA


# --- batalha e replay ----------------------------------------------------------------


def test_batalha_aplica_o_modo_no_chefe():
    normal = Batalha(1, ARENA, CHEFE)
    facil = Batalha(1, ARENA, CHEFE, Modo.SIMPLES)
    assert normal.modo is Modo.NORMAL and normal.chefe.vida == 1000
    assert facil.modo is Modo.SIMPLES and facil.chefe.vida == 700
    assert facil.dados_chefe is CHEFE  # os dados originais ficam guardados


def test_mesma_luta_no_simples_se_repete():
    comandos = [frozenset({Botao.TIRO}) if i % 40 < 30 else NENHUM for i in range(600)]
    retratos = []
    for _ in range(2):
        batalha = Batalha(9, ARENA, CHEFE, Modo.SIMPLES)
        for passo in comandos:
            batalha.atualizar(passo)
        retratos.append(batalha.retrato())
    assert retratos[0] == retratos[1]


def test_replay_guarda_o_modo():
    batalha = Batalha(3, ARENA, CHEFE, Modo.SIMPLES)
    batalha.atualizar(NENHUM)
    replay = Replay.da_batalha(batalha, chefe="teste")
    assert replay.modo is Modo.SIMPLES
    assert Replay.de_json(replay.para_json()) == replay


def test_replay_antigo_sem_modo_e_normal():
    texto = json.dumps({"versao": 1, "arena": "testes", "semente": 1, "comandos": [[]]})
    assert Replay.de_json(texto).modo is Modo.NORMAL


def test_replay_com_modo_desconhecido():
    texto = json.dumps({"versao": 1, "arena": "testes", "semente": 1, "modo": "x", "comandos": []})
    with pytest.raises(DadosInvalidos, match="modo desconhecido"):
        Replay.de_json(texto)
