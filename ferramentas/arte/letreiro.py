"""Texto com os acentos do português sobre a fonte embutida do Pillow.

A fonte que vem com o Pillow só tem os caracteres ASCII; os acentos (á, ã, â, à, ç, é, ê,
í, ó, õ, ô, ú) são desenhados aqui por traços. Serve para rótulos de pranchas e
documentos; a fonte do jogo (OFL, com acentos) é escolhida na Fase 3 (I12).
"""

import unicodedata

from PIL import ImageDraw, ImageFont

AGUDO, GRAVE, CIRCUNFLEXO, TIL, CEDILHA = "́", "̀", "̂", "̃", "̧"


def fonte(tamanho: int) -> ImageFont.FreeTypeFont:
    return ImageFont.load_default(size=tamanho)


def largura(texto: str, tamanho: int) -> float:
    f = fonte(tamanho)
    return sum(f.getlength(unicodedata.normalize("NFD", c)[0]) for c in texto)


def _acento(desenho, marca, cx, topo, base_y, s, cor, espessura) -> None:
    if marca == AGUDO:
        pontos = [(cx - 0.05 * s, topo - 0.06 * s), (cx + 0.09 * s, topo - 0.22 * s)]
    elif marca == GRAVE:
        pontos = [(cx + 0.05 * s, topo - 0.06 * s), (cx - 0.09 * s, topo - 0.22 * s)]
    elif marca == CIRCUNFLEXO:
        pontos = [
            (cx - 0.12 * s, topo - 0.07 * s),
            (cx, topo - 0.2 * s),
            (cx + 0.12 * s, topo - 0.07 * s),
        ]
    elif marca == TIL:
        pontos = [
            (cx - 0.13 * s, topo - 0.08 * s),
            (cx - 0.06 * s, topo - 0.16 * s),
            (cx + 0.05 * s, topo - 0.1 * s),
            (cx + 0.13 * s, topo - 0.18 * s),
        ]
    elif marca == CEDILHA:
        pontos = [
            (cx, base_y),
            (cx, base_y + 0.07 * s),
            (cx + 0.07 * s, base_y + 0.12 * s),
            (cx - 0.05 * s, base_y + 0.2 * s),
        ]
    else:
        raise ValueError(f"acento não suportado: {marca!r}")
    desenho.line(pontos, fill=cor, width=espessura, joint="curve")


def escrever(
    desenho: ImageDraw.ImageDraw, posicao: tuple[float, float], texto: str, tamanho: int, cor
) -> None:
    """Escreve `texto` com o topo da linha em `posicao`."""
    f = fonte(tamanho)
    x, y = posicao
    base_y = y + f.getmetrics()[0]
    altura_x = -f.getbbox("x", anchor="ls")[1]
    espessura = max(1, round(tamanho * 0.075))
    for caractere in texto:
        partes = unicodedata.normalize("NFD", caractere)
        base, marcas = partes[0], partes[1:]
        esquerda, cima, direita, _ = f.getbbox(base, anchor="ls")
        cx = x + (esquerda + direita) / 2
        if base == "i" and marcas:
            # "i" sem pingo: só a haste, para o acento ficar no lugar do pingo.
            meia = espessura * 0.7
            desenho.rectangle((cx - meia, base_y - altura_x, cx + meia, base_y), fill=cor)
        else:
            desenho.text((x, base_y), base, font=f, fill=cor, anchor="ls")
        topo = base_y + cima if base.isupper() else base_y - altura_x
        for marca in marcas:
            _acento(desenho, marca, cx, topo, base_y, tamanho, cor, espessura)
        x += f.getlength(base)
