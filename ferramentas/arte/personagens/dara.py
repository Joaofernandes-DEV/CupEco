"""Dara, catadora de 16 anos (D16): desenho em estilo rubber hose, original (D11, I1).

Diferenças de propósito em relação aos clássicos do gênero: luvas de trabalho amarelas em
vez das luvas brancas, boné da cooperativa e macacão de trabalho. Coordenadas locais com a
origem no chão, sob o corpo; y negativo para cima; ela olha para a direita.
"""

from __future__ import annotations

from dataclasses import dataclass

from ferramentas.arte import paleta
from ferramentas.arte.personagens.canhao import desenhar_canhao
from ferramentas.arte.traco import Pincel, Ponto, deslocar, direcao, girar, oval

LARGURA_PERNA = 15
LARGURA_BRACO = 11


@dataclass(frozen=True)
class Pose:
    """Esqueleto de uma pose: cada membro é uma curva pelas âncoras (sem cotovelo)."""

    quadril: Ponto
    peito: Ponto
    cabeca: Ponto
    perna_tras: tuple[Ponto, Ponto, Ponto]
    perna_frente: tuple[Ponto, Ponto, Ponto]
    braco_tras: tuple[Ponto, Ponto, Ponto]
    braco_frente: tuple[Ponto, Ponto, Ponto]
    canhao: Ponto  # direção para onde o canhão aponta
    bota_tras: Ponto = (1.0, 0.0)  # direção da ponta da bota
    bota_frente: Ponto = (1.0, 0.0)
    cabelo_vento: float = 0.0  # quanto o cabelo vai para trás (corrida, pulo)
    boca_aberta: bool = False


# --- partes (coordenadas relativas a cada parte) --------------------------------------

_LUVA = [(-7, -8), (2, -11), (10, -12), (17, -6), (18, 3), (12, 10), (2, 10), (-7, 8)]
_POLEGAR = [(2, -9), (6, -17), (12, -16), (11, -9)]
_PUNHO = [(-12, -11), (-4, -9), (-4, 9), (-12, 11), (-14, 0)]

_BOTA = [(-16, 0), (-17, -20), (-9, -28), (6, -27), (11, -17), (24, -16), (34, -9), (33, 0)]
# Solado: uma faixa escura acompanhando o fundo da bota, com salto mais grosso.
_SOLA = [(-17, -7), (-4, -7), (2, -5), (33, -5), (34, 0), (33, 2), (-17, 2)]

_CABECA = [
    (-36, -14),
    (-24, -36),
    (2, -42),
    (28, -34),
    (42, -12),
    (44, 14),
    (30, 36),
    (2, 40),
    (-26, 32),
    (-38, 10),
]
_BONE = [(-38, -10), (-34, -34), (-12, -50), (16, -48), (36, -30), (40, -14), (10, -18)]
_ABA = [(26, -20), (52, -22), (70, -16), (66, -8), (34, -10)]
_BOCA = [(22, 18), (34, 21), (46, 15), (44, 26), (34, 33), (25, 27)]
_LINGUA = [(28, 27), (35, 24), (41, 26), (35, 31)]
_TUFOS = [((-30, -24), 22), ((-42, -2), 19), ((-14, -40), 18), ((-36, 18), 14)]


def _luva(pincel: Pincel, mao: Ponto, eixo: Ponto) -> None:
    pincel.forma(girar(_PUNHO, eixo, mao), paleta.LUVA_PUNHO, contorno=2.5)
    pincel.forma(girar(_POLEGAR, eixo, mao), paleta.LUVA, contorno=2.5)
    pincel.forma(girar(_LUVA, eixo, mao), paleta.LUVA, contorno=2.8)


def _braco(pincel: Pincel, ancoras: tuple[Ponto, Ponto, Ponto]) -> None:
    pincel.mangueira(ancoras, LARGURA_BRACO, paleta.PELE, contorno=2.6)
    _luva(pincel, ancoras[2], direcao(ancoras[1], ancoras[2]))


