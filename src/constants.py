"""
constantes.py — Todas as constantes do projeto. Tudo em português.
"""
import pygame

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Tela e tempo
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LARGURA  = 800
ALTURA   = 600
TAM_TILE = 40          # tamanho de cada tile em pixels
FPS      = 60
COLUNAS  = LARGURA  // TAM_TILE   # 20 colunas
LINHAS   = ALTURA   // TAM_TILE   # 15 linhas

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Tipos de tile
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GRAMA       = 0
SOLO        = 1
SEMENTE     = 2   # semente comum plantada
SEMENTE_ESP = 3   # semente especial plantada
MUDA        = 4   # muda de árvore jovem
ARVORE      = 5   # árvore crescida
AGUA        = 6
PIER        = 7

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Identificadores de item do inventário (IDs internos)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ID_SEMENTE        = 'semente'
ID_SEMENTE_ESP    = 'semente_esp'
ID_MUDA           = 'muda'
ID_COLHEITA       = 'colheita'
ID_COLHEITA_ESP   = 'colheita_esp'
ID_MADEIRA        = 'madeira'
ID_PEIXE_COMUM    = 'peixe_comum'
ID_PEIXE_DOURADO  = 'peixe_dourado'
ID_PEIXE_RARO     = 'peixe_raro'

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Estado dos prédios
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ESTABULO_QUEBRADO    = 'estabulo_quebrado'
ESTABULO_FIXO        = 'estabulo_fixo'
GALINHEIRO_QUEBRADO  = 'galinheiro_quebrado'
GALINHEIRO_FIXO      = 'galinheiro_fixo'

CUSTO_REPARO = {
    ESTABULO_QUEBRADO:   {'dinheiro': 80, 'madeira': 10},
    GALINHEIRO_QUEBRADO: {'dinheiro': 40, 'madeira':  5},
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Tempo de crescimento das plantas (milissegundos)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEMPO_SEMENTE   = 15_000   # semente comum
TEMPO_ESPECIAL  = 30_000   # semente especial
TEMPO_MUDA      = 60_000   # muda crescer em árvore

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Preços
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Teclas padrão do jogador
# Os nomes das ações são usados como chaves no dicionário de teclas
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Minigame de pesca: lanes e padrões
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ACOES_PESCA  = ['esquerda', 'baixo', 'cima', 'direita']
LABELS_PESCA = ['A', 'S', 'W', 'D']
CORES_PESCA  = [
    (255,  80,  80),  # esquerda — vermelho
    ( 80, 220,  80),  # baixo    — verde
    ( 80, 150, 255),  # cima     — azul
    (255, 210,  50),  # direita  — amarelo
]

PADROES_PESCA_PADRAO = {
    'comum': {
        'nome':          'Peixinho',
        'cor':           (100, 180, 255),
        'icone':         'C',
        'bpm':           55,
        'padrao':        [(0,0),(1,2),(2,1),(3,3),(4,0),(5,2),(6,1),(7,3)],
        'queda_ms':      1800,
        'item_recompensa':  ID_PEIXE_COMUM,
        'qtd_recompensa':   1,
    },
    'dourado': {
        'nome':          'Peixe Dourado',
        'cor':           (255, 200, 50),
        'icone':         'D',
        'bpm':           75,
        'padrao':        [(0,0),(1,1),(2,0),(3,2),(4,1),(5,3),(6,2),(8,0),(9,1),(10,3),(11,2),(12,1)],
        'queda_ms':      1500,
        'item_recompensa':  ID_PEIXE_DOURADO,
        'qtd_recompensa':   1,
    },
    'raro': {
        'nome':          'Peixe Raro',
        'cor':           (180, 50, 255),
        'icone':         'R',
        'bpm':           100,
        'padrao':        [(0,0),(1,1),(2,2),(3,3),(4,0),(5,2),(6,1),(7,3),
                          (8,0),(9,1),(10,2),(11,0),(12,3),(13,1),(14,2),(15,3)],
        'queda_ms':      1200,
        'item_recompensa':  ID_PEIXE_RARO,
        'qtd_recompensa':   1,
    },
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Posições dos prédios na fazenda (col, lin, larg, alt) em tiles
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RET_CASA        = (0, 0, 4, 3)   # Casa:       cols 0-3,  linhas 0-2
RET_ESTABULO    = (0, 7, 4, 4)   # Estábulo:   cols 0-3,  linhas 7-10
RET_GALINHEIRO  = (6, 0, 3, 3)   # Galinheiro: cols 6-8,  linhas 0-2 (espaço de 2 cols da casa)

# Lago e pier de pesca
COLS_LAGO    = range(12, 20)
LINHAS_LAGO  = range( 9, 15)
COLS_PIER    = range( 9, 16)
LINHAS_PIER  = range(11, 13)
COL_PESCAR   = 15   # última coluna do pier acessível

# Spawn do jogador: dentro da casa
SPAWN_X = 64
SPAWN_Y = 50

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Cores de fallback (sem PNG)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COR_GRAMA   = ( 34, 139,  34)
COR_SOLO    = (139,  69,  19)
COR_PLANTADO = (  0, 190,   0)
COR_ESP     = (180,  80, 200)
COR_MUDA    = ( 80, 200,  80)
COR_ARVORE  = ( 30,  80,  30)
COR_AGUA    = ( 30, 100, 200)
COR_PIER    = (120,  80,  40)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Sistema de tempo interno
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HORA_INICIO        = 8    # hora de início do dia
HORA_FIM           = 24   # hora em que o jogador desmaia
MINUTOS_POR_TICK   = 10   # minutos de jogo por intervalo real
SEGUNDOS_POR_TICK  = 5    # segundos reais por intervalo

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Volumes padrão
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VOLUMES_PADRAO = {
    'animais':    0.8,
    'plantas':    0.6,
    'pesca':      0.8,
    'interface':  0.7,
    'musica':     0.5,
}

RESOLUCOES = [(800, 600), (1024, 768), (1280, 720)]
