"""Tela de título provisória: nome do jogo; Enter leva à arena de testes e Esc fecha."""

import pygame

from cupeco import __version__
from cupeco.config import LARGURA_TELA, TITULO, Paleta
from cupeco.estados.base import Estado
from cupeco.jogo import Jogo

# As quatro cores principais da coleta seletiva, como enfeite provisório até a arte (Fase 3).
CORES_MATERIAIS = (Paleta.PAPEL, Paleta.PLASTICO, Paleta.VIDRO, Paleta.METAL)


class EstadoTitulo(Estado):
    def __init__(self, jogo: Jogo) -> None:
        super().__init__(jogo)
        # Fonte padrão do pygame até a fonte dos anos 30 com acentos chegar (Fase 3, I12).
        fonte_titulo = pygame.font.Font(None, 160)
        fonte_texto = pygame.font.Font(None, 44)
        fonte_dica = pygame.font.Font(None, 32)
        self._linhas = [
            (fonte_titulo.render(TITULO.upper(), True, Paleta.TEXTO), 200),
            (fonte_texto.render("Dara contra os Rejeitos de Aterrópolis", True, Paleta.TEXTO), 330),
            (fonte_dica.render("Enter (ou A): arena de testes", True, Paleta.TEXTO), 560),
            (fonte_dica.render("Esc: sair", True, Paleta.APAGADO), 600),
            (fonte_dica.render(f"v{__version__}", True, Paleta.APAGADO), 640),
        ]

    def tratar_evento(self, evento: pygame.Event) -> None:
        if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
            self.jogo.encerrar()
        entrar = (
            evento.type == pygame.KEYDOWN and evento.key in (pygame.K_RETURN, pygame.K_z)
        ) or (
            evento.type == pygame.CONTROLLERBUTTONDOWN
            and evento.button == pygame.CONTROLLER_BUTTON_A
        )
        if entrar:
            from cupeco.estados.arena import EstadoArena

            self.jogo.trocar_estado(EstadoArena(self.jogo))

    def desenhar(self, tela: pygame.Surface) -> None:
        tela.fill(Paleta.FUNDO)
        for superficie, y in self._linhas:
            tela.blit(superficie, superficie.get_rect(midtop=(LARGURA_TELA // 2, y)))
        espaco = 90
        inicio = LARGURA_TELA // 2 - espaco * (len(CORES_MATERIAIS) - 1) // 2
        for indice, cor in enumerate(CORES_MATERIAIS):
            pygame.draw.circle(tela, cor, (inicio + indice * espaco, 460), 28)
