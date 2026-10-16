"""Telas de derrota (I6) e de vitória (I7), com o "Você sabia?" (J15, D17).

Derrota: a barra de progresso da luta com os marcos das fases, a mensagem e "tentar de
novo" na hora. Vitória: a nota com o modo ao lado (J14), os pontos, as estatísticas e a
mensagem. As duas telas só aceitam o botão depois de um terço de segundo, para quem
terminou a luta apertando não pular a tela sem querer.
"""

from __future__ import annotations

import pygame

from cupeco.config import LARGURA_TELA
from cupeco.dominio.batalha import Batalha
from cupeco.dominio.fatos import Mensagem
from cupeco.dominio.nota import calcular_nota, desempenho_da
from cupeco.estados.base import Estado
from cupeco.estados.luta import NOMES_DOS_MODOS, Luta
from cupeco.jogo import Jogo
from cupeco.ui.desenho import APAGADO, PAPEL_CLARO, TINTA, VAZIO, Desenho
from cupeco.ui.menu import Menu

QUADROS_DE_ESPERA = 20
FUNDO_RESULTADO = (60, 50, 46)
CLARO = (234, 222, 196)
PROGRESSO = (196, 120, 60)
MEIO = LARGURA_TELA // 2


def tempo(quadros: int) -> str:
    segundos = quadros // 60
    return f"{segundos // 60}:{segundos % 60:02d}"


