import random
from dataclasses import replace

import pytest

from cupeco.dominio.comandos import NENHUM, Botao
from cupeco.dominio.dados import DadosInvalidos
from cupeco.dominio.fisica import Caixa, Plataforma
from cupeco.dominio.jogador import (
    Estado,
    EventoJogador,
    Jogador,
    carregar_parametros_jogador,
    validar_parametros,
)

P = carregar_parametros_jogador()
CHAO = Plataforma(Caixa(-1000, 600, 4000, 120))
TABUA = Plataforma(Caixa(300, 450, 300, 16), atravessavel=True)
BEIRADA = Plataforma(Caixa(-1000, 600, 1200, 120))  # termina em x = 200

D, E, C, B = Botao.DIREITA, Botao.ESQUERDA, Botao.CIMA, Botao.BAIXO
PULO, DASH, TRAVAR = Botao.PULO, Botao.DASH, Botao.TRAVAR


def segurar(*botoes):
    return frozenset(botoes)


def rodar(jogador, comandos, passos, plataformas=(CHAO,)):
    eventos = []
    for _ in range(passos):
        eventos.extend(jogador.atualizar(comandos, plataformas))
    return eventos


def no_chao(x=100.0, plataformas=(CHAO,)):
    jogador = Jogador(x, 600)
    rodar(jogador, NENHUM, 1, plataformas)
    assert jogador.corpo.no_chao
    return jogador


def base(jogador):
    return jogador.corpo.y + jogador.corpo.altura


# --- parâmetros ----------------------------------------------------------------------


def test_parametros_do_toml_sao_validos():
    assert validar_parametros(P) is P
    assert P.altura_agachada < P.altura


@pytest.mark.parametrize(
    ("campo", "valor", "mensagem"),
    [
        ("velocidade_corrida", -1.0, "precisa ser positivo"),
        ("quadros_dash", 0, "precisa ser positivo"),
        ("altura_agachada", 200.0, "menor que a altura"),
        ("corte_pulo", 1.5, "vai de 0 a 1"),
    ],
)
def test_parametros_invalidos(campo, valor, mensagem):
    with pytest.raises(DadosInvalidos, match=mensagem):
        validar_parametros(replace(P, **{campo: valor}))


# --- chão e corrida ------------------------------------------------------------------


def test_comeca_caindo_e_pousa_parada():
    jogador = Jogador(100, 600)
    eventos = rodar(jogador, NENHUM, 1)
    assert eventos == [EventoJogador.POUSOU]
    assert jogador.estado is Estado.PARADA
    assert base(jogador) == 600


def test_corre_para_os_dois_lados_e_vira():
    jogador = no_chao()
    rodar(jogador, segurar(D), 10)
    assert jogador.corpo.x == 100 + 10 * P.velocidade_corrida
    assert jogador.virada == 1 and jogador.estado is Estado.CORRENDO
    rodar(jogador, segurar(E), 4)
    assert jogador.virada == -1
    rodar(jogador, NENHUM, 1)
    assert jogador.estado is Estado.PARADA and jogador.virada == -1


# --- pulo ----------------------------------------------------------------------------


def altura_do_pulo(passos_segurando):
    jogador = no_chao()
    topo = base(jogador)
    eventos = []
    for passo in range(120):
        comandos = segurar(PULO) if passo < passos_segurando else NENHUM
        eventos.extend(jogador.atualizar(comandos, [CHAO]))
        topo = min(topo, base(jogador))
    return 600 - topo, eventos, jogador


def test_pulo_segurado_chega_perto_de_200_pixels_e_volta():
    altura, eventos, jogador = altura_do_pulo(60)
    assert 180 <= altura <= 210
    assert eventos == [EventoJogador.PULOU, EventoJogador.POUSOU]
    assert jogador.corpo.no_chao


def test_soltar_o_pulo_cedo_da_um_pulo_curto():
    curto, _, _ = altura_do_pulo(1)
    longo, _, _ = altura_do_pulo(60)
    assert curto < longo * 0.5


