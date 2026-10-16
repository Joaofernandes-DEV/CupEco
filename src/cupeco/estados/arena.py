"""Arena de testes (J7, I8): a primeira tela jogável, com formas simples no lugar da arte.

Serve para jogar e ajustar o movimento, os tiros e a Triagem antes da arte final (Fase 3).
Os resíduos já seguem a regra de leitura sem depender de cor (I4, R3): cada um tem a cor
da CONAMA, uma sigla e, se não puder ser separado, um contorno serrilhado.

Teclas extras: Esc (ou Start) pausa; F1 mostra as caixas de colisão.
"""

from __future__ import annotations

import math
from collections.abc import Callable

import pygame

from cupeco.config import ALTURA_TELA, LARGURA_TELA, Paleta
from cupeco.dominio.batalha import Batalha
from cupeco.dominio.comandos import Comandos
from cupeco.dominio.fisica import Caixa
from cupeco.dominio.jogador import Estado as EstadoDara
from cupeco.dominio.jogador import EventoJogador
from cupeco.dominio.materiais import Material, carregar_materiais
from cupeco.dominio.medidor import FARDOS, PONTOS_POR_FARDO
from cupeco.dominio.projeteis import VETORES, Dono, Projetil
from cupeco.estados.base import Estado
from cupeco.jogo import Jogo
from cupeco.ui.entrada import e_pausa

SEMENTE_PADRAO = 1930

SIGLAS = {
    Material.PAPEL: "Pa",
    Material.PLASTICO: "Pl",
    Material.VIDRO: "Vi",
    Material.METAL: "Me",
    Material.REJEITO: "Re",
    Material.PERIGOSO: "!",
}
LIXEIRAS = {
    Material.PAPEL: "azul",
    Material.PLASTICO: "vermelha",
    Material.VIDRO: "verde",
    Material.METAL: "amarela",
}

TINTA = (28, 22, 20)
FUNDO = (226, 210, 178)
PLATAFORMA = (102, 92, 84)
TABUA = (146, 120, 88)
BONECO = (170, 150, 120)
DARA = (74, 84, 100)
PELE = (150, 96, 64)
NEUTRO = (90, 60, 50)
VIDA = (196, 52, 48)
VAZIO = (190, 178, 156)
APAGADO = (110, 96, 84)
SOBRE_O_CHAO = (226, 214, 190)  # texto claro sobre o chão escuro

OPCOES_PAUSA = ("Continuar", "Reiniciar", "Sair para o título")
QUADROS_AVISO = 120


def _rect(caixa: Caixa) -> pygame.Rect:
    return pygame.Rect(round(caixa.x), round(caixa.y), round(caixa.largura), round(caixa.altura))


