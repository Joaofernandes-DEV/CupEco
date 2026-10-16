"""Traço de desenho animado dos anos 1930 como código (D10).

Tudo é desenhado numa tela maior (4× por padrão) e reduzido no fim, o que suaviza as bordas.
As formas são descritas por poucos pontos e suavizadas por curvas que passam por eles; a
"linha viva" desloca esses pontos de leve com semente fixa, imitando o tremor do desenho à
mão sem perder a repetibilidade. O módulo não usa seno nem cosseno: só as quatro operações
e a raiz quadrada, que dão o mesmo resultado em qualquer máquina (D23).
"""

from __future__ import annotations

import math
import random
from collections.abc import Sequence

from PIL import Image, ImageDraw

Ponto = tuple[float, float]
Cor = tuple[int, int, int, int]

ESCALA_PADRAO = 4


def bezier(p0: Ponto, p1: Ponto, p2: Ponto, p3: Ponto, passos: int = 16) -> list[Ponto]:
    """Pontos de uma curva de Bézier cúbica, do ponto inicial ao final, inclusive."""
    pontos = []
    for i in range(passos + 1):
        t = i / passos
        u = 1 - t
        a, b, c, d = u * u * u, 3 * u * u * t, 3 * u * t * t, t * t * t
        pontos.append(
            (
                a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
                a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1],
            )
        )
    return pontos


def curva(
    ancoras: Sequence[Ponto], fechada: bool = False, passos: int = 10, suavidade: float = 1.0
) -> list[Ponto]:
    """Curva suave (Catmull-Rom) que passa por todas as âncoras.

    `suavidade` 0 dá segmentos retos; 1 é a curva clássica; acima disso a curva "incha".
    """
    n = len(ancoras)
    if n < 3:
        return list(ancoras)

    def ancora(i: int) -> Ponto:
        if fechada:
            return ancoras[i % n]
        return ancoras[min(max(i, 0), n - 1)]

    segmentos = n if fechada else n - 1
    fator = suavidade / 6
    resultado: list[Ponto] = []
    for i in range(segmentos):
        p0, p1, p2, p3 = ancora(i - 1), ancora(i), ancora(i + 1), ancora(i + 2)
        c1 = (p1[0] + (p2[0] - p0[0]) * fator, p1[1] + (p2[1] - p0[1]) * fator)
        c2 = (p2[0] - (p3[0] - p1[0]) * fator, p2[1] - (p3[1] - p1[1]) * fator)
        trecho = bezier(p1, c1, c2, p2, passos)
        resultado.extend(trecho[1:] if resultado else trecho)
    if fechada:
        resultado.pop()  # o último ponto repete o primeiro
    return resultado


def direcao(de: Ponto, para: Ponto) -> Ponto:
    """Vetor unitário de `de` para `para` (ou para a direita, se coincidirem)."""
    dx, dy = para[0] - de[0], para[1] - de[1]
    tamanho = math.sqrt(dx * dx + dy * dy)
    if tamanho == 0:
        return (1.0, 0.0)
    return (dx / tamanho, dy / tamanho)


def girar(pontos: Sequence[Ponto], eixo: Ponto, origem: Ponto = (0.0, 0.0)) -> list[Ponto]:
    """Gira pontos desenhados "olhando para a direita" para apontar na direção `eixo`.

    `eixo` é um vetor unitário; a rotação usa só multiplicações (sem ângulos).
    """
    cx, cy = eixo
    return [(origem[0] + x * cx - y * cy, origem[1] + x * cy + y * cx) for x, y in pontos]


def deslocar(pontos: Sequence[Ponto], dx: float, dy: float) -> list[Ponto]:
    return [(x + dx, y + dy) for x, y in pontos]


# Vértices de um octógono "redondo" (as diagonais a 0,7071 do raio), sem trigonometria.
_OCTOGONO = [
    (1, 0),
    (0.7071, 0.7071),
    (0, 1),
    (-0.7071, 0.7071),
    (-1, 0),
    (-0.7071, -0.7071),
    (0, -1),
    (0.7071, -0.7071),
]


