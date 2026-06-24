import pygame


# Tela e tempo

LARGURA  = 800
ALTURA   = 600
TAM_TILE = 40
FPS      = 60
COLUNAS  = LARGURA  // TAM_TILE   # 20 colunas
LINHAS   = ALTURA   // TAM_TILE   # 15 linhas


# Tipos de tile

GRAMA        = 0
SOLO         = 1
SEMENTE      = 2
SEMENTE_ESP  = 3
MUDA         = 4
ARVORE       = 5
AGUA         = 6
PIER         = 7
COLHEITA     = 8
COLHEITA_ESP = 9


# Identificadores de item do inventario

ID_SEMENTE        = 'semente'
ID_SEMENTE_ESP    = 'semente_esp'
ID_MUDA           = 'muda'
ID_COLHEITA       = 'colheita'
ID_COLHEITA_ESP   = 'colheita_esp'
ID_MADEIRA        = 'madeira'
ID_PEIXE_COMUM    = 'peixe_comum'
ID_PEIXE_DOURADO  = 'peixe_dourado'
ID_PEIXE_RARO     = 'peixe_raro'


# Estado dos predios

ESTABULO_QUEBRADO    = 'estabulo_quebrado'
ESTABULO_FIXO        = 'estabulo_fixo'
GALINHEIRO_QUEBRADO  = 'galinheiro_quebrado'
GALINHEIRO_FIXO      = 'galinheiro_fixo'

CUSTO_REPARO = {
    ESTABULO_QUEBRADO:   {'dinheiro': 80, 'madeira': 10},
    GALINHEIRO_QUEBRADO: {'dinheiro': 40, 'madeira':  5},
}


# Tempo de crescimento das plantas (ms)

TEMPO_SEMENTE   = 15_000
TEMPO_ESPECIAL  = 30_000
TEMPO_MUDA      = 60_000


# Precos

PRECOS_VENDA = {
    ID_COLHEITA:      5,
    ID_COLHEITA_ESP: 15,
    ID_MADEIRA:       3,
    ID_PEIXE_COMUM:   8,
    ID_PEIXE_DOURADO: 25,
    ID_PEIXE_RARO:    60,
}

PRECOS_COMPRA = {
    ID_SEMENTE:     2,
    ID_SEMENTE_ESP: 8,
    ID_MUDA:        5,
}

CUSTO_ANIMAIS = {
    'vaca':    {'dinheiro': 50, 'nome': 'Vaca',    'predio': ESTABULO_FIXO},
    'galinha': {'dinheiro': 20, 'nome': 'Galinha', 'predio': GALINHEIRO_FIXO},
}


# Teclas padrao do jogador

TECLAS_PADRAO = {
    'cima':       pygame.K_w,
    'baixo':      pygame.K_s,
    'esquerda':   pygame.K_a,
    'direita':    pygame.K_d,
    'interagir':  pygame.K_e,
    'plantar':    pygame.K_p,
    'colher':     pygame.K_c,
    'pescar':     pygame.K_f,
    'cortar':     pygame.K_x,
    'ciclar':     pygame.K_TAB,
    'inventario': pygame.K_i,
}


# Minigame de pesca: lanes e padroes

ACOES_PESCA  = ['esquerda', 'baixo', 'cima', 'direita']
LABELS_PESCA = ['A', 'S', 'W', 'D']
CORES_PESCA  = [
    (255,  80,  80),  # esquerda
    ( 80, 220,  80),  # baixo
    ( 80, 150, 255),  # cima
    (255, 210,  50),  # direita
]

PADROES_PESCA_PADRAO = {
    'comum': {
        'nome':           'Peixinho',
        'cor':            (100, 180, 255),
        'icone':          'C',
        'bpm':            55,
        'padrao':         [(0,0),(1,2),(2,1),(3,3),(4,0),(5,2),(6,1),(7,3)],
        'queda_ms':       1800,
        'item_recompensa': ID_PEIXE_COMUM,
        'qtd_recompensa':  1,
    },
    'dourado': {
        'nome':           'Peixe Dourado',
        'cor':            (255, 200, 50),
        'icone':          'D',
        'bpm':            80,
        'padrao':         [(0,0),(1,1),(2,0),(3,2),(4,1),(5,3),(6,2),(7,0),
                           (8,3),(9,1),(10,3),(11,0),(12,2),(13,1),(14,3),(15,2)],
        'queda_ms':       1400,
        'item_recompensa': ID_PEIXE_DOURADO,
        'qtd_recompensa':  1,
    },
    'raro': {
        'nome':           'Peixe Raro',
        'cor':            (180, 50, 255),
        'icone':          'R',
        'bpm':            110,
        'padrao':         [(0,0),(1,1),(2,2),(3,3),(4,0),(5,2),(6,1),(7,3),
                           (8,2),(9,0),(10,3),(11,1),(12,2),(13,0),(14,3),(15,1),
                           (16,2),(17,3),(18,0),(19,1),(20,3),(21,2),(22,0),(23,3)],
        'queda_ms':       1100,
        'item_recompensa': ID_PEIXE_RARO,
        'qtd_recompensa':  1,
    },
}


# Posicoes dos predios na fazenda (col, lin, larg, alt)

RET_CASA        = (0, 0, 4, 3)
RET_ESTABULO    = (0, 7, 4, 4)
RET_GALINHEIRO  = (6, 0, 3, 3)

# Lago e pier de pesca
COLS_LAGO    = range(12, 20)
LINHAS_LAGO  = range( 9, 15)
COLS_PIER    = range( 9, 16)
LINHAS_PIER  = range(11, 13)
COL_PESCAR   = 15

SPAWN_X = 64
SPAWN_Y = 50

COR_PIER = (120, 80, 40)


# Sistema de tempo interno

HORA_INICIO        = 8
HORA_FIM           = 24
MINUTOS_POR_TICK   = 10
SEGUNDOS_POR_TICK  = 3


# Volume padrao (barra unica geral)

VOLUMES_PADRAO = {
    'geral': 0.4,
    'musica': 0.3,
}

RESOLUCOES = [(800, 600), (1024, 768), (1280, 720)]
