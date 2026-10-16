from dataclasses import replace

import pytest

from cupeco.dominio.dados import DadosInvalidos
from cupeco.dominio.materiais import Material
from cupeco.dominio.triagem import (
    ResultadoTriagem,
    carregar_regras_triagem,
    resolver,
    validar_regras,
)

REGRAS = carregar_regras_triagem()
CERTA, OUTRA, PROIBIDA = (
    ResultadoTriagem.CERTA,
    ResultadoTriagem.OUTRA_COR,
    ResultadoTriagem.PROIBIDA,
)

# Tabela 5.2 do briefing, inteira: resíduo × arma da V1 (plástico e papel).
MATRIZ = [
    (Material.PLASTICO, Material.PLASTICO, CERTA, 100),
    (Material.PLASTICO, Material.PAPEL, OUTRA, 50),
    (Material.PAPEL, Material.PAPEL, CERTA, 100),
    (Material.PAPEL, Material.PLASTICO, OUTRA, 50),
    (Material.VIDRO, Material.PLASTICO, OUTRA, 50),
    (Material.VIDRO, Material.PAPEL, OUTRA, 50),
    (Material.METAL, Material.PLASTICO, OUTRA, 50),
    (Material.METAL, Material.PAPEL, OUTRA, 50),
    (Material.REJEITO, Material.PLASTICO, PROIBIDA, 0),
    (Material.REJEITO, Material.PAPEL, PROIBIDA, 0),
    (Material.PERIGOSO, Material.PLASTICO, PROIBIDA, 0),
    (Material.PERIGOSO, Material.PAPEL, PROIBIDA, 0),
]


def test_valores_padrao_seguem_d25():
    assert REGRAS.pontos_triagem_certa == 100
    assert REGRAS.pontos_triagem_outra_cor == 50


@pytest.mark.parametrize(("residuo", "arma", "resultado", "pontos"), MATRIZ)
def test_matriz_da_triagem(residuo, arma, resultado, pontos):
    resolucao = resolver(residuo, arma, REGRAS)
    assert resolucao.resultado is resultado
    assert resolucao.pontos == pontos
    assert resolucao.separou is (resultado is not PROIBIDA)
    assert resolucao.causa_dano is (resultado is PROIBIDA)


def test_matriz_cobre_todos_os_residuos():
    assert {residuo for residuo, *_ in MATRIZ} == set(Material)


@pytest.mark.parametrize(
    ("alteracao", "mensagem"),
    [
        ({"pontos_por_dano": 0}, "precisa ser positivo"),
        ({"pontos_triagem_outra_cor": 100}, "cor certa precisa render mais"),
    ],
)
def test_regras_invalidas(alteracao, mensagem):
    with pytest.raises(DadosInvalidos, match=mensagem):
        validar_regras(replace(REGRAS, **alteracao))
