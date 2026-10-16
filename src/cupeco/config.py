"""Constantes do jogo: janela, ritmo e cores."""

TITULO = "Triagem"

# Resolução lógica (16:9). A arte de desenho animado precisa de mais resolução que pixel art;
# o pygame.SCALED ajusta a janela à tela (D4).
LARGURA_TELA = 1280
ALTURA_TELA = 720

# Ritmo de desenho da tela. A simulação tem passo fixo próprio (passo_fixo.py, D8).
FPS = 60

Cor = tuple[int, int, int]


class Paleta:
    """Cores provisórias da Fase 0; a paleta final é definida na Fase 3 (I1).

    As cores dos materiais seguem a CONAMA 275/2001 e vão para o domínio na Fase 1 (D15).
    """

    FUNDO: Cor = (234, 222, 196)
    TEXTO: Cor = (40, 32, 28)
    APAGADO: Cor = (128, 114, 98)
    PAPEL: Cor = (36, 92, 170)
    PLASTICO: Cor = (196, 44, 40)
    VIDRO: Cor = (44, 132, 64)
    METAL: Cor = (226, 178, 30)
