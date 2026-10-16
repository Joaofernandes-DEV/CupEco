"""Materiais da Triagem (D15): quais existem, quais podem ser separados e como aparecem.

A classificação (reciclável, rejeito, perigoso) é regra do jogo e fica no código; o nome,
a cor da CONAMA 275/2001 e o ícone de cada material ficam em `conteudo/materiais.toml`,
junto com a fonte. Todo material precisa de cor **e** ícone: nenhuma informação só por cor
(R3, I4).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import cache
from typing import Any

from cupeco.dominio.dados import DadosInvalidos, converter, ler_toml


class Tipo(Enum):
    RECICLAVEL = "reciclável"
    REJEITO = "rejeito"
    PERIGOSO = "perigoso"


class Material(Enum):
    PAPEL = "papel"
    PLASTICO = "plastico"
    VIDRO = "vidro"
    METAL = "metal"
    REJEITO = "rejeito"
    PERIGOSO = "perigoso"

    @property
    def tipo(self) -> Tipo:
        if self is Material.REJEITO:
            return Tipo.REJEITO
        if self is Material.PERIGOSO:
            return Tipo.PERIGOSO
        return Tipo.RECICLAVEL

    @property
    def separavel(self) -> bool:
        """Só os recicláveis podem ser "separados" pela Triagem (D12)."""
        return self.tipo is Tipo.RECICLAVEL


Rgb = tuple[int, int, int]


@dataclass(frozen=True)
class DadosMaterial:
    nome: str
    cor: Rgb
    icone: str


@dataclass(frozen=True)
class TabelaMateriais:
    fonte: str
    dados: dict[Material, DadosMaterial]

    def __getitem__(self, material: Material) -> DadosMaterial:
        return self.dados[material]


def montar_tabela(bruto: dict[str, Any]) -> TabelaMateriais:
    """Valida o conteúdo de `materiais.toml` (já lido) e monta a tabela."""
    esperadas = {material.value for material in Material} | {"fonte"}
    desconhecidas = sorted(set(bruto) - esperadas)
    if desconhecidas:
        raise DadosInvalidos(f"materiais: chave desconhecida: {', '.join(desconhecidas)}")
    faltando = sorted(esperadas - set(bruto))
    if faltando:
        raise DadosInvalidos(f"materiais: falta: {', '.join(faltando)}")
    fonte = converter(bruto["fonte"], str, "materiais.fonte")
    if not fonte.strip():
        raise DadosInvalidos("materiais.fonte: a fonte não pode ficar vazia (C1)")

    dados = {}
    for material in Material:
        onde = f"materiais.{material.value}"
        item = converter(bruto[material.value], DadosMaterial, onde)
        if any(not 0 <= canal <= 255 for canal in item.cor):
            raise DadosInvalidos(f"{onde}.cor: cada canal vai de 0 a 255, veio {item.cor}")
        if not item.icone.strip():
            raise DadosInvalidos(f"{onde}.icone: todo material precisa de ícone (D15)")
        dados[material] = item

    if len({item.cor for item in dados.values()}) != len(dados):
        raise DadosInvalidos("materiais: dois materiais com a mesma cor")
    if len({item.icone for item in dados.values()}) != len(dados):
        raise DadosInvalidos("materiais: dois materiais com o mesmo ícone")
    return TabelaMateriais(fonte=fonte, dados=dados)


@cache
def carregar_materiais() -> TabelaMateriais:
    """A tabela de materiais do jogo, lida uma única vez."""
    return montar_tabela(ler_toml("materiais.toml"))
