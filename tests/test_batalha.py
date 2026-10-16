import random
from dataclasses import replace

import pytest

from cupeco.dominio.batalha import (
    Batalha,
    EventoBatalha,
    Replay,
    carregar_arena,
    validar_arena,
)
from cupeco.dominio.comandos import NENHUM, Botao
from cupeco.dominio.dados import DadosInvalidos
from cupeco.dominio.jogador import EventoJogador
from cupeco.dominio.materiais import Material
from cupeco.dominio.projeteis import Dono, Projetil

ARENA = carregar_arena()
TIRO, EX, PULO = Botao.TIRO, Botao.EX, Botao.PULO


def rodar(batalha, comandos, passos):
    eventos = []
    for _ in range(passos):
        eventos.extend(batalha.atualizar(comandos))
    return eventos


def sem_lancador():
    """Arena de testes com o lançador quase parado, para isolar o que se quer testar."""
    return replace(ARENA, lancador=replace(ARENA.lancador, quadros_entre_lancamentos=100_000))


# --- arena ---------------------------------------------------------------------------


def test_arena_de_testes_carrega():
    assert ARENA.nome == "Arena de testes"
    assert (ARENA.largura, ARENA.altura) == (1280, 720)
    assert len(ARENA.plataformas_fisicas) == 5
    assert sum(p.atravessavel for p in ARENA.plataformas_fisicas) == 2


def test_arena_inexistente_e_erro():
    with pytest.raises(DadosInvalidos, match="não existe a arena"):
        carregar_arena("lua")


def test_lancador_sem_alturas_e_erro():
    with pytest.raises(DadosInvalidos, match="pelo menos uma altura"):
        validar_arena(replace(ARENA, lancador=replace(ARENA.lancador, alturas=())), "x")


def test_dara_comeca_no_chao_da_arena():
    batalha = Batalha(1)
    eventos = batalha.atualizar(NENHUM)
    assert EventoJogador.POUSOU in eventos
    assert batalha.jogador.corpo.y + batalha.jogador.corpo.altura == ARENA.inicio[1]


# --- tiros no boneco -----------------------------------------------------------------


def test_atirar_no_boneco_causa_dano_e_enche_o_medidor():
    batalha = Batalha(1, sem_lancador())
    eventos = rodar(batalha, frozenset({TIRO}), 120)
    acertos = eventos.count(EventoBatalha.ACERTOU_ALVO)
    assert acertos > 5
    dano_do_tiro = batalha.jogador.arsenal.ativa.dano
    assert batalha.alvo.dano_recebido == acertos * dano_do_tiro
    pontos_por_dano = batalha.jogador.regras.pontos_por_dano
    assert batalha.jogador.medidor.pontos == min(500, acertos * dano_do_tiro * pontos_por_dano)


def test_tiro_que_acerta_some():
    batalha = Batalha(1, sem_lancador())
    for _ in range(200):
        batalha.atualizar(frozenset({TIRO}))
        for projetil in batalha.projeteis:
            if projetil.dono is Dono.JOGADOR and not projetil.perfura:
                assert not projetil.caixa.sobrepoe(batalha.alvo.caixa)


def test_tiro_perfurante_acerta_o_boneco_uma_vez_so():
    batalha = Batalha(1, sem_lancador())
    batalha.atualizar(NENHUM)
    batalha.jogador.medidor.ganhar(100)
    eventos = batalha.atualizar(frozenset({EX}))
    assert EventoJogador.EX in eventos
    eventos = rodar(batalha, NENHUM, 120)
    assert eventos.count(EventoBatalha.ACERTOU_ALVO) == 1
    assert batalha.alvo.dano_recebido == batalha.jogador.arsenal.ativa.ex.dano


def test_super_atinge_o_boneco():
    batalha = Batalha(1, sem_lancador())
    batalha.atualizar(NENHUM)
    batalha.jogador.medidor.ganhar(500)
    eventos = batalha.atualizar(frozenset({EX}))
    assert EventoBatalha.SUPER_ACERTOU in eventos
    assert batalha.alvo.dano_recebido == batalha.jogador.regras.dano_super