class EstadoResultado(Estado):
    """O que as duas telas têm em comum: a espera, o menu e a mensagem."""

    OPCOES: tuple[str, ...] = ()

    def __init__(self, jogo: Jogo, luta: Luta, batalha: Batalha, mensagem: Mensagem) -> None:
        super().__init__(jogo)
        self.luta = luta
        self.batalha = batalha
        self.mensagem = mensagem
        self.menu = Menu(self.OPCOES)
        self.espera = QUADROS_DE_ESPERA
        self.desenho = Desenho()

    def atualizar(self) -> None:
        if self.espera > 0:
            self.espera -= 1

    def tratar_evento(self, evento: pygame.Event) -> None:
        if self.espera > 0:
            return
        escolha = self.menu.tratar(evento)
        if escolha in ("Tentar de novo", "Jogar de novo"):
            from cupeco.estados.luta import EstadoLuta

            self.jogo.trocar_estado(EstadoLuta(self.jogo, self.luta.proxima()))
        elif escolha == "Trocar de modo":
            from cupeco.estados.escolha_modo import EstadoEscolhaModo

            self.jogo.trocar_estado(EstadoEscolhaModo(self.jogo, self.luta.chefe))
        elif escolha == "Sair para o título":
            from cupeco.estados.titulo import EstadoTitulo

            self.jogo.trocar_estado(EstadoTitulo(self.jogo))

    def _cabecalho(self, tela, titulo: str, y: int) -> None:
        desenho = self.desenho
        desenho.texto(tela, titulo, (MEIO, y), CLARO, desenho.fonte_grande, True)
        chefe = self.batalha.chefe.nome
        modo = NOMES_DOS_MODOS[self.luta.modo]
        desenho.texto(tela, f"{chefe} · Modo {modo}", (MEIO, y + 48), VAZIO, centro=True)

    def _desenhar_mensagem(self, tela, y: int) -> None:
        """O "Você sabia?" com a fonte, ou uma dica do jogo enquanto não há fatos (D35)."""
        desenho, mensagem = self.desenho, self.mensagem
        largura = 900
        linhas = desenho.quebrar_linhas(mensagem.texto, desenho.fonte, largura - 60)
        fonte = mensagem.fonte
        rodape = f"Fonte: {fonte.autor}, {fonte.titulo} ({fonte.ano})" if fonte else None
        altura = 70 + 30 * len(linhas) + (30 if rodape else 0)
        caixa = pygame.Rect(MEIO - largura // 2, y, largura, altura)
        pygame.draw.rect(tela, PAPEL_CLARO, caixa, border_radius=12)
        pygame.draw.rect(tela, TINTA, caixa, 3, border_radius=12)
        titulo = "Você sabia?" if mensagem.e_fato else "Dica"
        desenho.texto(tela, titulo, (caixa.x + 30, y + 16), TINTA, desenho.fonte_media)
        for indice, linha in enumerate(linhas):
            desenho.texto(tela, linha, (caixa.x + 30, y + 60 + 30 * indice))
        if rodape:
            desenho.texto(
                tela,
                rodape,
                (caixa.x + 30, y + 64 + 30 * len(linhas)),
                APAGADO,
                desenho.fonte_pequena,
            )

    def _desenhar_menu(self, tela, y: int) -> None:
        cor = CLARO if self.espera == 0 else APAGADO
        self.menu.desenhar(tela, self.desenho, MEIO, y, cor)


class EstadoDerrota(EstadoResultado):
    OPCOES = ("Tentar de novo", "Trocar de modo", "Sair para o título")

    def desenhar(self, tela: pygame.Surface) -> None:
        tela.fill(FUNDO_RESULTADO)
        self._cabecalho(tela, "Derrotada!", 70)
        self._desenhar_progresso(tela, 190)
        self._desenhar_mensagem(tela, 300)
        self._desenhar_menu(tela, 560)

    def _desenhar_progresso(self, tela, y: int) -> None:
        """Quanto da luta foi vencido, com os marcos das fases (I6)."""
        chefe, desenho = self.batalha.chefe, self.desenho
        largura, altura = 800, 28
        caixa = pygame.Rect(MEIO - largura // 2, y, largura, altura)
        pygame.draw.rect(tela, VAZIO, caixa, border_radius=8)
        feito = caixa.copy()
        feito.width = round(largura * chefe.progresso)
        if feito.width:
            pygame.draw.rect(tela, PROGRESSO, feito, border_radius=8)
        pygame.draw.rect(tela, TINTA, caixa, 3, border_radius=8)
        for numero, marco in enumerate(chefe.marcos, start=2):
            x = caixa.x + round(largura * marco)
            pygame.draw.line(tela, TINTA, (x, y - 8), (x, y + altura + 8), 4)
            desenho.texto(tela, f"Fase {numero}", (x, y - 22), CLARO, desenho.fonte_pequena, True)
        fase = chefe.fase + 1
        texto = f"Você chegou à fase {fase}: {chefe.dados_da_fase.nome}"
        desenho.texto(tela, texto, (MEIO, y + altura + 28), CLARO, centro=True)


class EstadoVitoria(EstadoResultado):
    OPCOES = ("Jogar de novo", "Sair para o título")

    def __init__(self, jogo: Jogo, luta: Luta, batalha: Batalha, mensagem: Mensagem) -> None:
        super().__init__(jogo, luta, batalha, mensagem)
        self.desempenho = desempenho_da(batalha, luta.chefe)
        self.nota = calcular_nota(self.desempenho)

    def desenhar(self, tela: pygame.Surface) -> None:
        tela.fill(FUNDO_RESULTADO)
        desenho, nota = self.desenho, self.nota
        self._cabecalho(tela, "Vitória!", 50)
        desenho.texto(
            tela, nota.letra, (MEIO - 300, 210), (250, 214, 110), desenho.fonte_enorme, True
        )
        modo = f"Modo {NOMES_DOS_MODOS[nota.modo]}"
        desenho.texto(tela, modo, (MEIO - 300, 290), VAZIO, centro=True)
        estatisticas = self.batalha.jogador.estatisticas
        linhas = (
            f"Tempo: {tempo(self.desempenho.quadros)}  ({nota.pontos_tempo} pontos)",
            f"Vida restante: {self.desempenho.vida}  ({nota.pontos_vida} pontos)",
            f"Triagens certas: {estatisticas.triagens_certas}  ({nota.pontos_triagens} pontos)",
            f"Supers: {estatisticas.supers}  ({nota.pontos_super} pontos)",
            f"Outra cor: {estatisticas.triagens_outra_cor} · "
            f"proibidas: {estatisticas.triagens_proibidas}",
            f"Total: {nota.pontos} de 100",
        )
        for indice, linha in enumerate(linhas):
            desenho.texto(tela, linha, (MEIO - 140, 150 + 32 * indice), CLARO)
        self._desenhar_mensagem(tela, 360)
        self._desenhar_menu(tela, 610)
