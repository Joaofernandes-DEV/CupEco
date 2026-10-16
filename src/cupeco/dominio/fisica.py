"""Física das lutas: caixas de colisão, gravidade e plataformas.

Coordenadas em pixels lógicos (1280×720), com y crescendo para baixo; velocidades em
pixels por passo de simulação (1/60 s, D8). Só as quatro operações e comparações (D23).

A colisão é resolvida um eixo de cada vez, primeiro o x e depois o y, e por **varredura**:
uma borda só bate numa plataforma se, antes do passo, estava do lado de fora dela. Assim um
corpo rápido não atravessa um chão fino, e um corpo que já está dentro de uma plataforma
atravessável (subindo por ela) não fica preso.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class Caixa:
    """Retângulo alinhado aos eixos; `x` e `y` são o canto superior esquerdo."""

    x: float
    y: float
    largura: float
    altura: float

    @property
    def esquerda(self) -> float:
        return self.x

    @property
    def direita(self) -> float:
        return self.x + self.largura

    @property
    def topo(self) -> float:
        return self.y

    @property
    def base(self) -> float:
        return self.y + self.altura

    @property
    def centro(self) -> tuple[float, float]:
        return (self.x + self.largura / 2, self.y + self.altura / 2)

    def sobrepoe(self, outra: Caixa) -> bool:
        """Há área em comum? Caixas que só encostam pela borda não se sobrepõem."""
        return (
            self.esquerda < outra.direita
            and outra.esquerda < self.direita
            and self.topo < outra.base
            and outra.topo < self.base
        )

    def deslocada(self, dx: float, dy: float) -> Caixa:
        return Caixa(self.x + dx, self.y + dy, self.largura, self.altura)


@dataclass(frozen=True)
class Plataforma:
    """Algo em que se pisa. A atravessável só segura quem cai sobre ela vindo de cima."""

    caixa: Caixa
    atravessavel: bool = False


@dataclass(frozen=True)
class Contatos:
    """O que o corpo tocou neste passo."""

    chao: bool = False
    teto: bool = False
    parede_esquerda: bool = False
    parede_direita: bool = False


@dataclass
class Corpo:
    """Algo que se move e colide (a Dara, inimigos que andam). `y` é o topo da caixa."""

    x: float
    y: float
    largura: float
    altura: float
    vx: float = 0.0
    vy: float = 0.0
    no_chao: bool = False

    @property
    def caixa(self) -> Caixa:
        return Caixa(self.x, self.y, self.largura, self.altura)


def _cruza_horizontal(a: Caixa, b: Caixa) -> bool:
    """As caixas têm faixa horizontal em comum (para colisões no eixo y)."""
    return a.esquerda < b.direita and b.esquerda < a.direita


def _cruza_vertical(a: Caixa, b: Caixa) -> bool:
    """As caixas têm faixa vertical em comum (para colisões no eixo x)."""
    return a.topo < b.base and b.topo < a.base


def _mover_x(corpo: Corpo, solidas: list[Caixa]) -> tuple[bool, bool]:
    antes = corpo.caixa
    depois = antes.deslocada(corpo.vx, 0)
    if corpo.vx > 0:
        limites = [
            p.esquerda
            for p in solidas
            if _cruza_vertical(depois, p) and antes.direita <= p.esquerda < depois.direita
        ]
        if limites:
            corpo.x = min(limites) - corpo.largura
            corpo.vx = 0.0
            return (False, True)
    elif corpo.vx < 0:
        limites = [
            p.direita
            for p in solidas
            if _cruza_vertical(depois, p) and depois.esquerda < p.direita <= antes.esquerda
        ]
        if limites:
            corpo.x = max(limites)
            corpo.vx = 0.0
            return (True, False)
    corpo.x = depois.x
    return (False, False)


def _mover_y(corpo: Corpo, plataformas: Iterable[Plataforma], descer: bool) -> tuple[bool, bool]:
    antes = corpo.caixa
    depois = antes.deslocada(0, corpo.vy)
    if corpo.vy > 0:
        limites = [
            p.caixa.topo
            for p in plataformas
            if not (p.atravessavel and descer)
            and _cruza_horizontal(depois, p.caixa)
            and antes.base <= p.caixa.topo < depois.base
        ]
        if limites:
            corpo.y = min(limites) - corpo.altura
            corpo.vy = 0.0
            return (True, False)
    elif corpo.vy < 0:
        limites = [
            p.caixa.base
            for p in plataformas
            if not p.atravessavel
            and _cruza_horizontal(depois, p.caixa)
            and depois.topo < p.caixa.base <= antes.topo
        ]
        if limites:
            corpo.y = max(limites)
            corpo.vy = 0.0
            return (False, True)
    corpo.y = depois.y
    return (False, False)


def mover(
    corpo: Corpo,
    plataformas: Iterable[Plataforma],
    gravidade: float,
    queda_maxima: float,
    descer: bool = False,
) -> Contatos:
    """Avança o corpo um passo: aplica a gravidade, anda em x, depois em y.

    `descer` faz o corpo atravessar as plataformas atravessáveis neste passo (o jogador
    segurando para baixo + pulo, por exemplo).
    """
    plataformas = list(plataformas)
    corpo.vy = min(corpo.vy + gravidade, queda_maxima)
    solidas = [p.caixa for p in plataformas if not p.atravessavel]
    parede_esquerda, parede_direita = _mover_x(corpo, solidas)
    chao, teto = _mover_y(corpo, plataformas, descer)
    corpo.no_chao = chao
    return Contatos(
        chao=chao, teto=teto, parede_esquerda=parede_esquerda, parede_direita=parede_direita
    )
