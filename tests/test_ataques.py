"""Peças de ataque, roteiro e inimigos menores (D29, D30, D34, J6)."""

import math
import random
from dataclasses import replace

import pytest

from cupeco.dominio.ataques import (
    AVISO_MINIMO_NORMAL,
    DadosAtaque,
    Etapa,
    Inimigo,
    Roteiro,
    TipoAtaque,
    validar_ataque,
)
from cupeco.dominio.batalha import Batalha, EventoBatalha, carregar_arena
from cupeco.dominio.chefe import Chefe, DadosChefe, DadosFase, EventoChefe, validar_chefe
from cupeco.dominio.comandos import NENHUM, Botao
from cupeco.dominio.dados import DadosInvalidos
from cupeco.dominio.jogador import EventoJogador
from cupeco.dominio.materiais import Material

RAJADA = DadosAtaque(
    "raios",
    TipoAtaque.RAJADA,
    aviso=20,
    duracao=10,
    espera=15,
    intervalo=5,
    velocidade=6.0,
    origem=(1200.0, 600.0),
)
LEQUE = DadosAtaque(
    "leque",
    TipoAtaque.LEQUE,
    aviso=24,
    duracao=1,
    espera=10,
    velocidade=5.0,
    espalhamento=((1.0, 0.0), (0.965926, 0.258819), (0.965926, -0.258819)),
)
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
    materiais=("metal",),
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
    quantidade=2,
    velocidade=3.0,
    vida_inimigo=4,
    origem=(1000.0, 300.0),
)


def roteiro(*ataques, semente=1):
    return Roteiro(tuple(ataques), random.Random(semente))


def passos(r, quantidade, centro=(1000.0, 400.0), alvo=(200.0, 575.0)):
    disparos = []
    for _ in range(quantidade):
        disparo, _ = r.atualizar(centro, alvo)
        disparos.append(disparo)
    return disparos


# --- validação (J6, D30) -------------------------------------------------------------


@pytest.mark.parametrize("ataque", [RAJADA, LEQUE, MIRADO, CHUVA, ZONA, INIMIGOS])
def test_ataques_de_exemplo_sao_validos(ataque):
    assert validar_ataque(ataque, "x") is ataque


@pytest.mark.parametrize(
    ("ataque", "mensagem"),
    [
        (replace(RAJADA, aviso=AVISO_MINIMO_NORMAL - 1), r"pelo menos 20 quadros de aviso \(J6\)"),
        (replace(RAJADA, velocidade=0.0), "velocidade: precisa ser positiva"),
        (replace(RAJADA, direcao=(1.0, 1.0)), "direcao: precisa ter tamanho 1"),
        (replace(LEQUE, espalhamento=()), "espalhamento"),
        (replace(CHUVA, faixa=(500.0, 100.0)), "faixa"),
        (replace(ZONA, area=None), "a zona precisa de uma área"),
        (replace(RAJADA, materiais=("madeira",)), "materiais"),
        (replace(RAJADA, materiais=()), "materiais"),
        (replace(INIMIGOS, vida_inimigo=0), "vida_inimigo"),
        (replace(RAJADA, duracao=0), "duração"),
    ],
)
def test_ataque_invalido(ataque, mensagem):
    with pytest.raises(DadosInvalidos, match=mensagem):
        validar_ataque(ataque, "x")


def test_chefe_com_ataque_sem_aviso_suficiente_nao_carrega():
    fase = DadosFase("um", 100, 100, 100, ((1000, 500),), 0.0, (replace(RAJADA, aviso=5),))
    with pytest.raises(DadosInvalidos, match=r"fases\[0\].ataques\[0\].aviso"):
        validar_chefe(DadosChefe("x", 100, 30, True, (fase,)), "chefes.x")


# --- etapas --------------------------------------------------------------------------


def test_nada_sai_durante_o_aviso_e_depois_o_ataque_age():
    r = roteiro(RAJADA)
    aviso = passos(r, RAJADA.aviso)
    assert r.etapa is Etapa.AVISO
    assert all(not d.projeteis for d in aviso)
    ativo = passos(r, RAJADA.duracao)
    disparos = [len(d.projeteis) for d in ativo]
    assert disparos == [1, 0, 0, 0, 0, 1, 0, 0, 0, 0]  # a cada 5 quadros
    assert r.etapa is Etapa.ATIVO
    passos(r, 1)
    assert r.etapa is Etapa.ESPERA


def test_espera_e_depois_um_novo_aviso():
    r = roteiro(RAJADA)
    passos(r, RAJADA.aviso + RAJADA.duracao + RAJADA.espera)
    assert r.etapa is Etapa.ESPERA
    _, comecos = r.atualizar((0.0, 0.0), (0.0, 0.0))
    assert comecos == ["aviso"] and r.etapa is Etapa.AVISO


def test_zona_avisa_antes_e_machuca_so_depois():
    r = roteiro(ZONA)
    passos(r, ZONA.aviso)
    assert r.zona_avisada is not None and r.zona_ativa is None
    passos(r, 1)
    assert r.zona_ativa is not None and r.zona_avisada is None
    passos(r, ZONA.duracao)
    assert r.zona_ativa is None


def test_sem_repetir_o_mesmo_ataque_seguido():
    r = roteiro(RAJADA, LEQUE, semente=3)
    escolhidos = []
    for _ in range(400):
        _, comecos = r.atualizar((0.0, 0.0), (0.0, 0.0))
        if "aviso" in comecos:
            escolhidos.append(r.atual.nome)
    assert len(escolhidos) > 5
    assert all(a != b for a, b in zip(escolhidos, escolhidos[1:], strict=False))


