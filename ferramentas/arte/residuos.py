"""Os seis resíduos da Triagem (I4, D15): cor da CONAMA + silhueta própria + marca.

Recicláveis (papel, plástico, vidro, metal) têm um halo claro e liso: dá para separar.
Rejeito e perigoso têm um halo serrilhado e um selo (proibido ou perigo): não dá. Assim
nenhuma informação depende só da cor (R3). Cada resíduo é desenhado em torno da origem,
com cerca de 30 unidades de raio.
"""

from collections.abc import Callable

from ferramentas.arte import paleta
from ferramentas.arte.traco import Pincel, Ponto, deslocar, girar, oval

# 16 direções em volta do círculo (cosseno, seno), escritas à mão para não usar trigonometria.
_C = (1.0, 0.9239, 0.7071, 0.3827, 0.0, -0.3827, -0.7071, -0.9239)
_S = (0.0, 0.3827, 0.7071, 0.9239, 1.0, 0.9239, 0.7071, 0.3827)
CIRCULO_16: tuple[Ponto, ...] = tuple(
    zip(_C + tuple(-c for c in _C), _S + tuple(-s for s in _S), strict=True)
)

HALO_LISO = (250, 246, 236, 170)
HALO_SERRA = (28, 22, 20, 255)


def _halo_liso(pincel: Pincel) -> None:
    pincel.forma(oval((0, 0), 38, 38), HALO_LISO, contorno=0)


def _halo_serrilhado(pincel: Pincel, cor) -> None:
    pontas = []
    for i, (c, s) in enumerate(CIRCULO_16):
        raio = 42 if i % 2 == 0 else 32
        pontas.append((c * raio, s * raio))
    pincel.forma(pontas, cor, contorno=2.5, suave=False)


def _selo_proibido(pincel: Pincel, centro: Ponto) -> None:
    x, y = centro
    pincel.elipse(centro, 12, 12, paleta.BRANCO, contorno=3.5)
    pincel.traco([(x - 8, y - 8), (x + 8, y + 8)], 4, afinar=False, suave=False)


def _selo_perigo(pincel: Pincel, centro: Ponto) -> None:
    triangulo = deslocar([(0, -15), (15, 11), (-15, 11)], *centro)
    pincel.forma(triangulo, paleta.BRANCO, contorno=3, suave=False)
    x, y = centro
    pincel.traco([(x, y - 7), (x, y + 2)], 3.6, afinar=False, suave=False)
    pincel.elipse((x, y + 6.5), 2, 2, paleta.TINTA, contorno=0)


def papel(pincel: Pincel) -> None:
    """Bola de papel amassada."""
    _halo_liso(pincel)
    bola = [
        (-24, -8),
        (-16, -24),
        (-2, -22),
        (8, -28),
        (22, -16),
        (26, 0),
        (20, 18),
        (6, 26),
        (-8, 20),
        (-22, 20),
        (-28, 6),
    ]
    pincel.forma(bola, paleta.PAPEL, contorno=3, suavidade=0.55)
    for vinco in (
        [(-14, -14), (-4, -6), (-8, 6)],
        [(4, -18), (8, -4), (18, 2)],
        [(-2, 8), (6, 16)],
        [(-18, 6), (-10, 12)],
    ):
        pincel.traco(vinco, 2.2, suave=False)
    pincel.traco([(-10, -20), (2, -18)], 2.4, paleta.BRANCO)


_DIAGONAL = (0.7071, -0.7071)  # garrafa inclinada, com a tampa para cima e para a direita
_GARRAFA = [(-27, -10), (-27, 10), (6, 12), (14, 7), (19, 5), (19, -5), (14, -7), (6, -12)]
_TAMPA_PET = [(18, -7), (27, -7), (27, 7), (18, 7)]
_ROTULO = [(-16, -12), (-2, -12), (-2, 12), (-16, 12)]


