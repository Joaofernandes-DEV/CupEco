from cupeco.passo_fixo import PassoFixo


def test_um_segundo_em_quadros_irregulares_da_60_passos():
    relogio = PassoFixo()
    # Quadros reais de 16 e 17 ms, como os que o clock.tick(60) devolve: 1000 ms no total.
    quadros = [17, 17, 16] * 20
    assert sum(relogio.avancar(ms) for ms in quadros) == 60


def test_quadro_curto_acumula_ate_completar_um_passo():
    relogio = PassoFixo()
    assert relogio.avancar(16) == 0
    assert relogio.avancar(1) == 1


def test_quadro_muito_longo_e_limitado_e_descarta_o_atraso():
    relogio = PassoFixo(max_passos=5)
    assert relogio.avancar(1000) == 5
    # O atraso foi descartado: o quadro seguinte volta ao ritmo normal.
    assert relogio.avancar(17) == 1


def test_tempo_negativo_ou_zero_nao_avanca():
    relogio = PassoFixo()
    assert relogio.avancar(0) == 0
    assert relogio.avancar(-50) == 0
