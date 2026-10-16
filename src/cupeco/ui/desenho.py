"""Desenho com formas simples, comum à arena de testes e à luta (até a arte da Fase 3).

Os resíduos seguem a regra de leitura sem depender de cor (I4, R3): cada um tem a cor da
CONAMA, uma sigla e, se não puder ser separado, um contorno serrilhado. Nada pisca mais
que 3 vezes por segundo (R4).
"""

from __future__ import annotations

import math

import pygame

from cupeco.config import ALTURA_TELA, LARGURA_TELA, Cor
from cupeco.dominio.fisica import Caixa, Plataforma
from cupeco.dominio.jogador import Estado as EstadoDara
from cupeco.dominio.jogador import EventoJogador, Jogador
from cupeco.dominio.materiais import Material, carregar_materiais
from cupeco.dominio.medidor import FARDOS, PONTOS_POR_FARDO
from cupeco.dominio.projeteis import VETORES, Dono, Projetil

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
PAPEL_CLARO = (250, 246, 236)
PLATAFORMA = (102, 92, 84)
TABUA = (146, 120, 88)
DARA = (74, 84, 100)
PELE = (150, 96, 64)
NEUTRO = (90, 60, 50)
VIDA = (196, 52, 48)
VAZIO = (190, 178, 156)
APAGADO = (110, 96, 84)
DESTAQUE = (250, 214, 110)  # em fundo escuro
DESTAQUE_NO_CLARO = (168, 58, 28)  # em fundo claro
SOBRE_O_CHAO = (226, 214, 190)  # texto claro sobre o chão escuro

# Invencível, a Dara some e volta 3 vezes por segundo (R4): 10 quadros de cada lado.
QUADROS_DO_PISCAR = 10


def retangulo(caixa: Caixa) -> pygame.Rect:
    return pygame.Rect(round(caixa.x), round(caixa.y), round(caixa.largura), round(caixa.altura))


def estrela(cx: float, cy: float, raio: float, pontas: int = 8) -> list[tuple[float, float]]:
    """Contorno serrilhado do que não pode ser separado.

    A interface pode usar trigonometria: só o domínio é que não usa (D23).
    """
    pontos = []
    for i in range(pontas * 2):
        angulo = math.pi * i / pontas
        r = raio if i % 2 == 0 else raio * 0.72
        pontos.append((cx + math.cos(angulo) * r, cy + math.sin(angulo) * r))
    return pontos


def mensagem_da_triagem(jogador: Jogador, eventos: list) -> tuple[str, Material] | None:
    """Explica a Triagem na hora em que ela acontece: a parte educativa da luta (D17)."""
    residuo = jogador.ultimo_residuo
    if residuo is None:
        return None
    nome = carregar_materiais()[residuo].nome
    if EventoJogador.TRIAGEM_CERTA in eventos:
        return f"{nome} na lixeira {LIXEIRAS[residuo]}: +1 fardo!", residuo
    if EventoJogador.TRIAGEM_OUTRA_COR in eventos:
        return f"{nome} é da lixeira {LIXEIRAS[residuo]}: só +½ fardo", residuo
    if EventoJogador.TRIAGEM_PROIBIDA in eventos:
        if residuo is Material.PERIGOSO:
            texto = (
                "Pilhas e baterias são resíduos perigosos: não se separam, "
                "vão para a coleta especial!"
            )
            return texto, residuo
        return "Rejeito não se separa: misturado ou contaminado, vai para o aterro", residuo
    return None


