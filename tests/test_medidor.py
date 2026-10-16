import pytest

from cupeco.dominio.medidor import FARDOS, PONTOS_MAXIMOS, PONTOS_POR_FARDO, Medidor


def test_medidor_tem_cinco_fardos_de_cem_pontos():
    assert (FARDOS, PONTOS_POR_FARDO, PONTOS_MAXIMOS) == (5, 100, 500)


def test_ganha_e_conta_fardos_completos():
    medidor = Medidor()
    medidor.ganhar(250)
    assert medidor.pontos == 250 and medidor.fardos == 2
    assert medidor.pode_ex and not medidor.cheio


def test_nao_passa_do_maximo():
    medidor = Medidor(480)
    medidor.ganhar(100)
    assert medidor.pontos == PONTOS_MAXIMOS and medidor.cheio


def test_ex_gasta_um_fardo():
    medidor = Medidor(150)
    assert medidor.gastar_ex()
    assert medidor.pontos == 50
    assert not medidor.gastar_ex()
    assert medidor.pontos == 50


def test_super_exige_e_gasta_o_medidor_cheio():
    medidor = Medidor(499)
    assert not medidor.gastar_super()
    medidor.ganhar(1)
    assert medidor.gastar_super()
    assert medidor.pontos == 0


def test_ganho_negativo_e_erro():
    with pytest.raises(ValueError):
        Medidor().ganhar(-10)
