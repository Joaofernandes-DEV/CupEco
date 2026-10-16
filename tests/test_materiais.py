import copy

import pytest

from cupeco.dominio.dados import DadosInvalidos, ler_toml
from cupeco.dominio.materiais import Material, Tipo, carregar_materiais, montar_tabela


def test_seis_materiais_quatro_reciclaveis():
    assert [m.value for m in Material] == [
        "papel",
        "plastico",
        "vidro",
        "metal",
        "rejeito",
        "perigoso",
    ]
    reciclaveis = [m for m in Material if m.tipo is Tipo.RECICLAVEL]
    assert reciclaveis == [Material.PAPEL, Material.PLASTICO, Material.VIDRO, Material.METAL]


def test_rejeito_e_perigoso_nao_podem_ser_separados():
    assert Material.REJEITO.tipo is Tipo.REJEITO
    assert Material.PERIGOSO.tipo is Tipo.PERIGOSO
    assert not Material.REJEITO.separavel
    assert not Material.PERIGOSO.separavel
    assert all(
        m.separavel for m in (Material.PAPEL, Material.PLASTICO, Material.VIDRO, Material.METAL)
    )


def test_todo_material_tem_cor_e_icone_distintos():
    # D15 / R3: nenhuma informação só por cor; cada material tem também um ícone próprio.
    tabela = carregar_materiais()
    cores = {tabela[m].cor for m in Material}
    icones = {tabela[m].icone for m in Material}
    assert len(cores) == len(icones) == len(Material)


def test_cores_seguem_o_padrao_conama():
    # Confere o matiz dominante de cada cor, não o tom exato (escolha de arte).
    tabela = carregar_materiais()
    r, g, b = tabela[Material.PAPEL].cor
    assert b > r and b > g  # azul
    r, g, b = tabela[Material.PLASTICO].cor
    assert r > g and r > b  # vermelho
    r, g, b = tabela[Material.VIDRO].cor
    assert g > r and g > b  # verde
    r, g, b = tabela[Material.METAL].cor
    assert r > b and g > b and abs(r - g) < 70  # amarelo
    r, g, b = tabela[Material.PERIGOSO].cor
    assert r > g > b  # laranja
    r, g, b = tabela[Material.REJEITO].cor
    assert max(r, g, b) - min(r, g, b) < 12  # cinza


def test_tabela_tem_fonte():
    assert "CONAMA nº 275" in carregar_materiais().fonte


def _bruto():
    return copy.deepcopy(ler_toml("materiais.toml"))


def test_material_faltando_e_erro():
    bruto = _bruto()
    del bruto["vidro"]
    with pytest.raises(DadosInvalidos, match="materiais: falta: vidro"):
        montar_tabela(bruto)


def test_material_desconhecido_e_erro():
    bruto = _bruto()
    bruto["madeira"] = {"nome": "Madeira", "cor": [0, 0, 0], "icone": "tabua"}
    with pytest.raises(DadosInvalidos, match="chave desconhecida: madeira"):
        montar_tabela(bruto)


def test_cor_fora_da_faixa_e_erro():
    bruto = _bruto()
    bruto["papel"]["cor"] = [38, 98, 300]
    with pytest.raises(DadosInvalidos, match="materiais.papel.cor"):
        montar_tabela(bruto)


def test_icone_vazio_e_erro():
    bruto = _bruto()
    bruto["metal"]["icone"] = " "
    with pytest.raises(DadosInvalidos, match="todo material precisa de ícone"):
        montar_tabela(bruto)


def test_icone_repetido_e_erro():
    bruto = _bruto()
    bruto["vidro"]["icone"] = bruto["plastico"]["icone"]
    with pytest.raises(DadosInvalidos, match="mesmo ícone"):
        montar_tabela(bruto)


def test_fonte_vazia_e_erro():
    bruto = _bruto()
    bruto["fonte"] = ""
    with pytest.raises(DadosInvalidos, match="fonte não pode ficar vazia"):
        montar_tabela(bruto)


def test_arte_usa_as_mesmas_cores_do_jogo():
    from ferramentas.arte import paleta

    tabela = carregar_materiais()
    assert paleta.PAPEL[:3] == tabela[Material.PAPEL].cor
    assert paleta.PERIGOSO[:3] == tabela[Material.PERIGOSO].cor
