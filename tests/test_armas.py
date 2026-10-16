import math
from dataclasses import replace

import pytest

from cupeco.dominio.armas import (
    Arsenal,
    boca_do_canhao,
    carregar_armas,
    disparar,
    disparar_ex,
    validar_arma,
)
from cupeco.dominio.dados import DadosInvalidos
from cupeco.dominio.fisica import Caixa
from cupeco.dominio.materiais import Material
from cupeco.dominio.projeteis import VETORES, Dono, Projetil, tamanho_orientado

ARMAS = carregar_armas()
PLASTICO = ARMAS[Material.PLASTICO]
PAPEL = ARMAS[Material.PAPEL]


# --- projéteis -----------------------------------------------------------------------


def test_vetores_das_oito_direcoes_sao_unitarios():
    assert len(VETORES) == 8
    for (h, v), (dx, dy) in VETORES.items():
        assert math.isclose(dx * dx + dy * dy, 1.0)
        assert (dx > 0) - (dx < 0) == h and (dy > 0) - (dy < 0) == v


def test_tamanho_do_projetil_acompanha_a_direcao():
    assert tamanho_orientado(26, 14, 1, 0) == (26, 14)
    assert tamanho_orientado(26, 14, 0, -1) == (14, 26)
    assert tamanho_orientado(26, 14, 0.7, 0.7) == (20, 20)


def test_projetil_anda_em_linha_reta_e_some():
    tiro = Projetil(100, 100, 10, 10, vx=5, vy=-2, dano=1, quadros_de_vida=3, dono=Dono.JOGADOR)
    for _ in range(3):
        assert tiro.vivo
        tiro.atualizar()
    assert (tiro.x, tiro.y) == (115, 94)
    assert not tiro.vivo


def test_projetil_fora_da_area():
    area = Caixa(0, 0, 1280, 720)
    assert not Projetil(1270, 50, 30, 10, 0, 0, 1, 1, Dono.JOGADOR).fora_da_area(area)
    assert Projetil(1300, 50, 30, 10, 0, 0, 1, 1, Dono.JOGADOR).fora_da_area(area)


# --- armas em dados ------------------------------------------------------------------


def test_armas_da_v1_sao_plastico_e_papel():
    assert set(ARMAS) == {Material.PLASTICO, Material.PAPEL}
    assert PLASTICO.nome == "Rajada de Plástico" and PAPEL.nome == "Leque de Papel"
    assert len(PLASTICO.espalhamento) == 1 and len(PAPEL.espalhamento) == 3
    assert PLASTICO.ex.perfura and not PAPEL.ex.perfura


@pytest.mark.parametrize(
    ("alteracao", "mensagem"),
    [
        ({"material": Material.REJEITO}, "material reciclável"),
        ({"dano": 0}, "dano: precisa ser positivo"),
        ({"espalhamento": ()}, "pelo menos um tiro"),
        ({"espalhamento": ((1.0, 0.5),)}, r"espalhamento\[0\]"),
    ],
)
def test_arma_invalida(alteracao, mensagem):
    with pytest.raises(DadosInvalidos, match=mensagem):
        validar_arma(replace(PLASTICO, **alteracao), "armas.teste")


def test_ex_invalido():
    with pytest.raises(DadosInvalidos, match="ex.dano"):
        validar_arma(replace(PLASTICO, ex=replace(PLASTICO.ex, dano=0)), "armas.teste")


# --- disparos ------------------------------------------------------------------------


def test_rajada_de_plastico_sai_reta_na_cor_da_arma():
    (tiro,) = disparar(PLASTICO, (200, 300), (1, 0))
    assert (tiro.vx, tiro.vy) == (PLASTICO.velocidade, 0)
    assert tiro.material is Material.PLASTICO and tiro.dono is Dono.JOGADOR
    assert (tiro.x, tiro.y) == (200, 300)


def test_leque_de_papel_abre_simetrico():
    tiros = disparar(PAPEL, (0, 0), (1, 0))
    assert len(tiros) == 3
    vys = sorted(round(t.vy, 6) for t in tiros)
    assert vys[0] == -vys[2] and vys[1] == 0
    for tiro in tiros:
        assert math.isclose(math.hypot(tiro.vx, tiro.vy), PAPEL.velocidade, rel_tol=1e-4)


def test_tiro_na_diagonal_tem_a_mesma_velocidade():
    (tiro,) = disparar(PLASTICO, (0, 0), (-1, -1))
    assert tiro.vx < 0 and tiro.vy < 0
    assert math.isclose(math.hypot(tiro.vx, tiro.vy), PLASTICO.velocidade)


def test_tiro_ex():
    tiro = disparar_ex(PLASTICO, (0, 0), (0, -1))
    assert tiro.ex and tiro.perfura and tiro.dano == PLASTICO.ex.dano
    assert (tiro.vx, tiro.vy) == (0, -PLASTICO.ex.velocidade)
    assert (tiro.largura, tiro.altura) == (PLASTICO.ex.altura, PLASTICO.ex.largura)


def test_boca_do_canhao_fica_na_direcao_da_mira():
    caixa = Caixa(100, 100, 50, 100)  # centro (125, 150)
    assert boca_do_canhao(caixa, (1, 0), 40) == (165, 150)
    assert boca_do_canhao(caixa, (0, -1), 40) == (125, 110)


# --- arsenal -------------------------------------------------------------------------


def test_cadencia_da_rajada():
    arsenal = Arsenal.padrao()
    tiros = [len(arsenal.atualizar(True, (0, 0), (1, 0))) for _ in range(24)]
    assert sum(tiros) == 24 // PLASTICO.quadros_entre_tiros
    assert tiros[0] == 1 and tiros[PLASTICO.quadros_entre_tiros] == 1


def test_sem_segurar_o_tiro_nao_dispara():
    arsenal = Arsenal.padrao()
    assert all(arsenal.atualizar(False, (0, 0), (1, 0)) == [] for _ in range(20))


def test_trocar_alterna_as_armas():
    arsenal = Arsenal.padrao()
    assert arsenal.ativa is PLASTICO
    arsenal.trocar()
    assert arsenal.ativa is PAPEL
    arsenal.trocar()
    assert arsenal.ativa is PLASTICO


def test_arsenal_vazio_nao_existe():
    with pytest.raises(ValueError):
        Arsenal(())
