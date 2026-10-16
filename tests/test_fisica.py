import pytest

from cupeco.dominio.fisica import Caixa, Corpo, Plataforma, apoios, mover

GRAVIDADE = 1.0
QUEDA_MAXIMA = 15.0

CHAO = Plataforma(Caixa(0, 600, 1280, 120))
PAREDE = Plataforma(Caixa(800, 0, 40, 600))
TETO = Plataforma(Caixa(0, 300, 1280, 20))
TABUA = Plataforma(Caixa(400, 450, 200, 16), atravessavel=True)


def passos(corpo, plataformas, quantidade, **opcoes):
    contatos = None
    for _ in range(quantidade):
        contatos = mover(corpo, plataformas, GRAVIDADE, QUEDA_MAXIMA, **opcoes)
    return contatos


# --- caixas --------------------------------------------------------------------------


def test_caixas_que_so_encostam_nao_se_sobrepoem():
    a = Caixa(0, 0, 10, 10)
    assert not a.sobrepoe(Caixa(10, 0, 10, 10))
    assert not a.sobrepoe(Caixa(0, 10, 10, 10))
    assert a.sobrepoe(Caixa(9.5, 9.5, 10, 10))


def test_bordas_e_centro_da_caixa():
    caixa = Caixa(10, 20, 30, 40)
    assert (caixa.esquerda, caixa.direita, caixa.topo, caixa.base) == (10, 40, 20, 60)
    assert caixa.centro == (25, 40)
    assert caixa.deslocada(5, -5) == Caixa(15, 15, 30, 40)


# --- gravidade e chão ----------------------------------------------------------------


def test_queda_livre_acelera_ate_a_queda_maxima():
    corpo = Corpo(100, 0, 40, 80)
    passos(corpo, [], 3)
    assert corpo.vy == 3
    passos(corpo, [], 30)
    assert corpo.vy == QUEDA_MAXIMA


def test_pousa_exatamente_no_topo_do_chao():
    corpo = Corpo(100, 400, 40, 80)
    contatos = passos(corpo, [CHAO], 40)
    assert corpo.y + corpo.altura == 600
    assert corpo.vy == 0
    assert corpo.no_chao and contatos.chao


def test_parado_no_chao_continua_no_chao():
    corpo = Corpo(100, 520, 40, 80)
    for _ in range(10):
        contatos = mover(corpo, [CHAO], GRAVIDADE, QUEDA_MAXIMA)
        assert contatos.chao
        assert corpo.y == 520


def test_queda_rapida_nao_atravessa_chao_fino():
    fino = Plataforma(Caixa(0, 600, 1280, 2))
    corpo = Corpo(100, 590 - 80, 40, 80, vy=QUEDA_MAXIMA)
    passos(corpo, [fino], 1)
    assert corpo.y + corpo.altura == 600


def test_sai_da_borda_e_cai():
    beirada = Plataforma(Caixa(0, 600, 200, 120))
    corpo = Corpo(150, 520, 40, 80)
    passos(corpo, [beirada], 1)
    assert corpo.no_chao
    # Enquanto qualquer parte da caixa estiver sobre a beirada, o corpo continua apoiado.
    corpo.vx = 10
    contatos = passos(corpo, [beirada], 4)
    assert corpo.x == 190 and contatos.chao
    contatos = passos(corpo, [beirada], 2)
    assert corpo.x >= 200
    assert not corpo.no_chao and not contatos.chao
    assert corpo.y > 520


def test_pousa_na_primeira_plataforma_do_caminho():
    alta = Plataforma(Caixa(0, 500, 300, 20))
    corpo = Corpo(100, 380, 40, 80, vy=QUEDA_MAXIMA)
    passos(corpo, [CHAO, alta], 20)
    assert corpo.y + corpo.altura == 500


# --- paredes e teto ------------------------------------------------------------------


