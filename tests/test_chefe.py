"""Chefe genérico (D28) e a batalha contra ele."""

from dataclasses import replace

import pytest

from cupeco.dominio.batalha import Batalha, EventoBatalha, Replay, Resultado, carregar_arena
from cupeco.dominio.chefe import Chefe, DadosChefe, DadosFase, EventoChefe, validar_chefe
from cupeco.dominio.comandos import NENHUM, Botao
from cupeco.dominio.dados import DadosInvalidos
from cupeco.dominio.jogador import EventoJogador

FASES = (
    DadosFase("um", 100, 120, 160, ((1000, 500), (1100, 500)), 2.0),
    DadosFase("dois", 66, 80, 80, ((900, 300),), 3.0),
    DadosFase("três", 33, 200, 100, ((800, 560),), 0.0),
)
DADOS = DadosChefe("Chefe de Teste", 300, 60, True, FASES)
# Arena de testes sem boneco nem lançador: só o chefe.
ARENA = replace(carregar_arena(), alvo=None, lancador=None)


def rodar_chefe(chefe, passos):
    eventos = []
    for _ in range(passos):
        eventos.extend(chefe.atualizar())
    return eventos


# --- dados ---------------------------------------------------------------------------


def test_dados_validos():
    assert validar_chefe(DADOS, "x") is DADOS


@pytest.mark.parametrize(
    ("alteracao", "mensagem"),
    [
        ({"vida": 0}, "vida: precisa ser positiva"),
        ({"fases": ()}, "pelo menos uma fase"),
        ({"fases": (replace(FASES[0], comeca_em=90),)}, "a primeira fase começa em 100"),
        ({"fases": (FASES[0], FASES[2], FASES[1])}, r"fases\[2\].comeca_em"),
        ({"fases": (FASES[0], replace(FASES[1], rota=()))}, "pelo menos um ponto"),
        ({"vida": 2}, "vida pequena demais"),
    ],
)
def test_dados_invalidos(alteracao, mensagem):
    with pytest.raises(DadosInvalidos, match=mensagem):
        validar_chefe(replace(DADOS, **alteracao), "x")


# --- vida e fases --------------------------------------------------------------------


def test_comeca_na_primeira_fase_com_vida_cheia():
    chefe = Chefe(DADOS)
    assert (chefe.vida, chefe.fase, chefe.vulneravel) == (300, 0, True)
    assert chefe.marcos == (pytest.approx(0.34), pytest.approx(0.67))
    assert chefe.progresso == 0


def test_dano_abaixo_do_limite_muda_de_fase_e_abre_a_transicao():
    chefe = Chefe(DADOS)
    assert chefe.levar_dano(50) == [EventoChefe.LEVOU_DANO]
    eventos = chefe.levar_dano(60)  # 190 < 198 (66% de 300)
    assert eventos == [EventoChefe.LEVOU_DANO, EventoChefe.MUDOU_FASE]
    assert chefe.fase == 1 and chefe.em_transicao and not chefe.vulneravel
    assert chefe.vida == 198  # para no limite da fase


def test_na_transicao_nao_leva_dano_e_depois_volta():
    chefe = Chefe(DADOS)
    chefe.levar_dano(102)
    assert chefe.levar_dano(50) == []
    assert chefe.vida == 198
    eventos = rodar_chefe(chefe, DADOS.quadros_transicao)
    assert EventoChefe.TERMINOU_TRANSICAO in eventos
    assert chefe.vulneravel
    chefe.levar_dano(10)
    assert chefe.vida == 188


def test_dano_enorme_nao_pula_fase():
    chefe = Chefe(DADOS)
    chefe.levar_dano(10_000)
    assert chefe.fase == 1 and chefe.vida == 198 and not chefe.derrotado
    rodar_chefe(chefe, DADOS.quadros_transicao)
    chefe.levar_dano(10_000)
    assert chefe.fase == 2 and chefe.vida == 99
    rodar_chefe(chefe, DADOS.quadros_transicao)
    eventos = chefe.levar_dano(10_000)
    assert eventos == [EventoChefe.LEVOU_DANO, EventoChefe.DERROTADO]
    assert chefe.derrotado and chefe.progresso == 1


def test_derrotado_nao_reage_mais():
    chefe = Chefe(replace(DADOS, fases=FASES[:1]))
    chefe.levar_dano(300)
    assert chefe.derrotado
    assert chefe.levar_dano(5) == []
    x, y = chefe.x, chefe.y
    rodar_chefe(chefe, 10)
    assert (chefe.x, chefe.y) == (x, y)


