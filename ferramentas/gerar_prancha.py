"""Gera a prancha de estilo (D19) em `docs/prancha-estilo.png`.

Uso, a partir da raiz do repositório: `python -m ferramentas.gerar_prancha`.
A prancha mostra a Dara em 3 poses, os 6 resíduos e um pedaço de Aterrópolis com o efeito
de filme, para o João aprovar o estilo antes de qualquer animação.
"""

from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

from ferramentas.arte import paleta
from ferramentas.arte.cenarios.aterropolis import desenhar_rua
from ferramentas.arte.efeitos import filme, grao
from ferramentas.arte.letreiro import escrever, largura
from ferramentas.arte.personagens import dara
from ferramentas.arte.residuos import RESIDUOS
from ferramentas.arte.traco import Pincel, Tela

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = RAIZ / "docs" / "prancha-estilo.png"

LARGURA, ALTURA = 1600, 1040
TREMOR = 0.6  # amplitude da "linha viva"
APAGADO = (110, 96, 84)


def _centralizado(
    desenho: ImageDraw.ImageDraw,
    centro_x: float,
    y: float,
    texto: str,
    tamanho: int = 22,
    cor=paleta.TINTA,
) -> None:
    escrever(desenho, (centro_x - largura(texto, tamanho) / 2, y), texto, tamanho, cor)


def poses() -> Image.Image:
    tela = Tela(980, 400)
    for indice, (pose, x) in enumerate(
        [(dara.PARADA, 170), (dara.CORRENDO, 490), (dara.PULO_TIRO, 800)]
    ):
        pincel = Pincel(tela, origem=(x, 370), escala=1.3, tremor=TREMOR, semente=indice)
        dara.desenhar_dara(pincel, pose)
    return tela.reduzir()


def residuos() -> list[tuple[str, Image.Image]]:
    imagens = []
    for indice, (nome, desenhar) in enumerate(RESIDUOS.values()):
        tela = Tela(120, 120)
        desenhar(Pincel(tela, origem=(60, 60), escala=1.25, tremor=TREMOR, semente=40 + indice))
        imagens.append((nome, tela.reduzir()))
    return imagens


def cenario() -> Image.Image:
    tela = Tela(1500, 380)
    desenhar_rua(tela)
    dara.desenhar_dara(
        Pincel(tela, origem=(420, 340), escala=0.95, tremor=TREMOR, semente=9),
        dara.CORRENDO,
        cor_ativa=paleta.PAPEL,
    )
    # Resíduos voando sobre o fundo, para conferir a leitura contra o cenário (I4).
    posicoes = [(640, 150), (760, 230), (880, 120), (1000, 210), (1120, 140), (1240, 230)]
    for indice, ((_, desenhar), (x, y)) in enumerate(zip(RESIDUOS.values(), posicoes, strict=True)):
        desenhar(Pincel(tela, origem=(x, y), escala=0.85, tremor=TREMOR, semente=60 + indice))
    return filme(tela.reduzir())


def gerar() -> Image.Image:
    papel = Image.new("RGB", (LARGURA, ALTURA), paleta.PAPEL_FUNDO[:3])
    textura = grao(LARGURA, ALTURA, 11).point(lambda v: 128 + (v - 128) // 12)
    prancha = ImageChops.overlay(papel, Image.merge("RGB", [textura] * 3))
    desenho = ImageDraw.Draw(prancha)

    escrever(desenho, (40, 24), "TRIAGEM", 56, paleta.TINTA)
    escrever(
        desenho,
        (44, 92),
        "Prancha de estilo · rubber hose original, gerado por código (D10, D19)",
        22,
        APAGADO,
    )

    imagem_poses = poses()
    prancha.paste(imagem_poses, (10, 130), imagem_poses)
    for x, texto in ((190, "Parada"), (510, "Correndo"), (820, "Pulo + tiro na diagonal")):
        _centralizado(desenho, x, 540, texto)

    escrever(desenho, (1030, 136), "Resíduos da Triagem", 28, paleta.TINTA)
    escrever(desenho, (1030, 176), "cor (CONAMA 275/2001) + silhueta + marca", 18, APAGADO)
    for indice, (nome, imagem) in enumerate(residuos()):
        coluna, linha = indice % 3, indice // 3
        x, y = 1030 + coluna * 180, 220 + linha * 175
        prancha.paste(imagem, (x + 20, y), imagem)
        _centralizado(desenho, x + 80, y + 124, nome)
    _centralizado(desenho, 1300, 570, "Recicláveis: halo liso (dá para separar)", 17, APAGADO)
    _centralizado(
        desenho, 1300, 594, "Rejeito e perigoso: halo serrilhado + selo (não dá)", 17, APAGADO
    )

    imagem_cenario = cenario()
    desenho.rectangle(
        (46, 626, 54 + imagem_cenario.width, 634 + imagem_cenario.height), fill=paleta.TINTA
    )
    prancha.paste(imagem_cenario, (50, 630))
    _centralizado(
        desenho,
        800,
        1014,
        "Aterrópolis: rua com o aterro ao fundo, com efeito de filme",
        18,
        APAGADO,
    )
    return prancha


def main() -> None:
    SAIDA.parent.mkdir(exist_ok=True)
    gerar().save(SAIDA, optimize=True)
    print(f"Prancha gerada em {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
