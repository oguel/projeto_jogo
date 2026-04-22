"""
recursos.py / assets.py — Gerenciador de recursos visuais e sonoros.

Tenta carregar arquivos da pasta assets/.
Se não encontrar, usa placeholder gerado proceduralmente com pygame.
"""
import pygame
import os
import math

# Caminho base do projeto (dois níveis acima: src/ → projeto_jogo/)
DIR_BASE    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_ASSETS  = os.path.join(DIR_BASE, 'assets')
DIR_IMAGENS = os.path.join(DIR_ASSETS, 'images')
DIR_SONS    = os.path.join(DIR_ASSETS, 'sounds')

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Mapeamento: chave → caminho de arquivo
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CAMINHOS_IMG = {
    # Jogador masculino
    'jogador_m_cima':    os.path.join(DIR_IMAGENS, 'jogador', 'jogador_m_cima.png'),
    'jogador_m_baixo':   os.path.join(DIR_IMAGENS, 'jogador', 'jogador_m_baixo.png'),
    'jogador_m_esq':     os.path.join(DIR_IMAGENS, 'jogador', 'jogador_m_esq.png'),
    'jogador_m_dir':     os.path.join(DIR_IMAGENS, 'jogador', 'jogador_m_dir.png'),
    # Jogadora feminina
    'jogador_f_cima':    os.path.join(DIR_IMAGENS, 'jogador', 'jogador_f_cima.png'),
    'jogador_f_baixo':   os.path.join(DIR_IMAGENS, 'jogador', 'jogador_f_baixo.png'),
    'jogador_f_esq':     os.path.join(DIR_IMAGENS, 'jogador', 'jogador_f_esq.png'),
    'jogador_f_dir':     os.path.join(DIR_IMAGENS, 'jogador', 'jogador_f_dir.png'),
    # Tiles do mapa
    'tile_grama':        os.path.join(DIR_IMAGENS, 'tiles', 'grama.png'),
    'tile_solo':         os.path.join(DIR_IMAGENS, 'tiles', 'solo.png'),
    'tile_semente':      os.path.join(DIR_IMAGENS, 'tiles', 'semente.png'),
    'tile_semente_esp':  os.path.join(DIR_IMAGENS, 'tiles', 'semente_esp.png'),
    'tile_muda':         os.path.join(DIR_IMAGENS, 'tiles', 'muda.png'),
    'tile_arvore':       os.path.join(DIR_IMAGENS, 'tiles', 'arvore.png'),
    'tile_agua':         os.path.join(DIR_IMAGENS, 'tiles', 'agua.png'),
    'tile_pier':         os.path.join(DIR_IMAGENS, 'tiles', 'pier.png'),
    # Prédios
    'casa':              os.path.join(DIR_IMAGENS, 'predios', 'casa.png'),
    'estabulo_quebrado': os.path.join(DIR_IMAGENS, 'predios', 'estabulo_quebrado.png'),
    'estabulo_fixo':     os.path.join(DIR_IMAGENS, 'predios', 'estabulo_fixo.png'),
    'galinheiro_quebrado': os.path.join(DIR_IMAGENS, 'predios', 'galinheiro_quebrado.png'),
    'galinheiro_fixo':   os.path.join(DIR_IMAGENS, 'predios', 'galinheiro_fixo.png'),
    # NPCs
    'npc_fazendeiro':    os.path.join(DIR_IMAGENS, 'npcs', 'fazendeiro.png'),
    'npc_pescador':      os.path.join(DIR_IMAGENS, 'npcs', 'pescador.png'),
    'npc_vendedor':      os.path.join(DIR_IMAGENS, 'npcs', 'vendedor.png'),
    'npc_construtor':    os.path.join(DIR_IMAGENS, 'npcs', 'construtor.png'),
    # Animais
    'animal_vaca':       os.path.join(DIR_IMAGENS, 'animais', 'vaca.png'),
    'animal_galinha':    os.path.join(DIR_IMAGENS, 'animais', 'galinha.png'),
    # UI do minigame de pesca
    'nota_esquerda':     os.path.join(DIR_IMAGENS, 'ui', 'nota_esq.png'),
    'nota_baixo':        os.path.join(DIR_IMAGENS, 'ui', 'nota_baixo.png'),
    'nota_cima':         os.path.join(DIR_IMAGENS, 'ui', 'nota_cima.png'),
    'nota_direita':      os.path.join(DIR_IMAGENS, 'ui', 'nota_dir.png'),
}