def test_parede_bloqueia_pela_direita():
    corpo = Corpo(700, 520, 40, 80)
    for _ in range(20):
        corpo.vx = 9
        contatos = mover(corpo, [CHAO, PAREDE], GRAVIDADE, QUEDA_MAXIMA)
    assert corpo.x + corpo.largura == 800
    assert contatos.parede_direita and not contatos.parede_esquerda
    assert corpo.no_chao


def test_parede_bloqueia_pela_esquerda():
    corpo = Corpo(900, 520, 40, 80)
    for _ in range(20):
        corpo.vx = -9
        contatos = mover(corpo, [CHAO, PAREDE], GRAVIDADE, QUEDA_MAXIMA)
    assert corpo.x == 840
    assert contatos.parede_esquerda


def test_chao_nao_conta_como_parede():
    corpo = Corpo(100, 520, 40, 80)
    for _ in range(5):
        corpo.vx = 8
        contatos = mover(corpo, [CHAO], GRAVIDADE, QUEDA_MAXIMA)
    assert corpo.x == 140
    assert not contatos.parede_direita


def test_bate_a_cabeca_no_teto():
    # Com a gravidade, a velocidade vira -29: o topo passaria de 340 para 311, além do teto.
    corpo = Corpo(100, 340, 40, 80, vy=-30)
    contatos = passos(corpo, [TETO, CHAO], 1)
    assert contatos.teto
    assert corpo.y == 320
    assert corpo.vy == 0


# --- plataforma atravessável ---------------------------------------------------------


def test_sobe_atravessando_a_tabua_por_baixo():
    corpo = Corpo(450, 470, 40, 80, vy=-18)
    contatos = passos(corpo, [TABUA], 1)
    assert not contatos.teto
    assert corpo.y < 470


def test_cai_sobre_a_tabua_e_fica_em_pe():
    corpo = Corpo(450, 300, 40, 80)
    passos(corpo, [TABUA, CHAO], 30)
    assert corpo.y + corpo.altura == 450
    assert corpo.no_chao


def test_descer_atravessa_a_tabua():
    corpo = Corpo(450, 370, 40, 80)
    passos(corpo, [TABUA, CHAO], 1)
    assert corpo.no_chao
    passos(corpo, [TABUA, CHAO], 1, descer=True)
    passos(corpo, [TABUA, CHAO], 40)
    assert corpo.y + corpo.altura == 600


def test_corpo_ja_dentro_da_tabua_nao_e_puxado_para_cima():
    # Subindo pela tabua, o pulo perde força com a base ainda dentro dela: o corpo segue
    # caindo em vez de "teleportar" para o topo.
    corpo = Corpo(450, 380, 40, 80, vy=0)
    passos(corpo, [TABUA], 1)
    assert corpo.y == 381


def test_paredes_nao_contam_a_tabua():
    corpo = Corpo(350, 400, 40, 80)
    corpo.vx = 30
    contatos = mover(corpo, [TABUA], 0, QUEDA_MAXIMA)
    assert corpo.x == 380
    assert not contatos.parede_direita


@pytest.mark.parametrize("vx", [7.5, -7.5])
def test_mesmo_movimento_da_sempre_o_mesmo_resultado(vx):
    resultados = []
    for _ in range(2):
        corpo = Corpo(500, 100, 40, 80, vx=vx)
        for _ in range(120):
            mover(corpo, [CHAO, PAREDE, TABUA], GRAVIDADE, QUEDA_MAXIMA)
        resultados.append((corpo.x, corpo.y, corpo.vx, corpo.vy, corpo.no_chao))
    assert resultados[0] == resultados[1]


def test_apoios_sao_as_plataformas_sob_os_pes():
    em_pe = Caixa(450, 370, 40, 80)  # base em 450, o topo da tabua
    assert apoios(em_pe, [TABUA, CHAO]) == [TABUA]
    assert apoios(em_pe.deslocada(0, -1), [TABUA, CHAO]) == []
    assert apoios(Caixa(560, 370, 40, 80), [TABUA]) == [TABUA]  # metade do pé na tábua
    assert apoios(Caixa(600, 370, 40, 80), [TABUA]) == []  # só encosta na quina
