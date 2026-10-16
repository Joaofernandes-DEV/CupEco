"""O "Você sabia?" (J15, D35, C1, C7).

Os fatos de exemplo daqui são fictícios ("Fato de teste"), sem nenhuma afirmação real: os
fatos do jogo vêm do João ou do grupo, com fonte (D35).
"""

import random
from dataclasses import replace

import pytest

from cupeco.dominio.chefe import listar_chefes
from cupeco.dominio.dados import DadosInvalidos, converter
from cupeco.dominio.fatos import (
    MAXIMO_DE_CARACTERES,
    Dica,
    Fato,
    Fonte,
    SorteioDeFatos,
    TabelaFatos,
    TipoFonte,
    carregar_fatos,
    contar_frases,
    validar_fatos,
)

FONTE = Fonte("Documento de teste", "Autor de teste", 2020, TipoFonte.ORGAO_OFICIAL, "2026-10-16")
DOM = "dom_obsolescencio"
FATOS = tuple(Fato(f"teste-{i}", DOM, f"Fato de teste {i}.", FONTE) for i in range(1, 4))
DICAS = (Dica("dica-a", "Dica de teste A."), Dica("dica-b", "Dica de teste B."))
TABELA = TabelaFatos(DICAS, FATOS)
CHEFES = (DOM,)


def sorteio(tabela=TABELA, semente=1):
    return SorteioDeFatos(tabela, random.Random(semente))


# --- os dados do jogo ----------------------------------------------------------------


def test_fatos_do_jogo_carregam_com_as_5_dicas():
    tabela = carregar_fatos()
    assert [d.id for d in tabela.dicas] == [
        "dica-avisos",
        "dica-lixeira-ativa",
        "dica-cinza-e-laranja",
        "dica-prensa",
        "dica-dash",
    ]


def test_todo_fato_do_jogo_tem_fonte_completa_e_texto_curto():
    """Vale sozinho para os fatos que o João ou o grupo enviarem (C1, C7, D35)."""
    tabela = carregar_fatos()
    for fato in tabela.fatos:
        assert fato.chefe in listar_chefes(), fato.id
        assert fato.fonte.titulo.strip() and fato.fonte.autor.strip(), fato.id
        assert isinstance(fato.fonte.tipo, TipoFonte), fato.id
        assert contar_frases(fato.texto) <= 2 and len(fato.texto) <= MAXIMO_DE_CARACTERES


def test_sem_fatos_sai_uma_dica_sem_fonte():
    tabela = carregar_fatos()
    s = SorteioDeFatos(replace(tabela, fatos=()), random.Random(1))
    for _ in range(12):
        mensagem = s.proxima(DOM)
        assert not mensagem.e_fato and mensagem.fonte is None
        assert mensagem.id in {d.id for d in tabela.dicas}
    assert s.vistos == {}


# --- sorteio (J15) -------------------------------------------------------------------


def test_nao_repete_ate_esgotar_os_fatos_do_chefe():
    s = sorteio()
    ids = [s.proxima(DOM).id for _ in range(30)]
    for rodada in range(10):
        assert sorted(ids[rodada * 3 : rodada * 3 + 3]) == ["teste-1", "teste-2", "teste-3"]
    assert all(a != b for a, b in zip(ids, ids[1:], strict=False))  # nunca dois iguais seguidos


@pytest.mark.parametrize("semente", range(20))
def test_rodada_nova_nao_comeca_pelo_ultimo(semente):
    s = sorteio(semente=semente)
    ids = [s.proxima(DOM).id for _ in range(6)]
    assert ids[2] != ids[3]


def test_cada_chefe_tem_o_seu_sorteio():
    s = sorteio()
    assert s.proxima("outro_chefe").id.startswith("dica-")  # sem fatos: dica
    assert s.proxima(DOM).e_fato


def test_mesma_semente_mesma_ordem():
    a, b = sorteio(semente=7), sorteio(semente=7)
    assert [a.proxima(DOM).id for _ in range(9)] == [b.proxima(DOM).id for _ in range(9)]


def test_fato_traz_a_fonte_e_fica_nos_vistos():
    s = sorteio()
    mensagem = s.proxima(DOM)
    assert mensagem.e_fato and mensagem.fonte == FONTE
    for _ in range(5):
        s.proxima(DOM)
    assert sorted(s.vistos[DOM]) == ["teste-1", "teste-2", "teste-3"]  # sem repetir


# --- validação -----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("texto", "frases"),
    [
        ("Uma frase.", 1),
        ("Sem ponto final", 1),
        ("Uma. Duas!", 2),
        ("Uma. Duas? Três…", 3),
        ("A Lei 12.305/2010 conta como uma frase.", 1),
    ],
)
def test_contar_frases(texto, frases):
    assert contar_frases(texto) == frases


def fato(**mudancas):
    fonte = replace(FONTE, **mudancas.pop("fonte", {}))
    return replace(FATOS[0], fonte=fonte, **mudancas)


@pytest.mark.parametrize(
    ("tabela", "mensagem"),
    [
        (TabelaFatos(()), "pelo menos uma dica"),
        (TabelaFatos(DICAS, (fato(id="dica-a"),)), "id repetido: dica-a"),
        (TabelaFatos(DICAS, (fato(chefe="baron"),)), "não existe o chefe 'baron'"),
        (TabelaFatos(DICAS, (fato(texto="  "),)), "não pode ficar vazio"),
        (TabelaFatos(DICAS, (fato(texto="Um. Dois. Três."),)), r"no máximo 2 frases \(C7\)"),
        (TabelaFatos(DICAS, (fato(texto="a" * 221),)), "no máximo 220 caracteres"),
        (TabelaFatos((Dica("d", "Um. Dois. Três."),)), "dicas.d.texto: no máximo 2 frases"),
        (TabelaFatos(DICAS, (fato(fonte={"titulo": ""}),)), r"fonte.titulo: .*\(C1\)"),
        (TabelaFatos(DICAS, (fato(fonte={"autor": " "}),)), r"fonte.autor: .*\(C1\)"),
        (TabelaFatos(DICAS, (fato(fonte={"consultado_em": "16/10/2026"}),)), "AAAA-MM-DD"),
        (TabelaFatos(DICAS, (fato(fonte={"ano": 2030}),)), "antes da consulta"),
        (TabelaFatos(DICAS, (fato(fonte={"url": "www.x"}),)), "https://"),
    ],
)
def test_fatos_invalidos(tabela, mensagem):
    with pytest.raises(DadosInvalidos, match=mensagem):
        validar_fatos(tabela, CHEFES)


def test_fato_de_exemplo_e_valido():
    assert validar_fatos(TABELA, CHEFES) is TABELA


BRUTO = {
    "id": "x",
    "chefe": DOM,
    "texto": "Fato de teste.",
    "fonte": {
        "titulo": "Documento de teste",
        "autor": "Autor de teste",
        "ano": 2020,
        "tipo": "orgao_oficial",
        "consultado_em": "2026-10-16",
    },
}


def test_fato_sem_fonte_nem_carrega():
    sem_fonte = {k: v for k, v in BRUTO.items() if k != "fonte"}
    with pytest.raises(DadosInvalidos, match="falta a chave fonte"):
        converter({"dicas": [], "fatos": [sem_fonte]}, TabelaFatos, "fatos")


def test_livro_nao_e_fonte_aceita():
    livro = {**BRUTO, "fonte": {**BRUTO["fonte"], "tipo": "livro"}}
    with pytest.raises(DadosInvalidos, match="'livro' não é um de legislacao"):
        converter({"dicas": [], "fatos": [livro]}, TabelaFatos, "fatos")