def test_mesma_semente_mesma_sequencia():
    def sequencia(semente):
        r = roteiro(RAJADA, LEQUE, MIRADO, CHUVA, semente=semente)
        nomes = []
        for _ in range(600):
            _, comecos = r.atualizar((0.0, 0.0), (0.0, 0.0))
            if "aviso" in comecos:
                nomes.append(r.atual.nome)
        return nomes

    assert sequencia(7) == sequencia(7)


# --- peças ---------------------------------------------------------------------------


def test_leque_abre_tres_tiros_com_a_mesma_velocidade():
    r = roteiro(LEQUE)
    (disparo,) = passos(r, LEQUE.aviso + 1)[-1:]
    assert len(disparo.projeteis) == 3
    for tiro in disparo.projeteis:
        assert math.isclose(math.hypot(tiro.vx, tiro.vy), LEQUE.velocidade, rel_tol=1e-4)


def test_tiro_mirado_vai_na_direcao_da_dara():
    r = roteiro(MIRADO)
    (disparo,) = passos(r, MIRADO.aviso + 1, alvo=(300.0, 400.0))[-1:]
    (tiro,) = disparo.projeteis
    assert math.isclose(tiro.vx, 6.0) and math.isclose(tiro.vy, 8.0)  # (3, 4)/5 × 10


def test_chuva_cai_onde_o_aviso_mostrou():
    r = roteiro(CHUVA)
    passos(r, 1)
    pontos = r.pontos_da_chuva
    assert len(pontos) == 4 and all(100 <= x <= 1100 for x in pontos)
    (disparo,) = passos(r, CHUVA.aviso)[-1:]
    assert tuple(t.x for t in disparo.projeteis) == pontos
    assert all(t.vy > 0 and t.vx == 0 for t in disparo.projeteis)
    assert all(t.material is Material.METAL for t in disparo.projeteis)


def test_material_comum_nao_tem_material():
    r = roteiro(RAJADA)
    (disparo,) = passos(r, RAJADA.aviso + 1)[-1:]
    assert disparo.projeteis[0].material is None


def test_inimigos_nascem_e_voam_ate_a_dara():
    r = roteiro(INIMIGOS)
    (disparo,) = passos(r, INIMIGOS.aviso + 1)[-1:]
    assert [i.nome for i in disparo.inimigos] == ["inimigo-1", "inimigo-2"]
    inimigo = disparo.inimigos[0]
    inimigo.atualizar((1000.0, 400.0))  # 100 px abaixo
    assert (inimigo.x, inimigo.y) == (1000.0, 303.0)


def test_inimigo_cai_com_dano():
    inimigo = Inimigo("i", 0, 0, 30, 3, 2.0)
    inimigo.levar_dano(2)
    assert inimigo.vulneravel
    inimigo.levar_dano(5)
    assert inimigo.vida == 0 and not inimigo.vulneravel


# --- integração com o chefe e a batalha ----------------------------------------------

ARENA = replace(carregar_arena(), alvo=None, lancador=None)


def chefe_com(*ataques, vida=300):
    fases = (
        DadosFase("um", 100, 100, 100, ((1100, 400),), 0.0, tuple(ataques)),
        DadosFase("dois", 50, 100, 100, ((1100, 400),), 0.0, (LEQUE,)),
    )
    return DadosChefe("Teste", vida, 40, False, fases)


def test_chefe_nao_ataca_na_transicao_e_troca_de_lista():
    chefe = Chefe(chefe_com(RAJADA), random.Random(1))
    for _ in range(RAJADA.aviso + 1):
        chefe.atualizar((200.0, 575.0))
    assert chefe.novos_projeteis
    chefe.levar_dano(200)
    for _ in range(39):
        assert chefe.atualizar((200.0, 575.0)) is not None
        assert chefe.novos_projeteis == []
    eventos = chefe.atualizar((200.0, 575.0))
    assert EventoChefe.TERMINOU_TRANSICAO in eventos and EventoChefe.ATAQUE_AVISO in eventos
    assert chefe.roteiro.atual is LEQUE


def test_rajada_do_chefe_acerta_a_dara():
    rajada = replace(RAJADA, origem=(1200.0, 580.0), velocidade=12.0)
    batalha = Batalha(1, ARENA, chefe_com(rajada))
    eventos = []
    for _ in range(200):
        eventos.extend(batalha.atualizar(NENHUM))
    assert EventoChefe.ATAQUE_AVISO in eventos and EventoJogador.LEVOU_DANO in eventos


def test_zona_machuca_a_dara_no_chao():
    batalha = Batalha(1, ARENA, chefe_com(ZONA))
    eventos = []
    for _ in range(ZONA.aviso):
        eventos.extend(batalha.atualizar(NENHUM))
    assert EventoJogador.LEVOU_DANO not in eventos  # só o aviso
    for _ in range(5):
        eventos.extend(batalha.atualizar(NENHUM))
    assert EventoJogador.LEVOU_DANO in eventos


def test_inimigos_caem_com_tiros_e_enchem_o_medidor():
    batalha = Batalha(1, ARENA, chefe_com(replace(INIMIGOS, origem=(700.0, 575.0))))
    eventos = []
    for _ in range(INIMIGOS.aviso + 60):
        eventos.extend(batalha.atualizar(frozenset({Botao.TIRO})))
    assert EventoBatalha.INIMIGO_DESTRUIDO in eventos
    assert batalha.jogador.medidor.pontos > 0


def test_inimigo_que_encosta_machuca_e_some():
    batalha = Batalha(1, ARENA, chefe_com(replace(INIMIGOS, origem=(300.0, 575.0))))
    eventos = []
    for _ in range(INIMIGOS.aviso + 60):
        eventos.extend(batalha.atualizar(NENHUM))
    assert EventoJogador.LEVOU_DANO in eventos and EventoBatalha.INIMIGO_DESTRUIDO in eventos