def _perna(pincel: Pincel, ancoras: tuple[Ponto, Ponto, Ponto], eixo_bota: Ponto) -> None:
    pe = ancoras[2]
    # A perna termina no tornozelo, dentro do cano da bota: a ponta redonda do tubo não
    # pode aparecer embaixo do solado.
    (tornozelo,) = girar([(-2, -16)], eixo_bota, pe)
    pincel.mangueira(
        (ancoras[0], ancoras[1], tornozelo), LARGURA_PERNA, paleta.MACACAO, contorno=2.8
    )
    pincel.forma(girar(_BOTA, eixo_bota, pe), paleta.BOTA, contorno=3)
    pincel.forma(girar(_SOLA, eixo_bota, pe), paleta.SOLA, contorno=2.5, suave=False)


def _tronco(pincel: Pincel, pose: Pose) -> None:
    """Tronco em forma de feijão, do quadril ao peito, com o macacão e as alças."""
    ex, ey = direcao(pose.quadril, pose.peito)  # eixo do corpo (para cima)
    nx, ny = -ey, ex  # perpendicular (para a frente)
    q, p = pose.quadril, pose.peito
    meio = ((q[0] + p[0]) / 2, (q[1] + p[1]) / 2)

    def lado(centro: Ponto, largura: float, ajuste: float = 0.0) -> tuple[Ponto, Ponto]:
        return (
            (centro[0] + nx * largura + ex * ajuste, centro[1] + ny * largura + ey * ajuste),
            (centro[0] - nx * largura + ex * ajuste, centro[1] - ny * largura + ey * ajuste),
        )

    frente_q, tras_q = lado(q, 27)
    frente_m, tras_m = lado(meio, 31)
    frente_p, tras_p = lado(p, 24)
    base = (q[0] - ex * 16, q[1] - ey * 16)
    topo = (p[0] + ex * 12, p[1] + ey * 12)
    contorno = [base, frente_q, frente_m, frente_p, topo, tras_p, tras_m, tras_q]
    pincel.forma(contorno, paleta.MACACAO, contorno=3)
    # Camisa aparecendo no peito, acima do peitilho do macacão.
    camisa = [
        lado(p, 20, -4)[1],
        (p[0] + ex * 11, p[1] + ey * 11),
        lado(p, 20, -4)[0],
        lado(p, 14, -14)[0],
        lado(p, 14, -14)[1],
    ]
    pincel.forma(camisa, paleta.CAMISA, contorno=2.2)
    # Alças e bolso.
    for sinal in (1, -1):
        inicio = (p[0] + nx * 13 * sinal + ex * 6, p[1] + ny * 13 * sinal + ey * 6)
        fim = (meio[0] + nx * 10 * sinal, meio[1] + ny * 10 * sinal)
        pincel.traco([inicio, fim], 3.2, paleta.MACACAO_ESCURO, afinar=False, suave=False)
    bolso_c = (meio[0] + ex * 2, meio[1] + ey * 2)
    pincel.forma(oval(bolso_c, 10, 7), paleta.MACACAO_ESCURO, contorno=2)


