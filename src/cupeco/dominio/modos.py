"""Modos Normal e Simples (J13, D13, D31): multiplicadores aplicados ao carregar a luta.

Cada modo é um conjunto de porcentagens de `conteudo/modos.toml` (100 = sem mudança):

- **vida** do chefe. As fases começam nas mesmas porcentagens da vida máxima, então as 3
  fases continuam em todos os modos (D13);
- **projeteis** de cada ataque, por ataque: se o ataque dispara várias vezes, o intervalo
  entre os disparos aumenta (menos disparos na mesma duração); se dispara uma vez só, a
  quantidade cai. Nunca menos que 1. O leque mantém o formato (as rotações) e só perde
  disparos quando repete. Zona e barra não têm projéteis;
- **velocidade** dos projéteis, dos inimigos menores e do movimento do chefe;
- **aviso** antes de cada ataque, arredondado para cima.

Depois de aplicar o modo, o chefe é validado de novo com o aviso mínimo daquele modo
(J6, D30): um Simples com aviso curto nem carrega. Contas em inteiros ou com as quatro
operações (D23).
"""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from enum import Enum
from functools import cache

from cupeco.dominio.ataques import (
    AVISO_MINIMO_NORMAL,
    AVISO_MINIMO_SIMPLES,
    DadosAtaque,
    TipoAtaque,
)
from cupeco.dominio.chefe import DadosChefe, DadosFase, validar_chefe
from cupeco.dominio.dados import DadosInvalidos, converter, ler_toml


class Modo(Enum):
    NORMAL = "normal"
    SIMPLES = "simples"


AVISO_MINIMO = {Modo.NORMAL: AVISO_MINIMO_NORMAL, Modo.SIMPLES: AVISO_MINIMO_SIMPLES}


@dataclass(frozen=True)
class DadosModo:
    vida: int  # porcentagens (100 = sem mudança)
    projeteis: int
    velocidade: int
    aviso: int


@dataclass(frozen=True)
class TabelaModos:
    normal: DadosModo
    simples: DadosModo

    def de(self, modo: Modo) -> DadosModo:
        return getattr(self, modo.value)


def validar_modos(tabela: TabelaModos) -> TabelaModos:
    for modo in Modo:
        dados = tabela.de(modo)
        for campo in fields(dados):
            if getattr(dados, campo.name) <= 0:
                raise DadosInvalidos(f"modos.{modo.value}.{campo.name}: precisa ser positivo")
        if dados.aviso < 100:
            raise DadosInvalidos(f"modos.{modo.value}.aviso: o aviso nunca diminui (J6)")
    normal, simples = tabela.normal, tabela.simples
    for nome in ("vida", "projeteis", "velocidade"):
        if getattr(simples, nome) > getattr(normal, nome):
            raise DadosInvalidos(f"modos.simples.{nome}: o Simples não pode passar do Normal")
    if simples.aviso < normal.aviso:
        raise DadosInvalidos("modos.simples.aviso: o Simples não pode avisar menos que o Normal")
    return tabela


@cache
def carregar_modos() -> TabelaModos:
    return validar_modos(converter(ler_toml("modos.toml"), TabelaModos, "modos"))


# --- contas --------------------------------------------------------------------------


def _arredondar(valor: int, porcentagem: int) -> int:
    """`valor` × `porcentagem` / 100, arredondado para o inteiro mais perto."""
    return (valor * porcentagem + 50) // 100


def _dividir_para_cima(valor: int, divisor: int) -> int:
    return -(-valor // divisor)


def disparos(ataque: DadosAtaque) -> int:
    """Quantas vezes o ataque dispara na etapa ativa."""
    if ataque.intervalo == 0:
        return 1
    return _dividir_para_cima(ataque.duracao, ataque.intervalo)


def _menos_projeteis(ataque: DadosAtaque, porcentagem: int) -> DadosAtaque:
    if porcentagem == 100 or ataque.tipo in (TipoAtaque.ZONA, TipoAtaque.BARRA):
        return ataque
    vezes = disparos(ataque)
    if vezes > 1:
        alvo = max(1, _arredondar(vezes, porcentagem))
        # Com intervalo = duração / alvo (para cima), saem no máximo `alvo` disparos.
        return replace(ataque, intervalo=_dividir_para_cima(ataque.duracao, alvo))
    if ataque.tipo is TipoAtaque.LEQUE:
        return ataque  # o formato do leque fica igual
    return replace(ataque, quantidade=max(1, _arredondar(ataque.quantidade, porcentagem)))


def _ajustar_ataque(ataque: DadosAtaque, modo: DadosModo) -> DadosAtaque:
    ataque = _menos_projeteis(ataque, modo.projeteis)
    return replace(
        ataque,
        aviso=_dividir_para_cima(ataque.aviso * modo.aviso, 100),
        velocidade=ataque.velocidade * (modo.velocidade / 100),
    )


def _ajustar_fase(fase: DadosFase, modo: DadosModo) -> DadosFase:
    return replace(
        fase,
        velocidade=fase.velocidade * (modo.velocidade / 100),
        ataques=tuple(_ajustar_ataque(ataque, modo) for ataque in fase.ataques),
    )


def aplicar_modo(dados: DadosChefe, modo: Modo, tabela: TabelaModos | None = None) -> DadosChefe:
    """O chefe com os multiplicadores do modo, validado com o aviso mínimo do modo."""
    multiplicadores = (tabela or carregar_modos()).de(modo)
    ajustado = replace(
        dados,
        vida=max(1, _arredondar(dados.vida, multiplicadores.vida)),
        fases=tuple(_ajustar_fase(fase, multiplicadores) for fase in dados.fases),
    )
    return validar_chefe(ajustado, f"chefe {dados.nome} ({modo.value})", AVISO_MINIMO[modo])
