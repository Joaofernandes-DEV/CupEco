"""Arena de testes (J7, I8): a primeira tela jogável, com formas simples no lugar da arte.

Serve para jogar e ajustar o movimento, os tiros e a Triagem antes da arte final (Fase 3).
O desenho comum com a luta fica em `ui/desenho.py`.

Teclas extras: Esc (ou Start) pausa; F1 mostra as caixas de colisão.
"""

from __future__ import annotations

from collections.abc import Callable

import pygame

from cupeco.config import ALTURA_TELA, LARGURA_TELA, Paleta
from cupeco.dominio.batalha import Batalha
from cupeco.dominio.comandos import Comandos
from cupeco.estados.base import Estado
from cupeco.jogo import Jogo
from cupeco.ui.desenho import FUNDO, TINTA, Desenho, mensagem_da_triagem, retangulo
from cupeco.ui.entrada import e_pausa
from cupeco.ui.menu import Menu, e_confirmar

SEMENTE_PADRAO = 1930

BONECO = (170, 150, 120)

OPCOES_PAUSA = ("Continuar", "Reiniciar", "Sair para o título")
QUADROS_AVISO = 120
AJUDA = (
    "Setas: mover  Z: pulo/Triagem  X: tiro  C: dash  V: EX/Super  Shift: travar  "
    "Tab: trocar  Esc: pausa  F1: caixas"
)


class EstadoArena(Estado):
    def __init__(
        self,
        jogo: Jogo,
        semente: int = SEMENTE_PADRAO,
        leitor: Callable[[], Comandos] | None = None,
    ) -> None:
        super().__init__(jogo)
        self._ler = leitor or jogo.entrada.ler
        self.semente = semente
        self.batalha = Batalha(semente)
        self.mostrar_caixas = False
        self.pausa_aberta = False
        self.menu_pausa = Menu(OPCOES_PAUSA)
        self.aviso: tuple[str, tuple[int, int, int], int] | None = None
        self.desenho = Desenho()

    @property
    def opcao(self) -> int:
        return self.menu_pausa.indice

    # --- eventos ---------------------------------------------------------------------

    def reiniciar(self) -> None:
        self.batalha = Batalha(self.semente)
        self.aviso = None
        self.pausa_aberta = False

    def tratar_evento(self, evento: pygame.Event) -> None:
        if evento.type == pygame.KEYDOWN and evento.key == pygame.K_F1:
            self.mostrar_caixas = not self.mostrar_caixas
            return
        if e_pausa(evento):
            self.pausa_aberta = not self.pausa_aberta
            self.menu_pausa.indice = 0
            return
        if self.pausa_aberta:
            escolha = self.menu_pausa.tratar(evento)
            if escolha == "Continuar":
                self.pausa_aberta = False
            elif escolha == "Reiniciar":
                self.reiniciar()
            elif escolha == "Sair para o título":
                from cupeco.estados.titulo import EstadoTitulo

                self.jogo.trocar_estado(EstadoTitulo(self.jogo))
        elif self.batalha.jogador.derrotada and e_confirmar(evento):
            self.reiniciar()

    # --- lógica ----------------------------------------------------------------------

    def atualizar(self) -> None:
        if self.pausa_aberta:
            return
        eventos = self.batalha.atualizar(self._ler())
        self._avisar(eventos)
        if self.aviso is not None:
            texto, cor, quadros = self.aviso
            self.aviso = (texto, cor, quadros - 1) if quadros > 1 else None

    def _avisar(self, eventos: list) -> None:
        """Explica a Triagem na hora: a parte educativa da arena (D17)."""
        mensagem = mensagem_da_triagem(self.batalha.jogador, eventos)
        if mensagem is not None:
            texto, residuo = mensagem
            self.aviso = (texto, self.desenho.cores[residuo], QUADROS_AVISO)

    # --- desenho ---------------------------------------------------------------------

    def desenhar(self, tela: pygame.Surface) -> None:
        tela.fill(FUNDO)
        batalha, desenho = self.batalha, self.desenho
        desenho.plataformas(tela, batalha.plataformas)
        self._desenhar_boneco(tela)
        for projetil in batalha.projeteis:
            desenho.projetil(tela, projetil)
        desenho.dara(tela, batalha.jogador, batalha.quadro)
        if self.mostrar_caixas:
            self._desenhar_caixas(tela)
        desenho.hud(tela, batalha.jogador)
        desenho.ajuda(tela, AJUDA, acima=self.mostrar_caixas)
        if self.aviso is not None:
            texto, cor, _ = self.aviso
            desenho.faixa(tela, texto, cor)
        if batalha.jogador.derrotada:
            self._desenhar_derrota(tela)
        if self.pausa_aberta:
            self._desenhar_pausa(tela)

    def _desenhar_boneco(self, tela: pygame.Surface) -> None:
        alvo, desenho = self.batalha.alvo, self.desenho
        pygame.draw.rect(tela, BONECO, retangulo(alvo.caixa), border_radius=18)
        pygame.draw.rect(tela, TINTA, retangulo(alvo.caixa), 3, border_radius=18)
        cx, _ = alvo.caixa.centro
        desenho.texto(
            tela, "boneco", (cx, alvo.caixa.y + 30), centro=True, fonte=desenho.fonte_pequena
        )
        desenho.texto(tela, str(alvo.dano_recebido), (cx, alvo.caixa.y + 70), centro=True)

    def _desenhar_caixas(self, tela: pygame.Surface) -> None:
        batalha = self.batalha
        pygame.draw.rect(tela, (0, 160, 255), retangulo(batalha.jogador.corpo.caixa), 1)
        pygame.draw.rect(tela, (0, 160, 255), retangulo(batalha.alvo.caixa), 1)
        for projetil in batalha.projeteis:
            pygame.draw.rect(tela, (255, 0, 200), retangulo(projetil.caixa), 1)
        estado = batalha.jogador.estado.value
        fps = self.jogo.relogio.get_fps()
        self.desenho.texto(
            tela,
            f"estado: {estado}   quadro: {batalha.quadro}   {fps:.0f} FPS",
            (20, ALTURA_TELA - 30),
            (120, 200, 255),
            self.desenho.fonte_pequena,
        )

    def _desenhar_derrota(self, tela: pygame.Surface) -> None:
        desenho = self.desenho
        desenho.escurecer(tela)
        meio = LARGURA_TELA // 2
        desenho.texto(tela, "Derrotada!", (meio, 300), Paleta.FUNDO, desenho.fonte_grande, True)
        desenho.texto(tela, "Enter, Z ou A: tentar de novo", (meio, 370), Paleta.FUNDO, centro=True)

    def _desenhar_pausa(self, tela: pygame.Surface) -> None:
        desenho = self.desenho
        desenho.escurecer(tela)
        meio = LARGURA_TELA // 2
        desenho.texto(tela, "Pausa", (meio, 240), Paleta.FUNDO, desenho.fonte_grande, True)
        self.menu_pausa.desenhar(tela, desenho, meio, 320, Paleta.FUNDO)