def _cabeca(pincel: Pincel, pose: Pose) -> None:
    c = pose.cabeca
    vento = pose.cabelo_vento
    for (dx, dy), raio in _TUFOS:
        pincel.forma(
            oval((c[0] + dx - vento, c[1] + dy), raio, raio * 0.92), paleta.CABELO, contorno=2.5
        )
    pincel.elipse((c[0] - 30, c[1] + 6), 8, 11, paleta.PELE, contorno=2.5)
    pincel.forma(deslocar(_CABECA, *c), paleta.PELE, contorno=3.2)
    pincel.elipse((c[0] + 6, c[1] + 17), 7, 4, paleta.BOCHECHA, contorno=0)
    # Boné da cooperativa: copa, faixa e aba.
    pincel.forma(deslocar(_ABA, *c), paleta.BONE_ABA, contorno=2.8)
    pincel.forma(deslocar(_BONE, *c), paleta.BONE, contorno=3)
    pincel.traco(deslocar([(-34, -16), (0, -20), (34, -18)], *c), 4, paleta.BONE_ABA, afinar=False)
    # Emblema: três setas em triângulo, só em traço (sem logotipo real).
    tri = deslocar([(4, -40), (-4, -27), (12, -27)], *c)
    pincel.traco([*tri, tri[0]], 2.2, paleta.TINTA, afinar=False, suave=False)
    # Olhos pie-cut, nariz de botão e boca.
    pincel.olho_pie_cut((c[0] + 11, c[1] - 5), 10, 15, olhar=(0.7, 0.0))
    pincel.olho_pie_cut((c[0] + 31, c[1] - 4), 9, 14, olhar=(0.7, 0.0))
    pincel.elipse((c[0] + 45, c[1] + 9), 6, 5, paleta.TINTA, contorno=0)
    if pose.boca_aberta:
        pincel.forma(deslocar(_BOCA, *c), paleta.BOCA, contorno=2.5)
        pincel.forma(deslocar(_LINGUA, *c), paleta.LINGUA, contorno=0)
    else:
        pincel.traco(deslocar([(22, 20), (33, 26), (44, 18)], *c), 3.2)


def desenhar_dara(pincel: Pincel, pose: Pose, cor_ativa=paleta.PLASTICO) -> None:
    """Desenha a Dara inteira, de trás para a frente."""
    _perna(pincel, pose.perna_tras, pose.bota_tras)
    _braco(pincel, pose.braco_tras)
    _tronco(pincel, pose)
    _perna(pincel, pose.perna_frente, pose.bota_frente)
    _cabeca(pincel, pose)
    mao = pose.braco_frente[2]
    desenhar_canhao(pincel, mao, pose.canhao, cor_ativa)
    _braco(pincel, pose.braco_frente)


# --- poses da prancha de estilo -----------------------------------------------------------

PARADA = Pose(
    quadril=(0, -80),
    peito=(3, -128),
    cabeca=(4, -186),
    perna_tras=((-11, -78), (-17, -46), (-16, -16)),
    perna_frente=((12, -78), (19, -46), (20, -16)),
    braco_tras=((-18, -124), (-42, -110), (-27, -88)),
    braco_frente=((18, -124), (34, -110), (44, -100)),
    canhao=direcao((0, 0), (1, 0.22)),
)

CORRENDO = Pose(
    quadril=(4, -84),
    peito=(18, -128),
    cabeca=(28, -184),
    perna_tras=((-6, -82), (-30, -64), (-50, -52)),
    perna_frente=((14, -82), (40, -64), (34, -16)),
    braco_tras=((2, -124), (-20, -118), (-34, -98)),
    braco_frente=((30, -122), (44, -106), (56, -104)),
    canhao=direcao((0, 0), (1, 0.05)),
    bota_tras=direcao((0, 0), (0.6, 0.8)),
    cabelo_vento=8,
    boca_aberta=True,
)

PULO_TIRO = Pose(
    quadril=(0, -118),
    peito=(8, -164),
    cabeca=(14, -220),
    perna_tras=((-10, -114), (-34, -100), (-30, -72)),
    perna_frente=((12, -114), (34, -108), (30, -80)),
    braco_tras=((-6, -158), (34, -136), (64, -164)),
    braco_frente=((22, -160), (38, -144), (50, -150)),
    canhao=direcao((0, 0), (1, -0.9)),
    bota_tras=direcao((0, 0), (0.8, 0.6)),
    bota_frente=direcao((0, 0), (0.9, 0.45)),
    cabelo_vento=6,
    boca_aberta=True,
)
