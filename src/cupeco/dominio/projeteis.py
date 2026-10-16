"""Projéteis: os tiros da Dara e, depois, os ataques dos chefes (resíduos e outros).

Andam em linha reta, sem gravidade, e somem quando o tempo de vida acaba ou saem da tela.
Os vetores das 8 direções de mira são escritos à mão (0,7071 nas diagonais), sem
trigonometria (D23).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from cupeco.dominio.comandos import Direcao
from cupeco.dominio.fisica import Caixa
from cupeco.dominio.materiais import Material

DIAGONAL = 0.7071067811865476  # 1 / raiz de 2

VETORES: dict[Direcao, tuple[float, float]] = {
    (1, 0): (1.0, 0.0),
    (-1, 0): (-1.0, 0.0),
    (0, -1): (0.0, -1.0),
    (0, 1): (0.0, 1.0),
    (1, -1): (DIAGONAL, -DIAGONAL),
    (-1, -1): (-DIAGONAL, -DIAGONAL),
    (1, 1): (DIAGONAL, DIAGONAL),
    (-1, 1): (-DIAGONAL, DIAGONAL),
}


class Dono(Enum):
    JOGADOR = "jogador"
    INIMIGO = "inimigo"


def tamanho_orientado(largura: float, altura: float, dx: float, dy: float) -> tuple[float, float]:
    """Caixa de um projétil desenhado na horizontal, conforme a direção em que voa."""
    if dy == 0:
        return (largura, altura)
    if dx == 0:
        return (altura, largura)
    media = (largura + altura) / 2
    return (media, media)


@dataclass
class Projetil:
    """`x` e `y` são o centro. `material` é o resíduo (ataques inimigos) ou a cor da arma."""

    x: float
    y: float
    largura: float
    altura: float
    vx: float
    vy: float
    dano: int
    quadros_de_vida: int
    dono: Dono
    material: Material | None = None
    perfura: bool = False
    ex: bool = False
    # Nomes dos alvos já atingidos: um tiro perfurante acerta cada alvo uma vez só.
    alvos_atingidos: set[str] = field(default_factory=set)

    @property
    def caixa(self) -> Caixa:
        return Caixa(self.x - self.largura / 2, self.y - self.altura / 2, self.largura, self.altura)

    @property
    def vivo(self) -> bool:
        return self.quadros_de_vida > 0

    def atualizar(self) -> None:
        self.x += self.vx
        self.y += self.vy
        self.quadros_de_vida -= 1

    def fora_da_area(self, area: Caixa) -> bool:
        """Saiu inteiro da área (a tela com alguma margem)."""
        return not self.caixa.sobrepoe(area)