class Desenho:
    """Fontes, cores dos materiais e as formas comuns das telas de luta."""

    def __init__(self) -> None:
        # Fonte padrão do pygame até a fonte dos anos 30 com acentos chegar (Fase 3, I12).
        self.fonte = pygame.font.Font(None, 28)
        self.fonte_pequena = pygame.font.Font(None, 22)
        self.fonte_media = pygame.font.Font(None, 40)
        self.fonte_grande = pygame.font.Font(None, 64)
        self.fonte_enorme = pygame.font.Font(None, 160)
        self.fonte_sigla = pygame.font.Font(None, 24)
        self.cores = {m: carregar_materiais()[m].cor for m in Material}

    def texto(self, tela, texto, posicao, cor=TINTA, fonte=None, centro=False) -> pygame.Rect:
        superficie = (fonte or self.fonte).render(texto, True, cor)
        caixa = (
            superficie.get_rect(center=posicao) if centro else superficie.get_rect(topleft=posicao)
        )
        tela.blit(superficie, caixa)
        return caixa

    def quebrar_linhas(self, texto: str, fonte: pygame.font.Font, largura: int) -> list[str]:
        """Quebra o texto em linhas que cabem na largura."""
        linhas, atual = [], ""
        for palavra in texto.split():
            tentativa = f"{atual} {palavra}".strip()
            if atual and fonte.size(tentativa)[0] > largura:
                linhas.append(atual)
                atual = palavra
            else:
                atual = tentativa
        if atual:
            linhas.append(atual)
        return linhas

    def faixa(self, tela, texto: str, borda: Cor, y: int = 120) -> None:
        """Uma faixa clara no alto da tela, com o texto no meio."""
        superficie = self.fonte.render(texto, True, TINTA)
        fundo = superficie.get_rect(center=(LARGURA_TELA // 2, y)).inflate(28, 16)
        pygame.draw.rect(tela, PAPEL_CLARO, fundo, border_radius=10)
        pygame.draw.rect(tela, borda, fundo, 4, border_radius=10)
        tela.blit(superficie, superficie.get_rect(center=fundo.center))

    def escurecer(self, tela: pygame.Surface) -> None:
        veu = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
        veu.fill((28, 22, 20, 150))
        tela.blit(veu, (0, 0))

    # --- cena ---

    def plataformas(self, tela, plataformas: tuple[Plataforma, ...]) -> None:
        for plataforma in plataformas:
            cor = TABUA if plataforma.atravessavel else PLATAFORMA
            pygame.draw.rect(tela, cor, retangulo(plataforma.caixa))
            pygame.draw.rect(tela, TINTA, retangulo(plataforma.caixa), 3)

    def projetil(self, tela, p: Projetil) -> None:
        if p.dono is Dono.JOGADOR:
            cor = self.cores[p.material] if p.material else TINTA
            pygame.draw.rect(tela, cor, retangulo(p.caixa), border_radius=6)
            pygame.draw.rect(
                tela, PAPEL_CLARO, retangulo(p.caixa), 3 if p.ex else 2, border_radius=6
            )
            return
        raio = p.largura / 2
        if p.material is None:
            pygame.draw.circle(tela, NEUTRO, (p.x, p.y), raio * 0.8)
            pygame.draw.circle(tela, TINTA, (p.x, p.y), raio * 0.8, 3)
            return
        if p.material.separavel:
            pygame.draw.circle(tela, PAPEL_CLARO, (p.x, p.y), raio + 4)  # halo liso
        else:
            pygame.draw.polygon(tela, TINTA, estrela(p.x, p.y, raio + 10))  # serrilhado
        pygame.draw.circle(tela, self.cores[p.material], (p.x, p.y), raio)
        pygame.draw.circle(tela, TINTA, (p.x, p.y), raio, 3)
        cor_sigla = TINTA if p.material in (Material.METAL, Material.PERIGOSO) else PAPEL_CLARO
        self.texto(tela, SIGLAS[p.material], (p.x, p.y), cor_sigla, self.fonte_sigla, True)

    def dara(self, tela, jogador: Jogador, quadro: int) -> None:
        piscar = jogador.invencivel and not jogador.derrotada
        if piscar and (quadro // QUADROS_DO_PISCAR) % 2:
            return
        caixa = jogador.corpo.caixa
        cor = {
            EstadoDara.DANO: VIDA,
            EstadoDara.DERROTADA: APAGADO,
            EstadoDara.SUPER: (240, 214, 150),
        }.get(jogador.estado, DARA)
        pygame.draw.rect(tela, cor, retangulo(caixa), border_radius=14)
        pygame.draw.rect(tela, TINTA, retangulo(caixa), 3, border_radius=14)
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
            pygame.draw.circle(tela, PAPEL_CLARO, (round(cx), round(caixa.centro[1])), 70, 4)

    def hud(self, tela, jogador: Jogador) -> None:
        """Vida, os 5 fardos do Medidor, a arma ativa e as triagens (I3)."""
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
        self.texto(tela, f"{arma.nome}  (lixeira {LIXEIRAS[arma.material]})", (386, 22))
        e = jogador.estatisticas
        self.texto(
            tela,
            f"Triagens: {e.triagens_certas} certas · {e.triagens_outra_cor} outra cor · "
            f"{e.triagens_proibidas} proibidas",
            (20, 56),
            APAGADO,
            self.fonte_pequena,
        )

    def ajuda(self, tela, texto: str, acima: bool = False) -> None:
        """Linha de ajuda dos controles, sobre o chão."""
        y = ALTURA_TELA - 58 if acima else ALTURA_TELA - 30
        self.texto(tela, texto, (20, y), SOBRE_O_CHAO, self.fonte_pequena)
