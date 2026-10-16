"""A Dara em combate: Triagem, dano, vida, Medidor, EX e Super (J3, J4, J5, D12, D14)."""

import pytest

from cupeco.dominio.comandos import NENHUM, Botao
from cupeco.dominio.fisica import Caixa, Plataforma
from cupeco.dominio.jogador import (
    Estado,
    EventoJogador,
    Jogador,
    carregar_parametros_jogador,
)
from cupeco.dominio.materiais import Material
from cupeco.dominio.projeteis import Dono, Projetil
from cupeco.dominio.triagem import carregar_regras_triagem

P = carregar_parametros_jogador()
R = carregar_regras_triagem()
CHAO = Plataforma(Caixa(-1000, 600, 4000, 120))
PULO, EX, DASH, TIRO = Botao.PULO, Botao.EX, Botao.DASH, Botao.TIRO


def segurar(*botoes):
    return frozenset(botoes)


def rodar(jogador, comandos, passos):
    eventos = []
    for _ in range(passos):
        eventos.extend(jogador.atualizar(comandos, [CHAO]))
    return eventos


def no_chao():
    jogador = Jogador(100, 600)
    rodar(jogador, NENHUM, 1)
    return jogador


def residuo(material=None):
    return Projetil(0, 0, 20, 20, 0, 0, 1, 60, Dono.INIMIGO, material=material)


def em_triagem():
    """Pula, solta e aperta o pulo de novo no ar: a janela da Triagem fica aberta."""
    jogador = no_chao()
    rodar(jogador, segurar(PULO), 1)
    rodar(jogador, NENHUM, 1)
    eventos = rodar(jogador, segurar(PULO), 1)
    assert EventoJogador.TENTOU_TRIAGEM in eventos
    assert jogador.estado is Estado.TRIAGEM and jogador.em_triagem
    return jogador


# --- Triagem (J3, D12) ---------------------------------------------------------------


def test_separar_residuo_da_cor_da_arma_rende_um_fardo_e_quica():
    jogador = em_triagem()
    assert jogador.arsenal.ativa.material is Material.PLASTICO
    toque = jogador.tocar(residuo(Material.PLASTICO))
    assert toque.remover_projetil
    assert toque.eventos == (EventoJogador.TRIAGEM_CERTA,)
    assert jogador.medidor.pontos == R.pontos_triagem_certa
    assert jogador.corpo.vy == -P.velocidade_quique
    assert jogador.vida == P.vida_maxima
    assert jogador.estatisticas.triagens_certas == 1


def test_separar_residuo_de_outra_cor_rende_meio_fardo():
    jogador = em_triagem()
    toque = jogador.tocar(residuo(Material.VIDRO))
    assert toque.remover_projetil and toque.eventos == (EventoJogador.TRIAGEM_OUTRA_COR,)
    assert jogador.medidor.pontos == R.pontos_triagem_outra_cor
    assert jogador.estatisticas.triagens_outra_cor == 1


@pytest.mark.parametrize("material", [Material.REJEITO, Material.PERIGOSO])
def test_tentar_separar_rejeito_ou_perigoso_machuca(material):
    jogador = em_triagem()
    toque = jogador.tocar(residuo(material))
    assert not toque.remover_projetil
    assert toque.eventos[:2] == (EventoJogador.TRIAGEM_PROIBIDA, EventoJogador.LEVOU_DANO)
    assert jogador.vida == P.vida_maxima - 1
    assert jogador.medidor.pontos == 0
    assert jogador.estatisticas.triagens_proibidas == 1


def test_trocar_de_arma_muda_qual_cor_e_a_certa():
    jogador = no_chao()
    rodar(jogador, segurar(Botao.TROCAR), 1)
    rodar(jogador, segurar(PULO), 1)
    rodar(jogador, NENHUM, 1)
    rodar(jogador, segurar(PULO), 1)
    toque = jogador.tocar(residuo(Material.PAPEL))
    assert toque.eventos == (EventoJogador.TRIAGEM_CERTA,)