def test_segurar_o_pulo_nao_pula_de_novo_ao_pousar():
    _, eventos, _ = altura_do_pulo(120)
    assert eventos.count(EventoJogador.PULOU) == 1


def sair_da_beirada():
    """Corre até sair da beirada e devolve a Dara no primeiro passo sem chão."""
    jogador = no_chao(140, (BEIRADA,))
    while jogador.corpo.no_chao:
        jogador.atualizar(segurar(D), [BEIRADA])
    return jogador


@pytest.mark.parametrize(
    ("espera", "pula"),
    [
        (0, True),
        (P.quadros_tolerancia_beirada - 1, True),
        (P.quadros_tolerancia_beirada + 2, False),
    ],
)
def test_tolerancia_na_beirada(espera, pula):
    jogador = sair_da_beirada()
    rodar(jogador, segurar(D), espera, (BEIRADA,))
    eventos = jogador.atualizar(segurar(D, PULO), [BEIRADA])
    assert (EventoJogador.PULOU in eventos) is pula


def passos_ate_pousar(altura_queda):
    jogador = Jogador(100, 600 - altura_queda)
    for passo in range(1, 200):
        if EventoJogador.POUSOU in jogador.atualizar(NENHUM, [CHAO]):
            return passo
    raise AssertionError("não pousou")


@pytest.mark.parametrize(
    ("antecedencia", "pula"), [(3, True), (P.quadros_pulo_guardado + 3, False)]
)
def test_pulo_apertado_antes_de_pousar(antecedencia, pula):
    pouso = passos_ate_pousar(150)
    jogador = Jogador(100, 450)
    eventos = []
    for passo in range(1, pouso + 2):
        comandos = segurar(PULO) if passo >= pouso - antecedencia else NENHUM
        eventos.extend(jogador.atualizar(comandos, [CHAO]))
    assert (EventoJogador.PULOU in eventos) is pula


# --- dash (D14) ----------------------------------------------------------------------


def test_dash_no_chao_percorre_distancia_fixa():
    jogador = no_chao()
    eventos = rodar(jogador, segurar(DASH), 1)
    assert eventos == [EventoJogador.DASH]
    rodar(jogador, segurar(DASH), P.quadros_dash - 1)
    assert jogador.corpo.x == 100 + P.velocidade_dash * P.quadros_dash
    assert base(jogador) == 600 and jogador.corpo.no_chao


def test_dash_tem_espera_antes_do_proximo():
    jogador = no_chao()
    rodar(jogador, segurar(DASH), 1)
    rodar(jogador, NENHUM, P.quadros_dash - 1)
    assert EventoJogador.DASH not in rodar(jogador, segurar(DASH), 1)
    rodar(jogador, NENHUM, P.quadros_espera_dash)
    assert EventoJogador.DASH in rodar(jogador, segurar(DASH), 1)


def test_dash_vai_para_onde_se_segura_ou_para_a_frente():
    jogador = no_chao(500)
    rodar(jogador, segurar(E, DASH), P.quadros_dash)
    assert jogador.corpo.x == 500 - P.velocidade_dash * P.quadros_dash
    assert jogador.virada == -1


def test_dash_no_ar_nao_cai_e_so_vale_uma_vez():
    jogador = no_chao()
    rodar(jogador, segurar(PULO), 12)
    eventos = rodar(jogador, segurar(PULO, DASH), 1)
    assert EventoJogador.DASH in eventos
    altura = jogador.corpo.y
    rodar(jogador, segurar(PULO), P.quadros_dash - 1)
    assert jogador.corpo.y == altura and jogador.estado is Estado.DASH
    rodar(jogador, NENHUM, P.quadros_espera_dash + 1)
    assert not jogador.corpo.no_chao
    assert EventoJogador.DASH not in rodar(jogador, segurar(DASH), 1)
    rodar(jogador, NENHUM, 60)
    assert jogador.corpo.no_chao
    rodar(jogador, NENHUM, P.quadros_espera_dash)
    assert EventoJogador.DASH in rodar(jogador, segurar(DASH), 1)


