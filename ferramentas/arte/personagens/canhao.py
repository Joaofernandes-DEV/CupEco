"""Canhão de Triagem: um aspirador industrial adaptado (I1).

A faixa colorida no corpo mostra a "lixeira ativa", a cor da arma equipada (D12).
Desenhado olhando para a direita, com a origem na empunhadura, e girado para `eixo`.
"""

from ferramentas.arte import paleta
from ferramentas.arte.traco import Pincel, Ponto, girar

# Corpo do tanque, faixa e bocal em funil (coordenadas locais, apontando para a direita).
_CORPO = [(-26, -11), (0, -13), (30, -12), (34, 0), (30, 12), (0, 13), (-26, 11), (-30, 0)]
_FAIXA = [(6, -14), (24, -14), (24, 14), (6, 14)]
_BOCAL = [(30, -9), (44, -11), (62, -21), (66, 0), (62, 21), (44, 11), (30, 9)]
_BOCA = [(60, -15), (64, 0), (60, 15), (57, 0)]
_TAMPA = [(-30, -8), (-36, -6), (-38, 0), (-36, 6), (-30, 8)]
_PONTEIRO = [(-6, -13), (-4, -21), (6, -21), (8, -13)]


def desenhar_canhao(pincel: Pincel, empunhadura: Ponto, eixo: Ponto, cor_ativa) -> None:
    def no_mundo(pontos):
        return girar(pontos, eixo, empunhadura)

    pincel.forma(no_mundo(_TAMPA), paleta.CANHAO_ESCURO, contorno=2.5)
    pincel.forma(no_mundo(_PONTEIRO), paleta.LATAO, contorno=2.5, suave=False)
    pincel.forma(no_mundo(_CORPO), paleta.CANHAO, contorno=3)
    pincel.forma(no_mundo(_FAIXA), cor_ativa, contorno=2, suave=False)
    pincel.forma(no_mundo(_BOCAL), paleta.LATAO, contorno=3, suavidade=0.6)
    pincel.forma(no_mundo(_BOCA), paleta.TINTA, contorno=0, suavidade=0.8)
    # Brilho no tanque.
    pincel.traco(no_mundo([(-18, -6), (4, -8), (24, -7)]), 2.2, paleta.BRANCO)
