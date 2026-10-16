"""Tela de título com menu: a luta contra o Dom, a arena de testes e sair (Esc também sai)."""

import pygame

from cupeco import __version__
from cupeco.config import LARGURA_TELA, TITULO, Paleta
from cupeco.dominio.chefe import carregar_chefe
from cupeco.estados.base import Estado
from cupeco.estados.luta import CHEFE_PADRAO
from cupeco.jogo import Jogo
from cupeco.ui.desenho import DESTAQUE_NO_CLARO, Desenho
from cupeco.ui.menu import Menu

# As quatro cores principais da coleta seletiva, como enfeite provisório até a arte (Fase 3).
CORES_MATERIAIS = (Paleta.PAPEL, Paleta.PLASTICO, Paleta.VIDRO, Paleta.METAL)
ARENA = "Arena de testes"
SAIR = "Sair"


class EstadoTitulo(Estado):
    def __init__(self, jogo: Jogo) -> None:
        super().__init__(jogo)
        self.desenho = Desenho()
        self.lutar = f"Lutar contra o {carregar_chefe(CHEFE_PADRAO).nome}"
        self.menu = Menu((self.lutar, ARENA, SAIR))
        # Fonte padrão do pygame até a fonte dos anos 30 com acentos chegar (Fase 3, I12).
        fonte_titulo = pygame.font.Font(None, 160)
        fonte_texto = pygame.font.Font(None, 44)
        fonte_dica = pygame.font.Font(None, 32)
        self._linhas = [
            (fonte_titulo.render(TITULO.upper(), True, Paleta.TEXTO), 140),
            (fonte_texto.render("Dara contra os Rejeitos de Aterrópolis", True, Paleta.TEXTO), 270),
            (fonte_dica.render(f"v{__version__}", True, Paleta.APAGADO), 660),
        ]

    def tratar_evento(self, evento: pygame.Event) -> None:
        if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
            self.jogo.encerrar()
            return
        escolha = self.menu.tratar(evento)
        if escolha == self.lutar:
            from cupeco.estados.escolha_modo import EstadoEscolhaModo

            self.jogo.trocar_estado(EstadoEscolhaModo(self.jogo, CHEFE_PADRAO))
        elif escolha == ARENA:
            from cupeco.estados.arena import EstadoArena

            self.jogo.trocar_estado(EstadoArena(self.jogo))
        elif escolha == SAIR:
            self.jogo.encerrar()

    def desenhar(self, tela: pygame.Surface) -> None:
        tela.fill(Paleta.FUNDO)
        for superficie, y in self._linhas:
            tela.blit(superficie, superficie.get_rect(midtop=(LARGURA_TELA // 2, y)))
        espaco = 90
        inicio = LARGURA_TELA // 2 - espaco * (len(CORES_MATERIAIS) - 1) // 2
        for indice, cor in enumerate(CORES_MATERIAIS):
            pygame.draw.circle(tela, cor, (inicio + indice * espaco, 380), 28)
        self.menu.desenhar(
            tela, self.desenho, LARGURA_TELA // 2, 470, Paleta.TEXTO, DESTAQUE_NO_CLARO
        )
