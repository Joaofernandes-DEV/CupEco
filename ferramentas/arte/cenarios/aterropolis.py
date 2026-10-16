"""Uma rua de Aterrópolis com o aterro ao fundo (pedaço de cenário da prancha, D19).

Fundo pintado, de contorno fino e tons apagados; primeiro plano com contorno grosso, como
nos desenhos dos anos 30. Nada aqui usa as cores fortes dos materiais (I4).
"""

import random

from ferramentas.arte import paleta
from ferramentas.arte.traco import Pincel, Tela, oval


def _ceu(tela: Tela) -> None:
    altura_px = tela.altura * tela.escala
    largura_px = tela.largura * tela.escala
    alto, baixo = paleta.CEU_ALTO, paleta.CEU_BAIXO
    faixas = 48
    for i in range(faixas):
        f = i / (faixas - 1)
        cor = tuple(round(alto[k] + (baixo[k] - alto[k]) * f) for k in range(3)) + (255,)
        y0 = altura_px * i // faixas
        y1 = altura_px * (i + 1) // faixas
        tela.desenho.rectangle((0, y0, largura_px, y1), fill=cor)


def _predio(
    pincel: Pincel,
    x: float,
    base: float,
    largura: float,
    altura: float,
    cor,
    sorteio: random.Random,
    contorno: float,
) -> None:
    curva = largura * 0.08  # paredes "de borracha", levemente barrigudas
    topo = base - altura
    pincel.forma(
        [
            (x, base),
            (x - curva, base - altura / 2),
            (x, topo),
            (x + largura / 2, topo - 4),
            (x + largura, topo),
            (x + largura + curva, base - altura / 2),
            (x + largura, base),
        ],
        cor,
        contorno=contorno,
        suavidade=0.6,
    )
    for linha in range(int((altura - 24) // 22)):
        for coluna in range(int((largura - 12) // 16)):
            acesa = sorteio.random() < 0.18
            jx = x + 9 + coluna * 16
            jy = topo + 14 + linha * 22
            pincel.poligono(
                [(jx, jy), (jx + 7, jy), (jx + 7, jy + 11), (jx, jy + 11)],
                paleta.JANELA_ACESA if acesa else paleta.JANELA,
            )


def desenhar_rua(tela: Tela, semente: int = 7) -> None:
    sorteio = random.Random(semente)
    largura, altura = tela.largura, tela.altura
    chao = altura - 58
    _ceu(tela)

    fundo = Pincel(tela, tremor=0.4, semente=semente)
    # Sol abafado pela fumaça.
    fundo.elipse((largura * 0.78, altura * 0.22), 34, 34, (244, 226, 180, 255), contorno=0)

    # Prédios distantes.
    x = -20.0
    while x < largura:
        w = sorteio.uniform(46, 80)
        h = sorteio.uniform(90, 170)
        _predio(fundo, x, chao - 40, w, h, paleta.PREDIO_LONGE, sorteio, contorno=1.4)
        x += w + sorteio.uniform(4, 14)

    # Chaminés soltando fumaça, numa camada translúcida.
    fumaca = tela.nova_camada()
    pincel_fumaca = Pincel(fumaca, tremor=1.0, semente=semente + 1)
    for cx in (largura * 0.18, largura * 0.56):
        fundo.forma(
            [(cx - 9, chao - 40), (cx - 7, chao - 210), (cx + 7, chao - 210), (cx + 9, chao - 40)],
            paleta.PREDIO_PERTO,
            contorno=1.6,
            suave=False,
        )
        for k in range(6):
            raio = 16 + k * 7
            pincel_fumaca.forma(
                oval((cx + 14 + k * 26, chao - 226 - k * 10), raio, raio * 0.7),
                paleta.FUMACA,
                contorno=0,
            )
    tela.juntar(fumaca, opacidade=0.55)

    # O aterro: um morro de lixo misturado, com pneus e sucata em tons apagados.
    meio = Pincel(tela, tremor=0.8, semente=semente + 2)
    morro = [
        (largura * 0.42, chao + 4),
        (largura * 0.52, chao - 70),
        (largura * 0.66, chao - 118),
        (largura * 0.8, chao - 104),
        (largura * 0.94, chao - 60),
        (largura + 30, chao - 40),
        (largura + 30, chao + 4),
    ]
    meio.forma(morro, paleta.ATERRO, contorno=2.2, suavidade=0.9)
    for _ in range(26):
        px = sorteio.uniform(largura * 0.5, largura * 0.98)
        py = sorteio.uniform(chao - 90, chao - 10)
        if sorteio.random() < 0.4:
            meio.elipse((px, py), 9, 6, paleta.SOLA, contorno=1.6)
            meio.elipse((px, py), 3.5, 2.4, paleta.ATERRO, contorno=0)
        else:
            w, h = sorteio.uniform(6, 14), sorteio.uniform(5, 10)
            meio.forma(
                [(px, py), (px + w, py - 2), (px + w + 2, py + h), (px - 1, py + h)],
                paleta.ATERRO_CLARO,
                contorno=1.6,
                suavidade=0.4,
            )

    # Primeiro plano: calçada, rua e um poste "de borracha".
    frente = Pincel(tela, tremor=0.6, semente=semente + 3)
    frente.forma(
        [
            (-10, chao - 8),
            (largura + 10, chao - 8),
            (largura + 10, altura + 10),
            (-10, altura + 10),
        ],
        paleta.CHAO,
        contorno=3,
        suave=False,
    )
    frente.forma(
        [(-10, chao - 8), (largura + 10, chao - 8), (largura + 10, chao + 8), (-10, chao + 8)],
        paleta.CALCADA,
        contorno=3,
        suave=False,
    )
    for i in range(14):
        bx = 20 + i * 56 + sorteio.uniform(-6, 6)
        frente.traco([(bx, chao + 26), (bx + 22, chao + 24)], 2.2)
        frente.traco([(bx + 28, chao + 42), (bx + 50, chao + 40)], 2.2)
    poste_x = largura * 0.08
    frente.mangueira(
        [(poste_x, chao - 6), (poste_x + 6, chao - 100), (poste_x + 30, chao - 158)],
        7,
        paleta.PREDIO_PERTO,
        contorno=2.6,
    )
    frente.forma(oval((poste_x + 38, chao - 160), 14, 9), paleta.JANELA_ACESA, contorno=2.6)
