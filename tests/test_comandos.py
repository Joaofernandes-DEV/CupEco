from cupeco.dominio.comandos import NENHUM, Botao, Controle


def test_apertou_vale_so_no_primeiro_passo():
    controle = Controle()
    controle.atualizar(frozenset({Botao.PULO}))
    assert controle.apertou(Botao.PULO) and controle.segurando(Botao.PULO)
    controle.atualizar(frozenset({Botao.PULO}))
    assert not controle.apertou(Botao.PULO) and controle.segurando(Botao.PULO)
    controle.atualizar(NENHUM)
    assert controle.soltou(Botao.PULO) and not controle.segurando(Botao.PULO)
    controle.atualizar(NENHUM)
    assert not controle.soltou(Botao.PULO)


def test_direcoes_opostas_se_anulam():
    controle = Controle()
    controle.atualizar(frozenset({Botao.ESQUERDA, Botao.DIREITA, Botao.CIMA}))
    assert controle.direcao == (0, -1)
    controle.atualizar(frozenset({Botao.ESQUERDA, Botao.BAIXO}))
    assert controle.direcao == (-1, 1)
    controle.atualizar(NENHUM)
    assert controle.direcao == (0, 0)
