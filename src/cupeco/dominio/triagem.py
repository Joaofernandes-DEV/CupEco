"""Regras da Triagem, o parry do jogo (J3, D12): a tabela 5.2 do briefing.

| Resíduo tocado              | Arma da mesma cor | Arma de outra cor |
|-----------------------------|-------------------|-------------------|
| Reciclável                  | +1 fardo, separa  | +½ fardo, separa  |
| Rejeito (cinza)             | dano              | dano              |
| Perigoso (laranja)          | dano              | dano              |

Os pontos vêm de `conteudo/triagem.toml` (D26).
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from enum import Enum
from functools import cache

from cupeco.dominio.dados import DadosInvalidos, converter, ler_toml
from cupeco.dominio.materiais import Material


class ResultadoTriagem(Enum):
    CERTA = "certa"
    OUTRA_COR = "outra_cor"
    PROIBIDA = "proibida"


@dataclass(frozen=True)
class RegrasTriagem:
    pontos_triagem_certa: int
    pontos_triagem_outra_cor: int
    pontos_por_dano: int
    dano_super: int
    quadros_super: int


@dataclass(frozen=True)
class Resolucao:
    resultado: ResultadoTriagem
    pontos: int

    @property
    def separou(self) -> bool:
        return self.resultado is not ResultadoTriagem.PROIBIDA

    @property
    def causa_dano(self) -> bool:
        return self.resultado is ResultadoTriagem.PROIBIDA


def validar_regras(regras: RegrasTriagem) -> RegrasTriagem:
    for campo in fields(regras):
        valor = getattr(regras, campo.name)
        if valor <= 0:
            raise DadosInvalidos(f"triagem.{campo.name}: precisa ser positivo, veio {valor}")
    if regras.pontos_triagem_outra_cor >= regras.pontos_triagem_certa:
        raise DadosInvalidos("triagem: a cor certa precisa render mais que outra cor")
    return regras


@cache
def carregar_regras_triagem() -> RegrasTriagem:
    return validar_regras(converter(ler_toml("triagem.toml"), RegrasTriagem, "triagem"))


def resolver(residuo: Material, arma: Material, regras: RegrasTriagem) -> Resolucao:
    """O que acontece ao "separar" `residuo` com a lixeira ativa da cor de `arma`."""
    if not residuo.separavel:
        return Resolucao(ResultadoTriagem.PROIBIDA, 0)
    if residuo is arma:
        return Resolucao(ResultadoTriagem.CERTA, regras.pontos_triagem_certa)
    return Resolucao(ResultadoTriagem.OUTRA_COR, regras.pontos_triagem_outra_cor)