def test_fora_da_janela_o_residuo_machuca():
    jogador = no_chao()
    toque = jogador.tocar(residuo(Material.PLASTICO))
    assert not toque.remover_projetil
    assert EventoJogador.LEVOU_DANO in toque.eventos


def test_janela_da_triagem_fecha_sozinha():
    jogador = em_triagem()
    rodar(jogador, NENHUM, P.quadros_janela_triagem)
    assert not jogador.em_triagem
    assert EventoJogador.LEVOU_DANO in jogador.tocar(residuo(Material.PLASTICO)).eventos


def test_uma_tentativa_por_pulo_e_o_acerto_devolve_a_tentativa():
    jogador = em_triagem()
    rodar(jogador, NENHUM, P.quadros_janela_triagem)
    eventos = rodar(jogador, segurar(PULO), 1)
    assert EventoJogador.TENTOU_TRIAGEM not in eventos

    jogador = em_triagem()
    jogador.tocar(residuo(Material.PLASTICO))
    rodar(jogador, NENHUM, 1)
    assert EventoJogador.TENTOU_TRIAGEM in rodar(jogador, segurar(PULO), 1)


def test_acertar_a_triagem_devolve_o_dash_aereo():
    # Bem alta no ar (o chão fica a 2600 px), para nenhum pouso devolver o dash no meio.
    jogador = Jogador(100, -2000)
    assert EventoJogador.DASH in rodar(jogador, segurar(DASH), 1)
    rodar(jogador, NENHUM, P.quadros_dash + P.quadros_espera_dash)
    assert EventoJogador.DASH not in rodar(jogador, segurar(DASH), 1)  # o dash aéreo já foi
    rodar(jogador, NENHUM, 1)
    assert EventoJogador.TENTOU_TRIAGEM in rodar(jogador, segurar(PULO), 1)
    jogador.tocar(residuo(Material.PLASTICO))
    rodar(jogador, NENHUM, 1)
    assert not jogador.corpo.no_chao
    assert EventoJogador.DASH in rodar(jogador, segurar(DASH), 1)


def test_no_chao_apertar_pulo_pula_em_vez_de_tentar_triagem():
    jogador = no_chao()
    eventos = rodar(jogador, segurar(PULO), 1)
    assert EventoJogador.PULOU in eventos and EventoJogador.TENTOU_TRIAGEM not in eventos


# --- dano e vida (J5, D14) ------------------------------------------------------------


def test_dano_tira_vida_empurra_e_deixa_invencivel():
    jogador = no_chao()
    toque = jogador.tocar(residuo())
    assert toque.eventos == (EventoJogador.LEVOU_DANO,)
    assert jogador.vida == P.vida_maxima - 1
    assert jogador.estado is Estado.DANO and jogador.invencivel
    assert jogador.corpo.vy < 0 and jogador.corpo.vx < 0  # para cima e para trás
    assert jogador.tocar(residuo()).eventos == ()  # invencível: o segundo não pega
    assert jogador.vida == P.vida_maxima - 1


def test_atordoada_ignora_os_comandos():
    jogador = no_chao()
    jogador.tocar(residuo())
    eventos = rodar(jogador, segurar(PULO, TIRO, DASH), P.quadros_atordoada - 1)
    assert not {EventoJogador.PULOU, EventoJogador.TIROU, EventoJogador.DASH} & set(eventos)
    assert jogador.estado is Estado.DANO


def test_invencibilidade_acaba():
    jogador = no_chao()
    jogador.tocar(residuo())
    rodar(jogador, NENHUM, P.quadros_invencivel)
    assert not jogador.invencivel
    assert EventoJogador.LEVOU_DANO in jogador.tocar(residuo()).eventos


def test_dash_nao_protege():
    jogador = no_chao()
    rodar(jogador, segurar(DASH), 3)
    assert jogador.estado is Estado.DASH
    assert EventoJogador.LEVOU_DANO in jogador.tocar(residuo()).eventos