# --- movimento -----------------------------------------------------------------------


def test_anda_pela_rota_e_volta_ao_comeco():
    chefe = Chefe(DADOS)
    assert (chefe.x, chefe.y) == (1000, 500)
    rodar_chefe(chefe, 25)
    assert chefe.x == 1050  # 2 px por passo rumo a (1100, 500)
    rodar_chefe(chefe, 25)
    assert chefe.x == 1100
    rodar_chefe(chefe, 50)
    assert chefe.x == 1000


def test_nova_fase_troca_o_tamanho_e_a_rota():
    chefe = Chefe(DADOS)
    chefe.levar_dano(102)
    assert (chefe.caixa.largura, chefe.caixa.altura) == (80, 80)
    rodar_chefe(chefe, 200)
    assert (chefe.x, chefe.y) == (900, 300)


# --- batalha contra o chefe ----------------------------------------------------------


def test_batalha_sem_boneco_nem_lancador():
    batalha = Batalha(1, ARENA, DADOS)
    assert batalha.alvo is None and batalha.lancador is None
    assert batalha.alvos == [batalha.chefe]
    eventos = batalha.atualizar(NENHUM)
    assert EventoBatalha.RESIDUO_LANCADO not in eventos


def test_tiros_ferem_o_chefe_e_enchem_o_medidor():
    parado = replace(DADOS, fases=(replace(FASES[0], rota=((1000, 560),), velocidade=0.0),))
    batalha = Batalha(1, ARENA, parado)
    eventos = []
    for _ in range(120):
        eventos.extend(batalha.atualizar(frozenset({Botao.TIRO})))
    assert EventoBatalha.ACERTOU_ALVO in eventos
    assert batalha.chefe.vida < 300
    assert batalha.jogador.medidor.pontos > 0


def test_tiro_no_chefe_em_transicao_e_absorvido():
    parado = replace(
        DADOS, fases=tuple(replace(f, rota=((1000, 560),), velocidade=0.0) for f in FASES)
    )
    batalha = Batalha(1, ARENA, parado)
    batalha.atualizar(NENHUM)
    batalha.chefe.levar_dano(102)  # entra em transição
    vida, pontos = batalha.chefe.vida, batalha.jogador.medidor.pontos
    for _ in range(50):
        batalha.atualizar(frozenset({Botao.TIRO}))
    assert batalha.chefe.vida == vida
    assert batalha.jogador.medidor.pontos == pontos
    assert not any(p.caixa.sobrepoe(batalha.chefe.caixa) for p in batalha.projeteis)


def test_encostar_no_chefe_machuca():
    perto = replace(DADOS, fases=(replace(FASES[0], rota=((200, 560),), velocidade=0.0),))
    batalha = Batalha(1, ARENA, perto)
    eventos = batalha.atualizar(NENHUM)
    assert EventoJogador.LEVOU_DANO in eventos


def test_super_fere_o_chefe_e_vence_a_ultima_fase():
    batalha = Batalha(1, ARENA, replace(DADOS, fases=FASES[:1], vida=100))
    batalha.atualizar(NENHUM)
    batalha.jogador.medidor.ganhar(500)
    eventos = batalha.atualizar(frozenset({Botao.EX}))
    assert EventoBatalha.SUPER_ACERTOU in eventos and EventoChefe.DERROTADO in eventos
    assert batalha.resultado is Resultado.VITORIA


def test_resultado_derrota():
    batalha = Batalha(1, ARENA, DADOS)
    batalha.atualizar(NENHUM)
    assert batalha.resultado is None
    batalha.jogador.vida = 1
    batalha.jogador.tocar_perigo()
    assert batalha.resultado is Resultado.DERROTA


def test_replay_guarda_o_nome_do_chefe():
    replay = Replay(3, (NENHUM,), "testes", "dom_obsolescencio")
    assert Replay.de_json(replay.para_json()) == replay
    sem_chefe = Replay(3, (NENHUM,))
    assert Replay.de_json(sem_chefe.para_json()).chefe is None


def test_mesma_luta_contra_o_chefe_se_repete():
    comandos = [
        frozenset({Botao.TIRO, Botao.PULO}) if i % 30 < 10 else frozenset({Botao.TIRO})
        for i in range(600)
    ]
    retratos = []
    for _ in range(2):
        batalha = Batalha(5, ARENA, DADOS)
        for passo in comandos:
            batalha.atualizar(passo)
        retratos.append(batalha.retrato())
    assert retratos[0] == retratos[1]