def oval(centro: Ponto, rx: float, ry: float) -> list[Ponto]:
    """Oito âncoras de um oval, para `Pincel.forma` suavizar."""
    return [(centro[0] + x * rx, centro[1] + y * ry) for x, y in _OCTOGONO]


class Tela:
    """Imagem de trabalho em resolução ampliada; `reduzir` devolve o tamanho final."""

    def __init__(
        self,
        largura: int,
        altura: int,
        fundo: Cor = (0, 0, 0, 0),
        escala: int = ESCALA_PADRAO,
    ) -> None:
        self.largura = largura
        self.altura = altura
        self.escala = escala
        self.imagem = Image.new("RGBA", (largura * escala, altura * escala), fundo)
        self.desenho = ImageDraw.Draw(self.imagem)

    def px(self, p: Ponto) -> Ponto:
        return (p[0] * self.escala, p[1] * self.escala)

    def nova_camada(self) -> Tela:
        return Tela(self.largura, self.altura, escala=self.escala)

    def juntar(self, camada: Tela, opacidade: float = 1.0) -> None:
        """Compõe uma camada por cima desta, com transparência opcional."""
        imagem = camada.imagem
        if opacidade < 1:
            alfa = imagem.getchannel("A").point(lambda a: round(a * opacidade))
            imagem = imagem.copy()
            imagem.putalpha(alfa)
        self.imagem.alpha_composite(imagem)

    def reduzir(self) -> Image.Image:
        return self.imagem.resize((self.largura, self.altura), Image.Resampling.LANCZOS)


