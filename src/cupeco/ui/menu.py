"""Menus de opções: setas (ou direcional) escolhem; Enter, Z ou A confirmam."""

from __future__ import annotations

from collections.abc import Sequence

import pygame

from cupeco.config import Cor
from cupeco.ui.desenho import DESTAQUE, Desenho


def e_confirmar(evento: pygame.Event) -> bool:
    return (evento.type == pygame.KEYDOWN and evento.key in (pygame.K_RETURN, pygame.K_z)) or (
        evento.type == pygame.CONTROLLERBUTTONDOWN and evento.button == pygame.CONTROLLER_BUTTON_A
    )


def e_voltar(evento: pygame.Event) -> bool:
    """Esc no teclado ou B no controle."""
    return (evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE) or (
        evento.type == pygame.CONTROLLERBUTTONDOWN and evento.button == pygame.CONTROLLER_BUTTON_B
    )


def _direcao(evento: pygame.Event) -> int:
    if evento.type == pygame.KEYDOWN:
        return {pygame.K_UP: -1, pygame.K_DOWN: 1}.get(evento.key, 0)
    if evento.type == pygame.CONTROLLERBUTTONDOWN:
        botoes = {
            pygame.CONTROLLER_BUTTON_DPAD_UP: -1,
            pygame.CONTROLLER_BUTTON_DPAD_DOWN: 1,
        }
        return botoes.get(evento.button, 0)
    return 0


class Menu:
    """Uma lista de opções com uma marcada."""

    def __init__(self, opcoes: Sequence[str]) -> None:
        self.opcoes = tuple(opcoes)
        self.indice = 0

    @property
    def marcada(self) -> str:
        return self.opcoes[self.indice]

    def tratar(self, evento: pygame.Event) -> str | None:
        """Move a marca ou devolve a opção confirmada."""
        passo = _direcao(evento)
        if passo:
            self.indice = (self.indice + passo) % len(self.opcoes)
            return None
        return self.marcada if e_confirmar(evento) else None

    def desenhar(
        self, tela, desenho: Desenho, centro_x: int, y: int, cor: Cor, destaque: Cor = DESTAQUE
    ) -> None:
        """A opção marcada leva setas, além da cor (D15). Em fundo claro, use um `destaque`
        escuro."""
        for indice, opcao in enumerate(self.opcoes):
            marcada = indice == self.indice
            texto = f"> {opcao} <" if marcada else opcao
            cor_da_opcao = destaque if marcada else cor
            desenho.texto(tela, texto, (centro_x, y + indice * 46), cor_da_opcao, centro=True)
