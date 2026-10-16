"""Cores da arte (RGBA).

As cores dos materiais seguem a CONAMA 275/2001 e são as únicas cores fortes do jogo: os
personagens e cenários usam tons terrosos e apagados para que um resíduo colorido sempre
se destaque (I4, R3). O domínio terá a mesma tabela na Fase 1 (D15).
"""

Cor = tuple[int, int, int, int]

# --- tinta e papel -------------------------------------------------------------------
TINTA: Cor = (28, 22, 20, 255)
BRANCO: Cor = (250, 246, 236, 255)
PAPEL_FUNDO: Cor = (236, 224, 198, 255)
SOMBRA: Cor = (28, 22, 20, 60)

# --- materiais (CONAMA 275/2001) -----------------------------------------------------
PAPEL: Cor = (38, 98, 182, 255)
PLASTICO: Cor = (206, 44, 40, 255)
VIDRO: Cor = (36, 140, 72, 255)
METAL: Cor = (242, 190, 28, 255)
REJEITO: Cor = (128, 126, 122, 255)
PERIGOSO: Cor = (240, 122, 18, 255)

# --- Dara ----------------------------------------------------------------------------
PELE: Cor = (150, 96, 64, 255)
PELE_SOMBRA: Cor = (122, 74, 48, 255)
BOCHECHA: Cor = (196, 102, 86, 255)
CABELO: Cor = (36, 26, 24, 255)
MACACAO: Cor = (74, 84, 100, 255)
MACACAO_ESCURO: Cor = (54, 62, 76, 255)
CAMISA: Cor = (232, 220, 196, 255)
BONE: Cor = (226, 214, 186, 255)
BONE_ABA: Cor = (92, 70, 52, 255)
LUVA: Cor = (226, 178, 66, 255)
LUVA_PUNHO: Cor = (196, 146, 46, 255)
BOTA: Cor = (112, 72, 46, 255)
SOLA: Cor = (52, 40, 34, 255)
BOCA: Cor = (96, 34, 30, 255)
LINGUA: Cor = (214, 110, 104, 255)

# --- Canhão de Triagem ---------------------------------------------------------------
CANHAO: Cor = (122, 132, 126, 255)
CANHAO_ESCURO: Cor = (86, 94, 90, 255)
LATAO: Cor = (182, 146, 82, 255)

# --- Aterrópolis ---------------------------------------------------------------------
CEU_ALTO: Cor = (226, 204, 160, 255)
CEU_BAIXO: Cor = (214, 176, 126, 255)
PREDIO_LONGE: Cor = (160, 140, 120, 255)
PREDIO_PERTO: Cor = (122, 104, 92, 255)
JANELA: Cor = (80, 66, 60, 255)
JANELA_ACESA: Cor = (240, 214, 150, 255)
FUMACA: Cor = (96, 86, 80, 255)
ATERRO: Cor = (118, 102, 82, 255)
ATERRO_CLARO: Cor = (146, 128, 104, 255)
CHAO: Cor = (102, 92, 84, 255)
CALCADA: Cor = (148, 136, 120, 255)
