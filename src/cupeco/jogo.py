"""Loop principal e troca de estados (telas) do jogo."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from cupeco.config import ALTURA_TELA, FPS, LARGURA_TELA, TITULO
from cupeco.passo_fixo import PassoFixo
from cupeco.ui.entrada import Entrada

if TYPE_CHECKING:
    from cupeco.estados.base import Estado


class Jogo:
    """Dono da janela e do único loop do jogo; a tela atual é o `estado`."""

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(TITULO)
        # SCALED ajusta a resolução lógica ao tamanho da janela.
        self.tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA), pygame.SCALED)
        self.relogio = pygame.time.Clock()
        self.passo_fixo = PassoFixo()
        self.entrada = Entrada()
        self.estado: Estado | None = None
        self.rodando = False

    def trocar_estado(self, estado: Estado) -> None:
        self.estado = estado

    def encerrar(self) -> None:
        """Pede o fim do loop; o pygame é encerrado ao sair de `executar`."""
        self.rodando = False

    def executar(self) -> None:
        self.rodando = True
        try:
            while self.rodando:
                passos = self.passo_fixo.avancar(self.relogio.tick(FPS))
                for evento in pygame.event.get():
                    self.entrada.tratar_evento(evento)
                    if evento.type == pygame.QUIT:
                        self.encerrar()
                    elif self.estado is not None:
                        self.estado.tratar_evento(evento)
                if not self.rodando:
                    break
                if self.estado is not None:
                    for _ in range(passos):
                        self.estado.atualizar()
                    self.estado.desenhar(self.tela)
                pygame.display.flip()
        finally:
            pygame.quit()
