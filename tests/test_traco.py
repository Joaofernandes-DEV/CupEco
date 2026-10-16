from ferramentas.arte.efeitos import grao
from ferramentas.arte.personagens import dara
from ferramentas.arte.traco import Pincel, Tela, bezier, curva, direcao, girar


def test_bezier_comeca_e_termina_nos_pontos_extremos():
    pontos = bezier((0, 0), (10, 30), (20, 30), (30, 0), passos=8)
    assert pontos[0] == (0, 0)
    assert pontos[-1] == (30, 0)
    assert len(pontos) == 9


def test_curva_passa_por_todas_as_ancoras():
    ancoras = [(0, 0), (20, -10), (40, 5), (60, 0)]
    pontos = curva(ancoras, passos=6)
    for ancora in ancoras:
        assert any(abs(x - ancora[0]) < 1e-9 and abs(y - ancora[1]) < 1e-9 for x, y in pontos)


def test_curva_fechada_nao_repete_o_primeiro_ponto():
    pontos = curva([(0, 0), (10, 0), (10, 10), (0, 10)], fechada=True, passos=4)
    assert pontos[0] != pontos[-1]
    assert len(pontos) == 16


def test_girar_aponta_o_desenho_para_o_eixo():
    assert girar([(10, 0)], (0.0, 1.0)) == [(0.0, 10.0)]
    assert girar([(10, 0)], (1.0, 0.0), origem=(5, 5)) == [(15.0, 5.0)]


def test_direcao_e_unitaria():
    dx, dy = direcao((0, 0), (3, 4))
    assert (dx, dy) == (0.6, 0.8)
    assert direcao((1, 1), (1, 1)) == (1.0, 0.0)


def _desenhar_dara(semente: int, tremor: float) -> bytes:
    tela = Tela(160, 240, escala=2)
    dara.desenhar_dara(Pincel(tela, origem=(70, 230), tremor=tremor, semente=semente), dara.PARADA)
    return tela.reduzir().tobytes()


def test_mesma_semente_gera_a_mesma_imagem():
    assert _desenhar_dara(3, 0.6) == _desenhar_dara(3, 0.6)


def test_linha_viva_muda_com_a_semente():
    assert _desenhar_dara(3, 0.6) != _desenhar_dara(4, 0.6)


def test_sem_tremor_a_semente_nao_importa():
    assert _desenhar_dara(3, 0.0) == _desenhar_dara(4, 0.0)


def test_grao_e_deterministico():
    assert grao(300, 300, 5).tobytes() == grao(300, 300, 5).tobytes()
    assert grao(300, 300, 5).tobytes() != grao(300, 300, 6).tobytes()
