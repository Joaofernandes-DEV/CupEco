"""Escolha do modo antes da luta (J13, D13): Normal ou Simples, com as 3 fases nos dois."""

from __future__ import annotations

import pygame

from cupeco.config import LARGURA_TELA, Paleta
from cupeco.dominio.chefe import carregar_chefe
from cupeco.dominio.modos import Modo
from cupeco.estados.base import Estado
from cupeco.estados.luta import CHEFE_PADRAO, NOMES_DOS_MODOS, EstadoLuta, Luta
from cupeco.jogo import Jogo
from cupeco.ui.desenho import APAGADO, DESTAQUE_NO_CLARO, Desenho
from cupeco.ui.menu import Menu, e_voltar

DESCRICOES = {
    Modo.NORMAL: ("A luta como ela é: difícil, como os clássicos do gênero.",),
    Modo.SIMPLES: (
        "O chefe tem menos vida, e os ataques são mais lentos, mais espaçados e avisam antes.",
        "As 3 fases continuam.",
    ),
}


class EstadoEscolhaModo(Estado):
    def __init__(self, jogo: Jogo, chefe: str = CHEFE_PADRAO) -> None:
        super().__init__(jogo)
        self.chefe = chefe
        self.nome_do_chefe = carregar_chefe(chefe).nome
        self.modos = tuple(Modo)
        self.menu = Menu([NOMES_DOS_MODOS[m] for m in self.modos])
        self.desenho = Desenho()

    @property
    def modo_marcado(self) -> Modo:
        return self.modos[self.menu.indice]

    def tratar_evento(self, evento: pygame.Event) -> None:
        if e_voltar(evento):
            from cupeco.estados.titulo import EstadoTitulo

            self.jogo.trocar_estado(EstadoTitulo(self.jogo))
            return
        if self.menu.tratar(evento) is not None:
            luta = Luta(chefe=self.chefe, modo=self.modo_marcado)
            self.jogo.trocar_estado(EstadoLuta(self.jogo, luta))

    def desenhar(self, tela: pygame.Surface) -> None:
        tela.fill(Paleta.FUNDO)
        desenho, meio = self.desenho, LARGURA_TELA // 2
        desenho.texto(
            tela, self.nome_do_chefe, (meio, 150), Paleta.TEXTO, desenho.fonte_grande, True
        )
        desenho.texto(tela, "Escolha o modo", (meio, 220), APAGADO, desenho.fonte_media, True)
        self.menu.desenhar(tela, desenho, meio, 320, Paleta.TEXTO, DESTAQUE_NO_CLARO)
        for indice, linha in enumerate(DESCRICOES[self.modo_marcado]):
            desenho.texto(tela, linha, (meio, 460 + 32 * indice), Paleta.TEXTO, centro=True)
        desenho.texto(
            tela, "Enter, Z ou A: lutar   Esc ou B: voltar", (meio, 620), APAGADO, centro=True
        )
