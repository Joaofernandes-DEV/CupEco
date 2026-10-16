"""O Dom Obsolescêncio, o primeiro chefe (J8), nos dois modos."""

import random

import pytest

from cupeco.dominio.ataques import TipoAtaque
from cupeco.dominio.batalha import Batalha, EventoBatalha, Replay, Resultado, carregar_arena
from cupeco.dominio.chefe import Chefe, EventoChefe, carregar_chefe
from cupeco.dominio.comandos import Botao
from cupeco.dominio.materiais import Material, Tipo
from cupeco.dominio.modos import Modo, aplicar_modo

DOM = carregar_chefe("dom_obsolescencio")
ARENA = carregar_arena("dom")


def ataques(fase):
    return {ataque.nome: ataque for ataque in DOM.fases[fase].ataques}


def test_o_dom_tem_as_3_fases_do_briefing():
    assert DOM.nome == "Dom Obsolescêncio"
    assert [f.nome for f in DOM.fases] == ["Torre de Tubos", "Enxame Descontinuado", "Placa-Mãe"]
    assert [f.comeca_em for f in DOM.fases] == [100, 66, 33]
    assert set(ataques(0)) == {"Raios de Pixel", "Chicote de Cabo", "Coroa de Antenas"}
    assert set(ataques(1)) == {"Celulares", "Baterias Estufadas", "Manuais de Papel"}
    assert set(ataques(2)) == {
        "Trilhas da Esquerda",
        "Trilhas da Direita",
        "Faíscas",
        "Atualização Obrigatória",
    }


def test_vida_nos_dois_modos():
    assert DOM.vida == 2000
    assert aplicar_modo(DOM, Modo.SIMPLES).vida == 1400
    assert len(aplicar_modo(DOM, Modo.SIMPLES).fases) == 3


def test_arena_do_dom_nao_tem_boneco_nem_lancador():
    assert ARENA.alvo is None and ARENA.lancador is None
    assert sum(p.atravessavel for p in ARENA.plataformas) == 2  # as tábuas


def test_materiais_dos_ataques_ensinam_a_triagem():
    coroa = ataques(0)["Coroa de Antenas"]
    assert coroa.materiais == ("metal",)  # amarelo, separável
    assert Material.METAL.tipo is Tipo.RECICLAVEL
    baterias = ataques(1)["Baterias Estufadas"]
    assert baterias.materiais == ("perigoso",)  # laranja, não se separa
    assert Material.PERIGOSO.tipo is Tipo.PERIGOSO
    assert baterias.explosao is not None and baterias.explode_em == 640.0
    assert ataques(1)["Manuais de Papel"].materiais == ("papel",)
    assert ataques(1)["Celulares"].tipo is TipoAtaque.INIMIGOS  # destrutíveis (D34)


def test_atualizacao_obrigatoria_cura_10_por_cento():
    barra = ataques(2)["Atualização Obrigatória"]
    assert barra.tipo is TipoAtaque.BARRA and barra.cura == 10


@pytest.mark.parametrize("modo", list(Modo))
def test_cada_fase_usa_todos_os_seus_ataques_ate_a_derrota(modo):
    chefe = Chefe(aplicar_modo(DOM, modo), random.Random(3))
    usados = [set(), set(), set()]
    while not chefe.derrotado:
        fase = chefe.fase
        for _ in range(3000):
            chefe.atualizar((300.0, 575.0))
            if chefe.roteiro.atual is not None:
                usados[fase].add(chefe.roteiro.atual.nome)
        chefe.levar_dano(chefe.vida)  # para no limite da fase seguinte
        while chefe.em_transicao:
            chefe.atualizar()
    assert usados == [set(ataques(i)) for i in range(3)]


@pytest.mark.parametrize("modo", list(Modo))
def test_luta_inteira_do_comeco_ao_fim(modo):
    """A Dara atira sem parar; o chefe leva um empurrão de dano a cada 900 quadros."""
    batalha = Batalha(11, ARENA, DOM, modo)
    batalha.jogador.vida = 1_000_000  # só para a luta chegar ao fim neste teste
    eventos, fases = set(), set()
    for quadro in range(20_000):
        eventos.update(batalha.atualizar(frozenset({Botao.TIRO})))
        fases.add(batalha.chefe.fase)
        if quadro % 900 == 899:
            batalha.chefe.levar_dano(batalha.chefe.dados.vida // 3)
        if batalha.resultado is not None:
            break
    assert batalha.resultado is Resultado.VITORIA
    assert fases == {0, 1, 2}
    esperados = {
        EventoBatalha.ACERTOU_ALVO,
        EventoBatalha.EXPLODIU,
        EventoBatalha.INIMIGO_DESTRUIDO,
    }
    assert esperados <= eventos and EventoChefe.ATAQUE_AVISO in eventos


@pytest.mark.parametrize("modo", list(Modo))
def test_replay_da_luta_contra_o_dom(modo):
    sorteio = random.Random(modo.value)
    botoes = list(Botao)
    comandos = [frozenset(b for b in botoes if sorteio.random() < 0.25) for _ in range(900)]
    original = Batalha(5, ARENA, DOM, modo)
    eventos = [original.atualizar(passo) for passo in comandos]
    replay = Replay.da_batalha(original, arena="dom", chefe="dom_obsolescencio")
    reproduzida, eventos_reproduzidos = Replay.de_json(replay.para_json()).reproduzir()
    assert reproduzida.modo is modo
    assert reproduzida.retrato() == original.retrato()
    assert eventos_reproduzidos == eventos
