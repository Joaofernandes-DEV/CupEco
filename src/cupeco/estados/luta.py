"""A luta contra um chefe (J8, I5, D33), com formas simples até a arte da Fase 3.

A vida do chefe não aparece na tela (D33): o avanço se vê nas trocas de fase, anunciadas
numa faixa. Todo ataque tem aviso visual antes de acontecer (I5); o aviso sonoro chega
com os sons, na Fase 3. Nada pisca mais que 3 vezes por segundo (R4): os avisos são
contornos fixos.

Cada tentativa usa uma semente nova (a da luta mais o número da tentativa), então os
ataques variam e a luta continua reproduzível.

Esc (ou Start) pausa. Com `--depurar`: F1 mostra as caixas e a vida do chefe; F2 pula
para a próxima fase.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace

import pygame

from cupeco.config import ALTURA_TELA, LARGURA_TELA, Paleta
from cupeco.dominio.ataques import TipoAtaque
from cupeco.dominio.batalha import Batalha, Resultado, carregar_arena
from cupeco.dominio.chefe import Chefe, EventoChefe, carregar_chefe
from cupeco.dominio.comandos import Comandos
from cupeco.dominio.materiais import Material
from cupeco.dominio.modos import Modo
from cupeco.estados.base import Estado
from cupeco.jogo import Jogo
from cupeco.ui.desenho import (
    APAGADO,
    FUNDO,
    PAPEL_CLARO,
    TINTA,
    Desenho,
    estrela,
    mensagem_da_triagem,
    retangulo,
)
from cupeco.ui.entrada import e_pausa
from cupeco.ui.menu import Menu

CHEFE_PADRAO = "dom_obsolescencio"
SEMENTE_PADRAO = 1930
NOMES_DOS_MODOS = {Modo.NORMAL: "Normal", Modo.SIMPLES: "Simples"}

OPCOES_PAUSA = ("Continuar", "Reiniciar", "Sair para o título")
QUADROS_FAIXA = 150
QUADROS_ATE_O_RESULTADO = 30  # meio segundo para ver o que aconteceu
AJUDA = (
    "Setas: mover  Z: pulo/Triagem  X: tiro  C: dash  V: EX/Super  Shift: travar  "
    "Tab: trocar  Esc: pausa"
)

CORES_DAS_FASES = ((112, 98, 136), (70, 112, 128), (64, 116, 76))
ALERTA = (214, 92, 40)
ELETRICO = (250, 214, 110)
BARRA = (132, 84, 168)
CELULAR = (52, 56, 64)


@dataclass(frozen=True)
class Luta:
    """Qual luta jogar: o chefe, o modo, a semente e o número da tentativa."""

    chefe: str = CHEFE_PADRAO
    modo: Modo = Modo.NORMAL
    semente: int = SEMENTE_PADRAO
    tentativa: int = 1

    @property
    def semente_da_tentativa(self) -> int:
        return self.semente + self.tentativa - 1

    def proxima(self) -> Luta:
        return replace(self, tentativa=self.tentativa + 1)


def tracejado(tela: pygame.Surface, caixa: pygame.Rect, cor, largura: int = 4) -> None:
    """Contorno tracejado: a área de um ataque que ainda vai acontecer."""
    passo = 18
    for x in range(caixa.left, caixa.right, passo * 2):
        fim = min(x + passo, caixa.right)
        pygame.draw.line(tela, cor, (x, caixa.top), (fim, caixa.top), largura)
        pygame.draw.line(tela, cor, (x, caixa.bottom), (fim, caixa.bottom), largura)
    for y in range(caixa.top, caixa.bottom, passo * 2):
        fim = min(y + passo, caixa.bottom)
        pygame.draw.line(tela, cor, (caixa.left, y), (caixa.left, fim), largura)
        pygame.draw.line(tela, cor, (caixa.right, y), (caixa.right, fim), largura)


class EstadoLuta(Estado):
    def __init__(
        self,
        jogo: Jogo,
        luta: Luta | None = None,
        leitor: Callable[[], Comandos] | None = None,
    ) -> None:
        super().__init__(jogo)
        self.luta = luta or Luta()
        self._ler = leitor or jogo.entrada.ler
        dados = carregar_chefe(self.luta.chefe)
        self.batalha = Batalha(
            self.luta.semente_da_tentativa, carregar_arena(dados.arena), dados, self.luta.modo
        )
        self.desenho = Desenho()
        self.menu_pausa = Menu(OPCOES_PAUSA)
        self.pausa_aberta = False
        self.mostrar_caixas = False
        self.faixa: tuple[str, tuple[int, int, int], int] | None = None
        self.aviso: tuple[str, tuple[int, int, int], int] | None = None
        self._fim = 0
        solidas = [p.caixa.y for p in self.batalha.plataformas if not p.atravessavel]
        self._chao = min(y for y in solidas if y > 0)

    @property
    def chefe(self) -> Chefe:
        return self.batalha.chefe

    # --- eventos ---------------------------------------------------------------------

    def tratar_evento(self, evento: pygame.Event) -> None:
        if self.jogo.depurar and evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_F1:
                self.mostrar_caixas = not self.mostrar_caixas
                return
            if evento.key == pygame.K_F2:
                self._reagir(self.chefe.levar_dano(self.chefe.vida))  # para no limite da fase
                return
        if e_pausa(evento):
            self.pausa_aberta = not self.pausa_aberta
            self.menu_pausa.indice = 0
            return
        if not self.pausa_aberta:
            return
        escolha = self.menu_pausa.tratar(evento)
        if escolha == "Continuar":
            self.pausa_aberta = False
        elif escolha == "Reiniciar":
            self.jogo.trocar_estado(EstadoLuta(self.jogo, self.luta.proxima(), self._ler))
        elif escolha == "Sair para o título":
            from cupeco.estados.titulo import EstadoTitulo

            self.jogo.trocar_estado(EstadoTitulo(self.jogo))

    # --- lógica ----------------------------------------------------------------------

    def atualizar(self) -> None:
        if self.pausa_aberta:
            return
        if self.batalha.resultado is not None:
            self._fim += 1
            if self._fim >= QUADROS_ATE_O_RESULTADO:
                self._mostrar_resultado()
            return
        eventos = self.batalha.atualizar(self._ler())
        self._reagir(eventos)
        self.faixa = self._contar(self.faixa)
        self.aviso = self._contar(self.aviso)

    @staticmethod
    def _contar(aviso):
        if aviso is None:
            return None
        texto, cor, quadros = aviso
        return (texto, cor, quadros - 1) if quadros > 1 else None

    def _reagir(self, eventos: list) -> None:
        chefe = self.chefe
        if EventoChefe.MUDOU_FASE in eventos:
            nome = chefe.dados_da_fase.nome
            cor = CORES_DAS_FASES[chefe.fase % len(CORES_DAS_FASES)]
            self.faixa = (f"Fase {chefe.fase + 1}: {nome}", cor, QUADROS_FAIXA)
        if EventoChefe.CUROU in eventos:
            self.faixa = ("Atualização instalada! O Dom se recuperou um pouco.", BARRA, 120)
        mensagem = mensagem_da_triagem(self.batalha.jogador, eventos)
        if mensagem is not None:
            texto, residuo = mensagem
            self.aviso = (texto, self.desenho.cores[residuo], 120)

    def _mostrar_resultado(self) -> None:
        from cupeco.estados.resultado import EstadoDerrota, EstadoVitoria

        mensagem = self.jogo.fatos.proxima(self.luta.chefe)
        if self.batalha.resultado is Resultado.VITORIA:
            self.jogo.trocar_estado(EstadoVitoria(self.jogo, self.luta, self.batalha, mensagem))
        else:
            self.jogo.trocar_estado(EstadoDerrota(self.jogo, self.luta, self.batalha, mensagem))

    # --- desenho ---------------------------------------------------------------------

    def desenhar(self, tela: pygame.Surface) -> None:
        tela.fill(FUNDO)
        batalha, desenho = self.batalha, self.desenho
        desenho.plataformas(tela, batalha.plataformas)
        self._desenhar_avisos(tela)
        self._desenhar_perigos(tela)
        self._desenhar_chefe(tela)
        self._desenhar_barra(tela)
        for inimigo in batalha.inimigos:
            caixa = retangulo(inimigo.caixa)
            pygame.draw.rect(tela, CELULAR, caixa, border_radius=8)
            pygame.draw.rect(tela, (150, 190, 200), caixa.inflate(-14, -18), border_radius=3)
            pygame.draw.rect(tela, TINTA, caixa, 3, border_radius=8)
        # O que cai do alto e não explode some ao chegar ao chão (não aparece atravessando).
        tela.set_clip(pygame.Rect(0, 0, LARGURA_TELA, round(self._chao)))
        for projetil in batalha.projeteis:
            desenho.projetil(tela, projetil)
        tela.set_clip(None)
        desenho.dara(tela, batalha.jogador, batalha.quadro)
        desenho.hud(tela, batalha.jogador)
        self._desenhar_nome(tela)
        desenho.ajuda(tela, AJUDA, acima=self.mostrar_caixas)
        if self.faixa is not None:
            texto, cor, _ = self.faixa
            desenho.faixa(tela, texto, cor, y=250)
        if self.aviso is not None:
            texto, cor, _ = self.aviso
            desenho.faixa(tela, texto, cor, y=120)
        if self.mostrar_caixas:
            self._desenhar_caixas(tela)
        if self.pausa_aberta:
            desenho.escurecer(tela)
            meio = LARGURA_TELA // 2
            desenho.texto(tela, "Pausa", (meio, 240), Paleta.FUNDO, desenho.fonte_grande, True)
            self.menu_pausa.desenhar(tela, desenho, meio, 320, Paleta.FUNDO)

    def _desenhar_nome(self, tela: pygame.Surface) -> None:
        """Chefe, fase e modo no alto, à direita (sem a vida do chefe, D33)."""
        chefe, desenho = self.chefe, self.desenho
        nome = f"{chefe.nome} · {chefe.dados_da_fase.nome}"
        caixa = desenho.fonte.render(nome, True, TINTA).get_rect(topright=(LARGURA_TELA - 20, 22))
        desenho.texto(tela, nome, caixa.topleft)
        modo = f"Modo {NOMES_DOS_MODOS[self.luta.modo]}"
        caixa = desenho.fonte_pequena.render(modo, True, APAGADO).get_rect(
            topright=(LARGURA_TELA - 20, 52)
        )
        desenho.texto(tela, modo, caixa.topleft, APAGADO, desenho.fonte_pequena)

    def _desenhar_avisos(self, tela: pygame.Surface) -> None:
        """O que ainda vai acontecer: contornos e marcas fixas, sem piscar (I5, R4)."""
        chefe, roteiro = self.chefe, self.chefe.roteiro
        zona = chefe.zona_avisada
        if zona is not None:
            tracejado(tela, retangulo(zona), ALERTA)
            self.desenho.texto(
                tela, "!", retangulo(zona).center, ALERTA, self.desenho.fonte_media, True
            )
        barra = roteiro.barra_avisada
        if barra is not None:
            tracejado(tela, retangulo(barra), BARRA)
        ataque = roteiro.atual
        if chefe.em_aviso and ataque is not None and ataque.tipo is TipoAtaque.CHUVA:
            material = ataque.materiais[0]
            cor = self.desenho.cores[Material(material)] if material != "comum" else ALERTA
            for x in roteiro.pontos_da_chuva:
                pygame.draw.polygon(tela, cor, [(x - 14, 72), (x + 14, 72), (x, 94)])
                pygame.draw.polygon(tela, TINTA, [(x - 14, 72), (x + 14, 72), (x, 94)], 3)
                if ataque.explosao is not None:
                    largura, altura, _ = ataque.explosao
                    area = pygame.Rect(
                        round(x - largura / 2),
                        round(self._chao - altura),
                        round(largura),
                        round(altura),
                    )
                    tracejado(tela, area, ALERTA, 3)
                else:
                    pygame.draw.ellipse(tela, cor, (x - 24, self._chao - 8, 48, 12), 3)

    def _desenhar_perigos(self, tela: pygame.Surface) -> None:
        zona = self.chefe.zona_ativa
        if zona is not None:
            caixa = retangulo(zona)
            pygame.draw.rect(tela, ELETRICO, caixa)
            for x in range(caixa.left, caixa.right, 40):
                meio = caixa.centery
                pontos = [(x, caixa.top + 4), (x + 12, meio), (x + 24, caixa.bottom - 4)]
                pygame.draw.lines(tela, ALERTA, False, pontos, 4)
            pygame.draw.rect(tela, TINTA, caixa, 3)
        cor = self.desenho.cores[Material.PERIGOSO]
        for explosao in self.batalha.explosoes:
            caixa = retangulo(explosao.caixa)
            cx, cy = caixa.center
            pygame.draw.polygon(tela, TINTA, estrela(cx, cy, caixa.height * 0.75, 10))
            pygame.draw.polygon(tela, cor, estrela(cx, cy, caixa.height * 0.62, 10))

    def _desenhar_chefe(self, tela: pygame.Surface) -> None:
        chefe = self.chefe
        if chefe.derrotado:
            return
        caixa = retangulo(chefe.caixa)
        cor = CORES_DAS_FASES[chefe.fase % len(CORES_DAS_FASES)]
        if chefe.em_transicao:
            cor = tuple((c + 255) // 2 for c in cor)  # mais claro: não leva dano agora
        if chefe.fase == 0:  # Torre de Tubos: TVs empilhadas
            altura = caixa.height // 3
            for i in range(3):
                tv = pygame.Rect(caixa.x, caixa.y + i * altura, caixa.width, altura)
                pygame.draw.rect(tela, cor, tv, border_radius=12)
                pygame.draw.rect(tela, (150, 190, 200), tv.inflate(-40, -36), border_radius=16)
                pygame.draw.rect(tela, TINTA, tv, 3, border_radius=12)
        elif chefe.fase == 1:  # Enxame Descontinuado: um núcleo redondo
            pygame.draw.ellipse(tela, cor, caixa)
            pygame.draw.ellipse(tela, TINTA, caixa, 3)
            pygame.draw.line(tela, TINTA, caixa.midtop, (caixa.centerx + 20, caixa.top - 30), 4)
        else:  # Placa-Mãe: placa com trilhas e chips
            pygame.draw.rect(tela, cor, caixa, border_radius=6)
            for y in range(caixa.top + 20, caixa.bottom - 10, 24):
                pygame.draw.line(tela, ELETRICO, (caixa.left + 10, y), (caixa.right - 10, y), 2)
            for x in range(caixa.left + 30, caixa.right - 30, 70):
                pygame.draw.rect(tela, TINTA, (x, caixa.centery - 14, 34, 28))
            pygame.draw.rect(tela, TINTA, caixa, 3, border_radius=6)
        if chefe.em_aviso:
            # O chefe vai atacar: um "!" fixo sobre ele (I5).
            centro = (caixa.centerx, max(30, caixa.top - 30))
            pygame.draw.circle(tela, PAPEL_CLARO, centro, 22)
            pygame.draw.circle(tela, ALERTA, centro, 22, 4)
            self.desenho.texto(tela, "!", centro, ALERTA, self.desenho.fonte_media, True)

    def _desenhar_barra(self, tela: pygame.Surface) -> None:
        roteiro, desenho = self.chefe.roteiro, self.desenho
        area = roteiro.barra_avisada
        barra = self.chefe.barra
        if barra is not None:
            area = barra.caixa
            caixa = retangulo(area)
            pygame.draw.rect(tela, PAPEL_CLARO, caixa)
            cheia = caixa.copy()
            cheia.width = round(caixa.width * roteiro.progresso_da_barra)
            pygame.draw.rect(tela, BARRA, cheia)
            pygame.draw.rect(tela, TINTA, caixa, 3)
            porcentagem = round(100 * roteiro.progresso_da_barra)
            desenho.texto(tela, f"{porcentagem}%", caixa.center, TINTA, desenho.fonte_pequena, True)
        if area is not None:
            caixa = retangulo(area)
            desenho.texto(
                tela,
                "Atualização Obrigatória",
                (caixa.centerx, caixa.top - 16),
                BARRA,
                desenho.fonte_pequena,
                True,
            )

    def _desenhar_caixas(self, tela: pygame.Surface) -> None:
        """Só com --depurar: caixas de colisão e a vida do chefe."""
        batalha, chefe = self.batalha, self.chefe
        pygame.draw.rect(tela, (0, 160, 255), retangulo(batalha.jogador.corpo.caixa), 1)
        pygame.draw.rect(tela, (0, 160, 255), retangulo(chefe.caixa), 1)
        for projetil in batalha.projeteis:
            pygame.draw.rect(tela, (255, 0, 200), retangulo(projetil.caixa), 1)
        ataque = chefe.roteiro.atual.nome if chefe.roteiro.atual else "-"
        fps = self.jogo.relogio.get_fps()
        self.desenho.texto(
            tela,
            f"vida do chefe: {chefe.vida}/{chefe.dados.vida}   fase: {chefe.fase + 1}   "
            f"ataque: {ataque}   quadro: {batalha.quadro}   {fps:.0f} FPS   F2: pular fase",
            (20, ALTURA_TELA - 30),
            (120, 200, 255),
            self.desenho.fonte_pequena,
        )