class Pincel:
    """Desenha numa `Tela` em coordenadas locais (de um personagem, de um objeto).

    `origem` e `escala` posicionam o desenho; `espelhar` inverte o eixo x; `tremor` é a
    amplitude da linha viva, em unidades locais, sorteada com `semente`.
    """

    def __init__(
        self,
        tela: Tela,
        origem: Ponto = (0.0, 0.0),
        escala: float = 1.0,
        espelhar: bool = False,
        tremor: float = 0.0,
        semente: int = 0,
        tinta: Cor = (28, 22, 20, 255),
    ) -> None:
        self.tela = tela
        self.origem = origem
        self.escala = escala
        self.espelhar = espelhar
        self.tremor = tremor
        self.tinta = tinta
        self._sorteio = random.Random(semente)

    # --- coordenadas -----------------------------------------------------------------

    def _mapear(self, p: Ponto) -> Ponto:
        x, y = p
        if self.espelhar:
            x = -x
        return self.tela.px((self.origem[0] + x * self.escala, self.origem[1] + y * self.escala))

    def _vivo(self, pontos: Sequence[Ponto]) -> list[Ponto]:
        if not self.tremor:
            return list(pontos)
        t = self.tremor
        return [
            (x + self._sorteio.uniform(-t, t), y + self._sorteio.uniform(-t, t)) for x, y in pontos
        ]

    def _largura_px(self, largura: float) -> float:
        return largura * self.escala * self.tela.escala

    # --- traços -----------------------------------------------------------------------

    def _carimbar(self, pontos: Sequence[Ponto], larguras: Sequence[float], cor: Cor) -> None:
        """Traço de largura variável: círculos carimbados ao longo do caminho (em pixels)."""
        desenho = self.tela.desenho
        for i in range(len(pontos) - 1):
            (x0, y0), (x1, y1) = pontos[i], pontos[i + 1]
            w0, w1 = larguras[i], larguras[i + 1]
            distancia = math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)
            passos = max(1, math.ceil(distancia / max(min(w0, w1) * 0.2, 1.0)))
            for k in range(passos + (1 if i == len(pontos) - 2 else 0)):
                f = k / passos
                x, y = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
                r = (w0 + (w1 - w0) * f) / 2
                desenho.ellipse((x - r, y - r, x + r, y + r), fill=cor)

    def traco(
        self,
        ancoras: Sequence[Ponto],
        largura: float,
        cor: Cor | None = None,
        afinar: bool = True,
        suave: bool = True,
        fechado: bool = False,
    ) -> None:
        """Linha de pincel. Com `afinar`, as pontas ficam finas como numa pincelada."""
        pontos = self._vivo(ancoras)
        if suave:
            pontos = curva(pontos, fechada=fechado)
        if fechado:
            pontos = [*pontos, pontos[0]]
        self._tracar_local(pontos, largura, cor or self.tinta, afinar)

    def _tracar_local(
        self, pontos: Sequence[Ponto], largura: float, cor: Cor, afinar: bool
    ) -> None:
        n = len(pontos)
        larguras = []
        for i in range(n):
            t = i / (n - 1) if n > 1 else 0.5
            perfil = 0.35 + 0.65 * min(1.0, t * 5, (1 - t) * 5) if afinar else 1.0
            larguras.append(self._largura_px(largura * perfil))
        self._carimbar([self._mapear(p) for p in pontos], larguras, cor)

    def mangueira(
        self,
        ancoras: Sequence[Ponto],
        largura: float,
        cor: Cor,
        contorno: float = 3.0,
    ) -> None:
        """Membro de "mangueira": tubo de largura constante, sem cotovelo, com contorno."""
        pontos = curva(self._vivo(ancoras), passos=14)
        self._tracar_local(pontos, largura + 2 * contorno, self.tinta, afinar=False)
        self._tracar_local(pontos, largura, cor, afinar=False)

    # --- formas cheias ---------------------------------------------------------------

    def forma(
        self,
        ancoras: Sequence[Ponto],
        cor: Cor,
        contorno: float = 3.0,
        suave: bool = True,
        suavidade: float = 1.0,
    ) -> None:
        """Forma fechada preenchida, com contorno de tinta (0 = sem contorno)."""
        pontos = self._vivo(ancoras)
        if suave:
            pontos = curva(pontos, fechada=True, suavidade=suavidade)
        self.tela.desenho.polygon([self._mapear(p) for p in pontos], fill=cor)
        if contorno:
            self._tracar_local([*pontos, pontos[0]], contorno, self.tinta, afinar=False)

    def poligono(self, pontos: Sequence[Ponto], cor: Cor) -> None:
        """Polígono reto, sem contorno nem linha viva (detalhes pequenos)."""
        self.tela.desenho.polygon([self._mapear(p) for p in pontos], fill=cor)

    def elipse(self, centro: Ponto, rx: float, ry: float, cor: Cor, contorno: float = 3.0) -> None:
        """Elipse alinhada aos eixos, com contorno opcional."""
        ((cx, cy),) = self._vivo([centro])
        if contorno:
            self._elipse_px((cx, cy), rx + contorno / 2, ry + contorno / 2, self.tinta)
            self._elipse_px((cx, cy), rx - contorno / 2, ry - contorno / 2, cor)
        else:
            self._elipse_px((cx, cy), rx, ry, cor)

    def _elipse_px(self, centro: Ponto, rx: float, ry: float, cor: Cor) -> None:
        x, y = self._mapear(centro)
        ex, ey = self._largura_px(rx), self._largura_px(ry)
        self.tela.desenho.ellipse((x - ex, y - ey, x + ex, y + ey), fill=cor)

    def olho_pie_cut(
        self,
        centro: Ponto,
        rx: float,
        ry: float,
        olhar: Ponto = (0.0, 0.0),
        branco: Cor = (250, 246, 236, 255),
        contorno: float = 2.5,
    ) -> None:
        """Olho clássico dos anos 30: branco oval, pupila grande com a "fatia" recortada.

        `olhar` desloca a pupila (frações do raio). O recorte é um triângulo apontado para
        o alto, no lado para onde o olho olha.
        """
        self.elipse(centro, rx, ry, branco, contorno)
        px = centro[0] + olhar[0] * rx * 0.45
        py = centro[1] + olhar[1] * ry * 0.35 + ry * 0.12
        prx, pry = rx * 0.62, ry * 0.7
        self.elipse((px, py), prx, pry, self.tinta, contorno=0)
        # A fatia: triângulo do centro da pupila até a borda, um pouco acima e ao lado.
        lado = 1 if olhar[0] >= 0 else -1
        fatia = [
            (px + prx * 0.05 * lado, py - pry * 0.05),
            (px + prx * 0.25 * lado, py - pry * 1.2),
            (px + prx * 0.95 * lado, py - pry * 0.75),
        ]
        self.poligono(fatia, branco)