def plastico(pincel: Pincel) -> None:
    """Garrafa PET com tampa e rótulo, inclinada."""
    _halo_liso(pincel)
    pincel.forma(girar(_GARRAFA, _DIAGONAL), paleta.PLASTICO, contorno=3, suavidade=0.45)
    pincel.forma(girar(_ROTULO, _DIAGONAL), (236, 112, 104, 255), contorno=2.2, suave=False)
    pincel.forma(girar(_TAMPA_PET, _DIAGONAL), paleta.BRANCO, contorno=2.6, suave=False)
    pincel.traco(girar([(-21, -10), (-21, 10)], _DIAGONAL), 2.2, afinar=False, suave=False)
    pincel.traco(girar([(-22, -5), (-6, -7), (10, -6)], _DIAGONAL), 2.6, paleta.BRANCO)


def vidro(pincel: Pincel) -> None:
    """Pote de vidro com tampa."""
    _halo_liso(pincel)
    pote = [(-20, -14), (-22, 6), (-20, 24), (0, 28), (20, 24), (22, 6), (20, -14), (0, -16)]
    pincel.forma(pote, paleta.VIDRO, contorno=3, suavidade=0.7)
    pincel.forma(
        [(-17, -26), (17, -26), (19, -14), (-19, -14)],
        paleta.CANHAO_ESCURO,
        contorno=2.6,
        suave=False,
    )
    pincel.traco([(-12, -6), (-14, 10), (-10, 20)], 3, paleta.BRANCO)
    pincel.traco([(10, -4), (12, 2)], 2.4, paleta.BRANCO)


def metal(pincel: Pincel) -> None:
    """Lata de alumínio com anel."""
    _halo_liso(pincel)
    pincel.forma(
        [(-18, -20), (18, -20), (18, 22), (0, 27), (-18, 22)],
        paleta.METAL,
        contorno=3,
        suavidade=0.35,
    )
    pincel.elipse((0, -20), 18, 6, (250, 222, 120, 255), contorno=2.6)
    pincel.forma([(-4, -22), (6, -22), (6, -17), (-4, -17)], paleta.CANHAO, contorno=1.8)
    for y in (-8, 10):
        pincel.traco([(-18, y), (0, y + 4), (18, y)], 2.2, afinar=False)
    pincel.traco([(-11, -12), (-11, 16)], 3, paleta.BRANCO)


def rejeito(pincel: Pincel) -> None:
    """Saco de lixo misturado (não reciclável): halo serrilhado e selo de proibido."""
    _halo_serrilhado(pincel, (88, 86, 82, 255))
    saco = [
        (-24, 2),
        (-20, -14),
        (-8, -20),
        (0, -24),
        (8, -20),
        (20, -14),
        (26, 4),
        (20, 22),
        (0, 27),
        (-18, 22),
    ]
    pincel.forma(saco, paleta.REJEITO, contorno=3, suavidade=0.8)
    pincel.forma([(-6, -22), (0, -34), (6, -22)], paleta.REJEITO, contorno=2.5)
    pincel.traco([(-14, 6), (-6, 14)], 2.2)
    _selo_proibido(pincel, (8, 6))


def perigoso(pincel: Pincel) -> None:
    """Pilha (resíduo perigoso): halo serrilhado e selo de perigo."""
    _halo_serrilhado(pincel, (150, 70, 10, 255))
    pincel.forma(
        [(-14, -20), (14, -20), (14, 26), (-14, 26)], paleta.PERIGOSO, contorno=3, suave=False
    )
    pincel.forma(
        [(-6, -27), (6, -27), (6, -20), (-6, -20)], paleta.CANHAO, contorno=2.4, suave=False
    )
    pincel.forma([(-14, 12), (14, 12), (14, 26), (-14, 26)], paleta.TINTA, contorno=0, suave=False)
    pincel.traco([(-9, -14), (-9, 6)], 2.6, paleta.BRANCO, afinar=False)
    _selo_perigo(pincel, (0, -2))


RESIDUOS: dict[str, tuple[str, Callable[[Pincel], None]]] = {
    "papel": ("Papel", papel),
    "plastico": ("Plástico", plastico),
    "vidro": ("Vidro", vidro),
    "metal": ("Metal", metal),
    "rejeito": ("Rejeito", rejeito),
    "perigoso": ("Perigoso", perigoso),
}