def test_tiros_que_saem_da_tela_somem():
    batalha = Batalha(1, sem_lancador())
    batalha.atualizar(NENHUM)
    rodar(batalha, frozenset({TIRO, Botao.CIMA}), 30)  # para cima: nunca acerta o boneco
    rodar(batalha, NENHUM, 120)
    assert batalha.projeteis == []


# --- lançador e resíduos -------------------------------------------------------------


def test_lancador_atira_no_intervalo():
    batalha = Batalha(3)
    eventos = rodar(batalha, NENHUM, 450)
    intervalo = ARENA.lancador.quadros_entre_lancamentos
    assert eventos.count(EventoBatalha.RESIDUO_LANCADO) == 450 // intervalo


def test_lancador_sorteia_todos_os_materiais():
    batalha = Batalha(5)
    vistos = set()
    for _ in range(45 * 80):
        batalha.atualizar(frozenset({PULO}))  # pulando sem parar, para sobreviver mais
        vistos.update(p.material for p in batalha.projeteis if p.dono is Dono.INIMIGO)
    assert vistos == {*Material, None}


def test_ficar_parada_leva_dano_dos_residuos():
    batalha = Batalha(7)
    eventos = rodar(batalha, NENHUM, 1200)
    assert EventoJogador.LEVOU_DANO in eventos
    assert batalha.jogador.vida < batalha.jogador.p.vida_maxima


def test_triagem_dentro_da_batalha():
    batalha = Batalha(1, sem_lancador())
    batalha.atualizar(NENHUM)
    batalha.atualizar(frozenset({PULO}))
    batalha.atualizar(NENHUM)
    assert EventoJogador.TENTOU_TRIAGEM in batalha.atualizar(frozenset({PULO}))
    cx, cy = batalha.jogador.corpo.caixa.centro
    residuo = Projetil(cx, cy, 30, 30, 0, 0, 1, 60, Dono.INIMIGO, material=Material.PLASTICO)
    batalha.projeteis.append(residuo)
    eventos = batalha.atualizar(NENHUM)
    assert EventoJogador.TRIAGEM_CERTA in eventos
    assert residuo not in batalha.projeteis
    assert batalha.jogador.medidor.pontos == 100


# --- replay (D8, D23, D24) -----------------------------------------------------------


def comandos_aleatorios(semente, passos):
    sorteio = random.Random(semente)
    botoes = list(Botao)
    return [frozenset(b for b in botoes if sorteio.random() < 0.25) for _ in range(passos)]


def jogar(semente, comandos):
    batalha = Batalha(semente)
    eventos = [batalha.atualizar(passo) for passo in comandos]
    return batalha, eventos


def test_mesma_semente_e_mesmos_comandos_dao_a_mesma_luta():
    comandos = comandos_aleatorios(11, 1200)
    primeira, eventos_1 = jogar(99, comandos)
    segunda, eventos_2 = jogar(99, comandos)
    assert primeira.retrato() == segunda.retrato()
    assert eventos_1 == eventos_2


def test_semente_diferente_muda_os_residuos():
    comandos = [NENHUM] * 300
    primeira, _ = jogar(1, comandos)
    segunda, _ = jogar(2, comandos)
    assert primeira.retrato() != segunda.retrato()


def test_replay_gravado_reproduz_a_luta_quadro_a_quadro():
    comandos = comandos_aleatorios(21, 900)
    original, eventos = jogar(42, comandos)
    replay = Replay.da_batalha(original)
    assert len(replay.comandos) == 900
    reproduzida, eventos_reproduzidos = Replay.de_json(replay.para_json()).reproduzir()
    assert reproduzida.retrato() == original.retrato()
    assert eventos_reproduzidos == eventos


def test_replay_em_json_ida_e_volta():
    replay = Replay(7, (frozenset({TIRO, PULO}), NENHUM, frozenset({Botao.DIREITA})))
    assert Replay.de_json(replay.para_json()) == replay


@pytest.mark.parametrize(
    ("texto", "mensagem"),
    [
        ('{"versao": 99, "arena": "testes", "semente": 1, "comandos": []}', "versão 99"),
        (
            '{"versao": 1, "arena": "testes", "semente": 1, "comandos": [["voar"]]}',
            "botão desconhecido",
        ),
    ],
)
def test_replay_invalido(texto, mensagem):
    with pytest.raises(DadosInvalidos, match=mensagem):
        Replay.de_json(texto)