def _estrela(cx: float, cy: float, raio: float, pontas: int = 8) -> list[tuple[float, float]]:
    """Contorno serrilhado dos resíduos que não podem ser separados.

    A interface pode usar trigonometria: só o domínio é que não usa (D23).
    """
    pontos = []
    for i in range(pontas * 2):
        angulo = math.pi * i / pontas
        r = raio if i % 2 == 0 else raio * 0.72
        pontos.append((cx + math.cos(angulo) * r, cy + math.sin(angulo) * r))
    return pontos


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
        self.opcao = 0
        self.aviso: tuple[str, tuple[int, int, int], int] | None = None
        self.cores = {m: carregar_materiais()[m].cor for m in Material}
        self.fonte = pygame.font.Font(None, 28)
        self.fonte_pequena = pygame.font.Font(None, 22)
        self.fonte_grande = pygame.font.Font(None, 64)
        self.fonte_sigla = pygame.font.Font(None, 24)

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
            self.opcao = 0
            return
        confirmar = (
            evento.type == pygame.KEYDOWN and evento.key in (pygame.K_RETURN, pygame.K_z)
        ) or (
            evento.type == pygame.CONTROLLERBUTTONDOWN
            and evento.button == pygame.CONTROLLER_BUTTON_A
        )
        if self.pausa_aberta:
            self._navegar_pausa(evento, confirmar)
        elif self.batalha.jogador.derrotada and confirmar:
            self.reiniciar()

    def _navegar_pausa(self, evento: pygame.Event, confirmar: bool) -> None:
        cima = (evento.type == pygame.KEYDOWN and evento.key == pygame.K_UP) or (
            evento.type == pygame.CONTROLLERBUTTONDOWN
            and evento.button == pygame.CONTROLLER_BUTTON_DPAD_UP
        )
        baixo = (evento.type == pygame.KEYDOWN and evento.key == pygame.K_DOWN) or (
            evento.type == pygame.CONTROLLERBUTTONDOWN
            and evento.button == pygame.CONTROLLER_BUTTON_DPAD_DOWN
        )
        if cima:
            self.opcao = (self.opcao - 1) % len(OPCOES_PAUSA)
        elif baixo:
            self.opcao = (self.opcao + 1) % len(OPCOES_PAUSA)
        elif confirmar:
            escolha = OPCOES_PAUSA[self.opcao]
            if escolha == "Continuar":
                self.pausa_aberta = False
            elif escolha == "Reiniciar":
                self.reiniciar()
            else:
                from cupeco.estados.titulo import EstadoTitulo

                self.jogo.trocar_estado(EstadoTitulo(self.jogo))

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
        jogador = self.batalha.jogador
        residuo = jogador.ultimo_residuo
        if residuo is None:
            return
        nome = carregar_materiais()[residuo].nome
        if EventoJogador.TRIAGEM_CERTA in eventos:
            texto = f"{nome} na lixeira {LIXEIRAS[residuo]}: +1 fardo!"
        elif EventoJogador.TRIAGEM_OUTRA_COR in eventos:
            texto = f"{nome} é da lixeira {LIXEIRAS[residuo]}: só +½ fardo"
        elif EventoJogador.TRIAGEM_PROIBIDA in eventos:
            if residuo is Material.PERIGOSO:
                texto = "Pilha é resíduo perigoso: não se separa, vai para coleta especial!"
            else:
                texto = "Rejeito não se separa: misturado ou contaminado, vai para o aterro"
        else:
            return
        self.aviso = (texto, self.cores[residuo], QUADROS_AVISO)

    # --- desenho ---------------------------------------------------------------------

    def desenhar(self, tela: pygame.Surface) -> None:
        tela.fill(FUNDO)
        batalha = self.batalha
        for plataforma in batalha.plataformas:
            cor = TABUA if plataforma.atravessavel else PLATAFORMA
            pygame.draw.rect(tela, cor, _rect(plataforma.caixa))
            pygame.draw.rect(tela, TINTA, _rect(plataforma.caixa), 3)
        self._desenhar_boneco(tela)
        for projetil in batalha.projeteis:
            self._desenhar_projetil(tela, projetil)
        self._desenhar_dara(tela)
        if self.mostrar_caixas:
            self._desenhar_caixas(tela)
        self._desenhar_hud(tela)
        if batalha.jogador.derrotada:
            self._desenhar_derrota(tela)
        if self.pausa_aberta:
            self._desenhar_pausa(tela)

    def _texto(self, tela, texto, posicao, cor=TINTA, fonte=None, centro=False) -> None:
        superficie = (fonte or self.fonte).render(texto, True, cor)
        retangulo = (
            superficie.get_rect(center=posicao) if centro else superficie.get_rect(topleft=posicao)
        )
        tela.blit(superficie, retangulo)

    def _desenhar_boneco(self, tela: pygame.Surface) -> None:
        alvo = self.batalha.alvo
        pygame.draw.rect(tela, BONECO, _rect(alvo.caixa), border_radius=18)
        pygame.draw.rect(tela, TINTA, _rect(alvo.caixa), 3, border_radius=18)
        cx, _ = alvo.caixa.centro
        self._texto(tela, "boneco", (cx, alvo.caixa.y + 30), centro=True, fonte=self.fonte_pequena)
        self._texto(tela, str(alvo.dano_recebido), (cx, alvo.caixa.y + 70), centro=True)

    def _desenhar_projetil(self, tela: pygame.Surface, p: Projetil) -> None:
        if p.dono is Dono.JOGADOR:
            cor = self.cores[p.material] if p.material else TINTA
            pygame.draw.rect(tela, cor, _rect(p.caixa), border_radius=6)
            pygame.draw.rect(
                tela, (250, 246, 236), _rect(p.caixa), 3 if p.ex else 2, border_radius=6
            )
            return
        raio = p.largura / 2
        if p.material is None:
            pygame.draw.circle(tela, NEUTRO, (p.x, p.y), raio * 0.8)
            pygame.draw.circle(tela, TINTA, (p.x, p.y), raio * 0.8, 3)
            return
        if p.material.separavel:
            pygame.draw.circle(tela, (250, 246, 236), (p.x, p.y), raio + 4)  # halo liso
        else:
            pygame.draw.polygon(tela, TINTA, _estrela(p.x, p.y, raio + 10))  # serrilhado
        pygame.draw.circle(tela, self.cores[p.material], (p.x, p.y), raio)
        pygame.draw.circle(tela, TINTA, (p.x, p.y), raio, 3)
        cor_sigla = TINTA if p.material in (Material.METAL, Material.PERIGOSO) else (250, 246, 236)
        self._texto(tela, SIGLAS[p.material], (p.x, p.y), cor_sigla, self.fonte_sigla, True)

    def _desenhar_dara(self, tela: pygame.Surface) -> None:
        jogador = self.batalha.jogador
        piscar = jogador.invencivel and not jogador.derrotada and (self.batalha.quadro // 4) % 2
        if piscar:
            return
        caixa = jogador.corpo.caixa
        cor = {
            EstadoDara.DANO: VIDA,
            EstadoDara.DERROTADA: APAGADO,
            EstadoDara.SUPER: (240, 214, 150),
        }.get(jogador.estado, DARA)
        pygame.draw.rect(tela, cor, _rect(caixa), border_radius=14)
        pygame.draw.rect(tela, TINTA, _rect(caixa), 3, border_radius=14)
        # Cabeça e o lado para onde olha.
        cx, _ = caixa.centro
        cabeca = (cx + jogador.virada * 6, caixa.y + 22)
        pygame.draw.circle(tela, PELE, cabeca, 18)
        pygame.draw.circle(tela, TINTA, cabeca, 18, 3)
        pygame.draw.circle(tela, TINTA, (cabeca[0] + jogador.virada * 9, cabeca[1] - 2), 4)
        # Canhão: linha na direção da mira, na cor da lixeira ativa (D12).
        material = jogador.arsenal.ativa.material
        dx, dy = VETORES[jogador.mira]
        origem = caixa.centro
        ponta = (
            origem[0] + dx * jogador.p.distancia_boca,
            origem[1] + dy * jogador.p.distancia_boca,
        )
        pygame.draw.line(tela, TINTA, origem, ponta, 14)
        pygame.draw.line(tela, self.cores[material], origem, ponta, 8)
        if jogador.em_triagem:
            pygame.draw.circle(tela, (250, 246, 236), (round(cx), round(caixa.centro[1])), 70, 4)

    def _desenhar_caixas(self, tela: pygame.Surface) -> None:
        batalha = self.batalha
        pygame.draw.rect(tela, (0, 160, 255), _rect(batalha.jogador.corpo.caixa), 1)
        pygame.draw.rect(tela, (0, 160, 255), _rect(batalha.alvo.caixa), 1)
        for projetil in batalha.projeteis:
            pygame.draw.rect(tela, (255, 0, 200), _rect(projetil.caixa), 1)
        estado = batalha.jogador.estado.value
        fps = self.jogo.relogio.get_fps()
        self._texto(
            tela,
            f"estado: {estado}   quadro: {batalha.quadro}   {fps:.0f} FPS",
            (20, ALTURA_TELA - 30),
            (120, 200, 255),
            self.fonte_pequena,
        )

    def _desenhar_hud(self, tela: pygame.Surface) -> None:
        jogador = self.batalha.jogador
        for i in range(jogador.p.vida_maxima):
            cor = VIDA if i < jogador.vida else VAZIO
            pygame.draw.rect(tela, cor, (20 + i * 34, 20, 26, 26), border_radius=5)
            pygame.draw.rect(tela, TINTA, (20 + i * 34, 20, 26, 26), 3, border_radius=5)
        pontos = jogador.medidor.pontos
        for i in range(FARDOS):
            x = 140 + i * 40
            pygame.draw.rect(tela, VAZIO, (x, 20, 32, 26), border_radius=4)
            cheio = min(PONTOS_POR_FARDO, max(0, pontos - i * PONTOS_POR_FARDO))
            if cheio:
                altura = round(26 * cheio / PONTOS_POR_FARDO)
                pygame.draw.rect(tela, (86, 150, 70), (x, 46 - altura, 32, altura), border_radius=4)
            pygame.draw.rect(tela, TINTA, (x, 20, 32, 26), 3, border_radius=4)
        arma = jogador.arsenal.ativa
        pygame.draw.circle(tela, self.cores[arma.material], (365, 33), 13)
        pygame.draw.circle(tela, TINTA, (365, 33), 13, 3)
        self._texto(tela, f"{arma.nome}  (lixeira {LIXEIRAS[arma.material]})", (386, 22))
        e = jogador.estatisticas
        self._texto(
            tela,
            f"Triagens: {e.triagens_certas} certas · {e.triagens_outra_cor} outra cor · "
            f"{e.triagens_proibidas} proibidas",
            (20, 56),
            APAGADO,
            self.fonte_pequena,
        )
        self._texto(
            tela,
            "Setas: mover  Z: pulo/Triagem  X: tiro  C: dash  V: EX/Super  Shift: travar  "
            "Tab: trocar  Esc: pausa  F1: caixas",
            (20, ALTURA_TELA - 58 if self.mostrar_caixas else ALTURA_TELA - 30),
            SOBRE_O_CHAO,
            self.fonte_pequena,
        )
        if self.aviso is not None:
            texto, cor, _ = self.aviso
            superficie = self.fonte.render(texto, True, TINTA)
            fundo = superficie.get_rect(center=(LARGURA_TELA // 2, 120)).inflate(28, 16)
            pygame.draw.rect(tela, (250, 246, 236), fundo, border_radius=10)
            pygame.draw.rect(tela, cor, fundo, 4, border_radius=10)
            tela.blit(superficie, superficie.get_rect(center=fundo.center))

    def _escurecer(self, tela: pygame.Surface) -> None:
        veu = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
        veu.fill((28, 22, 20, 150))
        tela.blit(veu, (0, 0))

    def _desenhar_derrota(self, tela: pygame.Surface) -> None:
        self._escurecer(tela)
        meio = LARGURA_TELA // 2
        self._texto(tela, "Derrotada!", (meio, 300), Paleta.FUNDO, self.fonte_grande, True)
        self._texto(tela, "Enter, Z ou A: tentar de novo", (meio, 370), Paleta.FUNDO, centro=True)

    def _desenhar_pausa(self, tela: pygame.Surface) -> None:
        self._escurecer(tela)
        meio = LARGURA_TELA // 2
        self._texto(tela, "Pausa", (meio, 240), Paleta.FUNDO, self.fonte_grande, True)
        for indice, opcao in enumerate(OPCOES_PAUSA):
            marcada = indice == self.opcao
            texto = f"> {opcao} <" if marcada else opcao
            cor = (250, 214, 110) if marcada else Paleta.FUNDO
            self._texto(tela, texto, (meio, 320 + indice * 46), cor, centro=True)
