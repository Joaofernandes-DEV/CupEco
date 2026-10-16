"""Classe base das telas do jogo."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from cupeco.jogo import Jogo


class Estado:
    """Uma tela do jogo. O `Jogo` repassa eventos, avança a lógica em passos fixos e desenha."""

    def __init__(self, jogo: Jogo) -> None:
        self.jogo = jogo

    def tratar_evento(self, evento: pygame.Event) -> None:
        """Reage a um evento (tecla, controle). Por padrão, ignora."""

    def atualizar(self) -> None:
        """Avança a lógica da tela em um passo fixo de 1/60 s. Por padrão, não faz nada."""

    def desenhar(self, tela: pygame.Surface) -> None:
        """Desenha a tela inteira na superfície da resolução lógica."""