def test_dash_para_fora_da_beirada_so_cai_depois():
    jogador = no_chao(150, (BEIRADA,))
    rodar(jogador, segurar(DASH), P.quadros_dash, (BEIRADA,))
    assert base(jogador) == 600 and not jogador.corpo.no_chao
    rodar(jogador, NENHUM, 5, (BEIRADA,))
    assert base(jogador) > 600


# --- agachar, travar e mira ----------------------------------------------------------


def test_agachar_baixa_a_caixa_e_para_a_corrida():
    jogador = no_chao()
    rodar(jogador, segurar(B, D), 5)
    assert jogador.estado is Estado.AGACHADA
    assert jogador.corpo.altura == P.altura_agachada and base(jogador) == 600
    assert jogador.corpo.x == 100
    assert jogador.mira == (1, 0)
    rodar(jogador, NENHUM, 1)
    assert jogador.corpo.altura == P.altura and base(jogador) == 600


def test_travar_segura_no_lugar_e_mira_em_oito_direcoes():
    jogador = no_chao()
    casos = [
        (segurar(TRAVAR), (1, 0)),
        (segurar(TRAVAR, D, C), (1, -1)),
        (segurar(TRAVAR, C), (0, -1)),
        (segurar(TRAVAR, E), (-1, 0)),
        (segurar(TRAVAR, E, B), (-1, 1)),
        (segurar(TRAVAR, B), (-1, 1)),  # no chão, "para baixo" vira a diagonal da frente
    ]
    for comandos, mira in casos:
        rodar(jogador, comandos, 1)
        assert jogador.estado is Estado.TRAVADA
        assert jogador.mira == mira, comandos
    assert jogador.corpo.x == 100


def test_mira_parada_correndo_e_no_ar():
    jogador = no_chao()
    rodar(jogador, segurar(C), 1)
    assert jogador.mira == (0, -1)
    rodar(jogador, segurar(D, C), 1)
    assert jogador.mira == (1, -1)
    rodar(jogador, segurar(PULO), 3)
    rodar(jogador, segurar(PULO, B), 1)
    assert jogador.estado is Estado.NO_AR and jogador.mira == (0, 1)
    rodar(jogador, segurar(PULO, E, B), 1)
    assert jogador.mira == (-1, 1)


# --- plataforma atravessável ---------------------------------------------------------


def test_baixo_e_pulo_desce_da_tabua():
    jogador = Jogador(400, 450)
    rodar(jogador, NENHUM, 1, (TABUA, CHAO))
    assert base(jogador) == 450
    eventos = rodar(jogador, segurar(B, PULO), 1, (TABUA, CHAO))
    assert eventos == [EventoJogador.DESCEU]
    rodar(jogador, NENHUM, 40, (TABUA, CHAO))
    assert base(jogador) == 600


def test_baixo_e_pulo_no_chao_solido_pula():
    jogador = no_chao()
    assert EventoJogador.PULOU in rodar(jogador, segurar(B, PULO), 1)


def test_sobe_pela_tabua_e_para_em_cima_dela():
    jogador = no_chao(400, (TABUA, CHAO))
    rodar(jogador, segurar(PULO), 80, (TABUA, CHAO))
    assert base(jogador) == 450


# --- repetibilidade ------------------------------------------------------------------


def test_mesmos_comandos_dao_o_mesmo_caminho():
    sorteio = random.Random(42)
    botoes = list(Botao)
    sequencia = [frozenset(b for b in botoes if sorteio.random() < 0.2) for _ in range(600)]
    trajetos = []
    for _ in range(2):
        jogador = Jogador(400, 600)
        trajeto = []
        for comandos in sequencia:
            jogador.atualizar(comandos, [TABUA, CHAO])
            trajeto.append((jogador.corpo.x, jogador.corpo.y, jogador.estado, jogador.mira))
        trajetos.append(trajeto)
    assert trajetos[0] == trajetos[1]
