"""Efeito de filme antigo (I2): tom desbotado, grão e vinheta, todos determinísticos."""

import random

from PIL import Image, ImageChops

TAMANHO_GRAO = 256


def grao(largura: int, altura: int, semente: int) -> Image.Image:
    """Ruído em tons de cinza, repetido em ladrilhos a partir de uma semente fixa."""
    sorteio = random.Random(semente)
    ladrilho = Image.frombytes(
        "L", (TAMANHO_GRAO, TAMANHO_GRAO), sorteio.randbytes(TAMANHO_GRAO**2)
    )
    imagem = Image.new("L", (largura, altura))
    for y in range(0, altura, TAMANHO_GRAO):
        for x in range(0, largura, TAMANHO_GRAO):
            imagem.paste(ladrilho, (x, y))
    return imagem


def vinheta(largura: int, altura: int, forca: float = 0.45) -> Image.Image:
    """Máscara clara no centro e escura nas bordas (255 = sem escurecer)."""
    radial = Image.radial_gradient("L").resize((largura, altura), Image.Resampling.BILINEAR)
    # radial_gradient vai de 0 (centro) a 255 (borda); escurece só a parte de fora.
    return radial.point(lambda v: 255 - round(max(0, v - 150) * forca * 2.4))


def filme(imagem: Image.Image, semente: int = 1930, desbotar: float = 0.18) -> Image.Image:
    """Aplica o "filme": puxa as cores para o sépia, soma grão e escurece as bordas."""
    base = imagem.convert("RGB")
    sepia = Image.merge(
        "RGB",
        [
            base.convert("L").point(lambda v: min(255, round(v * 1.08 + 12))),
            base.convert("L").point(lambda v: round(v * 0.95 + 6)),
            base.convert("L").point(lambda v: round(v * 0.78)),
        ],
    )
    resultado = Image.blend(base, sepia, desbotar)
    ruido = grao(*resultado.size, semente).point(lambda v: 128 + (v - 128) // 6)
    resultado = ImageChops.overlay(resultado, Image.merge("RGB", [ruido] * 3))
    mascara = vinheta(*resultado.size)
    return ImageChops.multiply(resultado, Image.merge("RGB", [mascara] * 3))