CAMINHOS_SOM = {
    'som_vaca':      os.path.join(DIR_SONS, 'animais',  'vaca.wav'),
    'som_galinha':   os.path.join(DIR_SONS, 'animais',  'galinha.wav'),
    'plantar':       os.path.join(DIR_SONS, 'plantas',  'plantar.wav'),
    'colher':        os.path.join(DIR_SONS, 'plantas',  'colher.wav'),
    'cortar':        os.path.join(DIR_SONS, 'plantas',  'cortar.wav'),
    'splash':        os.path.join(DIR_SONS, 'pesca',    'splash.wav'),
    'acerto_pesca':  os.path.join(DIR_SONS, 'pesca',    'acerto.wav'),
    'erro_pesca':    os.path.join(DIR_SONS, 'pesca',    'erro.wav'),
    'peixe_pego':    os.path.join(DIR_SONS, 'pesca',    'capturou.wav'),
    'clique':        os.path.join(DIR_SONS, 'interface', 'clique.wav'),
    'vender':        os.path.join(DIR_SONS, 'interface', 'vender.wav'),
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Cores de placeholder por chave
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_CORES_PLACEHOLDER = {
    'jogador_m_cima':    (0,100,255), 'jogador_m_baixo':  (0,100,255),
    'jogador_m_esq':     (0,100,255), 'jogador_m_dir':    (0,100,255),
    'jogador_f_cima':    (255,100,200), 'jogador_f_baixo':(255,100,200),
    'jogador_f_esq':     (255,100,200), 'jogador_f_dir':  (255,100,200),
    'tile_grama':        (34,139,34),  'tile_solo':       (139,69,19),
    'tile_semente':      (0,190,0),    'tile_semente_esp':(180,80,200),
    'tile_muda':         (80,200,80),  'tile_arvore':     (30,80,30),
    'tile_agua':         (30,100,200), 'tile_pier':       (120,80,40),
    'casa':              (180,140,100), 'estabulo_quebrado':(120,80,40),
    'estabulo_fixo':     (160,120,60), 'galinheiro_quebrado':(100,80,40),
    'galinheiro_fixo':   (140,100,60),
    'npc_fazendeiro':    (200,150,50), 'npc_pescador':    (50,150,200),
    'npc_vendedor':      (150,200,50), 'npc_construtor':  (200,100,50),
    'animal_vaca':       (200,180,100),'animal_galinha':  (255,200,50),
    'nota_esquerda':     (255,80,80),  'nota_baixo':      (80,220,80),
    'nota_cima':         (80,150,255), 'nota_direita':    (255,210,50),
}

_CACHE_IMAGEM: dict = {}
_CACHE_SOM:    dict = {}


def _criar_placeholder(chave: str, tamanho: tuple) -> pygame.Surface:
    """Gera uma Surface colorida como imagem de substituição."""
    cor  = _CORES_PLACEHOLDER.get(chave, (180, 180, 180))
    surf = pygame.Surface(tamanho, pygame.SRCALPHA)
    surf.fill((*cor, 220))
    pygame.draw.rect(surf, (0, 0, 0, 100), surf.get_rect(), 2)
    try:
        fonte = pygame.font.SysFont('arial', max(8, tamanho[1] // 4))
        rotulo = fonte.render(chave.split('_')[-1][:4], True, (0, 0, 0))
        surf.blit(rotulo, (2, tamanho[1] // 2 - rotulo.get_height() // 2))
    except Exception:
        pass
    return surf


def obter_imagem(chave: str, tamanho: tuple | None = None) -> pygame.Surface:
    """
    Retorna Surface para o recurso visual.
    Tenta arquivo PNG primeiro; se não existir, usa placeholder colorido.
    tamanho = (largura, altura) em pixels. Se None, usa TAM_TILE × TAM_TILE.
    """
    from src.constants import TAM_TILE
    if tamanho is None:
        tamanho = (TAM_TILE, TAM_TILE)

    chave_cache = (chave, tamanho)
    if chave_cache in _CACHE_IMAGEM:
        return _CACHE_IMAGEM[chave_cache]

    caminho = CAMINHOS_IMG.get(chave)
    surf    = None
    if caminho and os.path.isfile(caminho):
        try:
            carregado = pygame.image.load(caminho).convert_alpha()
            surf      = pygame.transform.smoothscale(carregado, tamanho)
        except Exception:
            surf = None

    if surf is None:
        surf = _criar_placeholder(chave, tamanho)

    _CACHE_IMAGEM[chave_cache] = surf
    return surf


def obter_som(chave: str) -> pygame.mixer.Sound | None:
    """Retorna Sound ou None se o arquivo não existir."""
    if chave in _CACHE_SOM:
        return _CACHE_SOM[chave]

    caminho = CAMINHOS_SOM.get(chave)
    som     = None
    if caminho and os.path.isfile(caminho):
        try:
            som = pygame.mixer.Sound(caminho)
        except Exception:
            som = None

    _CACHE_SOM[chave] = som
    return som


def tocar_som(chave: str, categoria: str = 'interface', volumes: dict | None = None):
    """Toca um som com o volume da categoria correspondente."""
    som = obter_som(chave)
    if som:
        volume = 1.0
        if volumes and categoria in volumes:
            volume = volumes[categoria]
        som.set_volume(max(0.0, min(1.0, volume)))
        som.play()


def limpar_cache():
    """Limpa o cache de imagens (útil ao trocar resolução)."""
    _CACHE_IMAGEM.clear()


def criar_pastas():
    """Cria a estrutura de pastas de assets se não existir."""
    subpastas = [
        os.path.join(DIR_IMAGENS, 'jogador'),
        os.path.join(DIR_IMAGENS, 'tiles'),
        os.path.join(DIR_IMAGENS, 'predios'),
        os.path.join(DIR_IMAGENS, 'npcs'),
        os.path.join(DIR_IMAGENS, 'animais'),
        os.path.join(DIR_IMAGENS, 'ui'),
        os.path.join(DIR_SONS, 'animais'),
        os.path.join(DIR_SONS, 'plantas'),
        os.path.join(DIR_SONS, 'pesca'),
        os.path.join(DIR_SONS, 'interface'),
    ]
    for pasta in subpastas:
        os.makedirs(pasta, exist_ok=True)

    # README com instruções de uso
    leia_me = os.path.join(DIR_ASSETS, 'LEIA-ME.txt')
    if not os.path.isfile(leia_me):
        with open(leia_me, 'w', encoding='utf-8') as arq:
            arq.write(
                "ASSETS DO FARM GAME\n"
                "===================\n\n"
                "Coloque seus arquivos PNG/WAV nas pastas abaixo.\n"
                "Enquanto nao existir arquivo, o jogo usa um placeholder colorido.\n\n"
                "images/jogador/\n"
                "  jogador_m_cima.png  jogador_m_baixo.png  jogador_m_esq.png  jogador_m_dir.png\n"
                "  jogador_f_cima.png  jogador_f_baixo.png  jogador_f_esq.png  jogador_f_dir.png\n"
                "  Tamanho sugerido: 32x48 px\n\n"
                "images/tiles/\n"
                "  grama.png  solo.png  semente.png  semente_esp.png\n"
                "  muda.png  arvore.png  agua.png  pier.png\n"
                "  Tamanho: 40x40 px\n\n"
                "images/predios/\n"
                "  casa.png  estabulo_quebrado.png  estabulo_fixo.png\n"
                "  galinheiro_quebrado.png  galinheiro_fixo.png\n\n"
                "images/npcs/\n"
                "  fazendeiro.png  pescador.png  vendedor.png  construtor.png\n\n"
                "images/animais/\n"
                "  vaca.png  galinha.png  Tamanho: 32x32 px\n\n"
                "images/ui/\n"
                "  nota_esq.png  nota_baixo.png  nota_cima.png  nota_dir.png  Tamanho: 50x50 px\n\n"
                "sounds/animais/   vaca.wav  galinha.wav\n"
                "sounds/plantas/   plantar.wav  colher.wav  cortar.wav\n"
                "sounds/pesca/     splash.wav  acerto.wav  erro.wav  capturou.wav\n"
                "sounds/interface/ clique.wav  vender.wav\n"
            )
