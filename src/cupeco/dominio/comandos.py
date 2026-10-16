"""Comandos do jogador (D24).

A cada passo a interface entrega só o **conjunto de botões segurados**; o domínio descobre
quando cada botão acabou de ser apertado ou solto comparando com o passo anterior. Assim
teclado e controle viram a mesma coisa, e um replay é só a semente mais a lista de
conjuntos de botões.
"""

from __future__ import annotations

from enum import Enum

Direcao = tuple[int, int]


class Botao(Enum):
    ESQUERDA = "esquerda"
    DIREITA = "direita"
    CIMA = "cima"
    BAIXO = "baixo"
    PULO = "pulo"  # também a Triagem, no ar (J3)
    TIRO = "tiro"
    DASH = "dash"
    EX = "ex"
    TRAVAR = "travar"
    TROCAR = "trocar"  # troca de arma


Comandos = frozenset[Botao]
NENHUM: Comandos = frozenset()


class Controle:
    """Botões deste passo e do anterior."""

    def __init__(self) -> None:
        self.atual: Comandos = NENHUM
        self.anterior: Comandos = NENHUM

    def atualizar(self, segurados: Comandos) -> None:
        self.anterior = self.atual
        self.atual = frozenset(segurados)

    def segurando(self, botao: Botao) -> bool:
        return botao in self.atual

    def apertou(self, botao: Botao) -> bool:
        """Verdadeiro só no primeiro passo em que o botão está segurado."""
        return botao in self.atual and botao not in self.anterior

    def soltou(self, botao: Botao) -> bool:
        return botao not in self.atual and botao in self.anterior

    @property
    def horizontal(self) -> int:
        """-1 (esquerda), 0 ou 1 (direita); os dois juntos se anulam."""
        return int(Botao.DIREITA in self.atual) - int(Botao.ESQUERDA in self.atual)

    @property
    def vertical(self) -> int:
        """-1 (cima), 0 ou 1 (baixo), na convenção da tela (y cresce para baixo)."""
        return int(Botao.BAIXO in self.atual) - int(Botao.CIMA in self.atual)

    @property
    def direcao(self) -> Direcao:
        return (self.horizontal, self.vertical)