def test_contato_com_perigo_tambem_machuca():
    jogador = no_chao()
    assert jogador.tocar_perigo() == (EventoJogador.LEVOU_DANO,)
    assert jogador.tocar_perigo() == ()


def test_sem_vida_a_dara_e_derrotada():
    jogador = no_chao()
    for _ in range(P.vida_maxima - 1):
        jogador.tocar(residuo())
        rodar(jogador, NENHUM, P.quadros_invencivel)
    toque = jogador.tocar(residuo())
    assert toque.eventos == (EventoJogador.LEVOU_DANO, EventoJogador.DERROTADA)
    assert jogador.derrotada and jogador.vida == 0
    eventos = rodar(jogador, segurar(PULO, TIRO), 30)
    assert EventoJogador.PULOU not in eventos and EventoJogador.TIROU not in eventos
    assert jogador.estado is Estado.DERROTADA and jogador.corpo.no_chao
    assert jogador.estatisticas.danos_recebidos == P.vida_maxima


def test_projetil_da_propria_dara_nao_toca():
    jogador = no_chao()
    with pytest.raises(ValueError):
        jogador.tocar(Projetil(0, 0, 10, 10, 0, 0, 1, 10, Dono.JOGADOR))


# --- Medidor, EX e Super (J4) --------------------------------------------------------


def test_acertar_tiros_normais_enche_o_medidor():
    jogador = no_chao()
    tiro = Projetil(0, 0, 10, 10, 0, 0, 4, 10, Dono.JOGADOR)
    jogador.acertou(tiro)
    assert jogador.medidor.pontos == 4 * R.pontos_por_dano
    tiro_ex = Projetil(0, 0, 10, 10, 0, 0, 30, 10, Dono.JOGADOR, ex=True)
    jogador.acertou(tiro_ex)
    assert jogador.medidor.pontos == 4 * R.pontos_por_dano  # o EX não enche


def test_ex_sem_fardo_nao_sai():
    jogador = no_chao()
    assert EventoJogador.EX not in rodar(jogador, segurar(EX), 1)
    assert jogador.novos_projeteis == []


def test_ex_gasta_um_fardo_e_dispara():
    jogador = no_chao()
    jogador.medidor.ganhar(150)
    eventos = rodar(jogador, segurar(EX), 1)
    assert EventoJogador.EX in eventos
    (tiro,) = jogador.novos_projeteis
    assert tiro.ex and tiro.dano == jogador.arsenal.ativa.ex.dano
    assert jogador.medidor.pontos == 50
    assert jogador.estatisticas.exs == 1


def test_medidor_cheio_solta_o_super():
    jogador = no_chao()
    jogador.medidor.ganhar(500)
    eventos = rodar(jogador, segurar(EX), 1)
    assert EventoJogador.SUPER in eventos and EventoJogador.EX not in eventos
    assert jogador.medidor.pontos == 0
    rodar(jogador, segurar(Botao.DIREITA, TIRO), 1)
    assert jogador.estado is Estado.SUPER and jogador.invencivel
    x = jogador.corpo.x
    rodar(jogador, segurar(Botao.DIREITA, TIRO), R.quadros_super - 3)
    assert jogador.corpo.x == x and jogador.novos_projeteis == []
    rodar(jogador, NENHUM, 3)
    assert jogador.estado is not Estado.SUPER and not jogador.invencivel
    assert jogador.estatisticas.supers == 1


def test_invencibilidade_mais_curta_que_o_atordoamento_e_invalida():
    from dataclasses import replace

    from cupeco.dominio.dados import DadosInvalidos
    from cupeco.dominio.jogador import validar_parametros

    with pytest.raises(DadosInvalidos, match="durar mais que o atordoamento"):
        validar_parametros(replace(P, quadros_invencivel=P.quadros_atordoada))
