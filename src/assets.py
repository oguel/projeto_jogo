import pygame
import os

DIR_BASE    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_ASSETS  = os.path.join(DIR_BASE, 'assets')
DIR_IMAGENS = os.path.join(DIR_ASSETS, 'images')
DIR_SONS    = os.path.join(DIR_ASSETS, 'sounds')

_JOGADOR = os.path.join(DIR_IMAGENS, 'jogador')
_TILES   = os.path.join(DIR_IMAGENS, 'tiles')
_ANIMAIS = os.path.join(DIR_IMAGENS, 'animais')
_PLANTAS = os.path.join(DIR_IMAGENS, 'plantas')
_PREDIOS = os.path.join(DIR_IMAGENS, 'predios')
_UI      = os.path.join(DIR_IMAGENS, 'ui')

CAMINHOS_IMG = {
    # Jogador - 4 direcoes
    'jogador_down':  os.path.join(_JOGADOR, 'Player_down_15-20.png'),
    'jogador_up':    os.path.join(_JOGADOR, 'Player_up_15-20.png'),
    'jogador_left':  os.path.join(_JOGADOR, 'Player_left_15-20.png'),
    'jogador_right': os.path.join(_JOGADOR, 'Player_right_15-20.png'),

    # Tiles do mapa
    'tile_grama':       os.path.join(_TILES,   'Grass_Middle_16-16.png'),
    'tile_solo':        os.path.join(_TILES,   'FarmLand_Tile_48-48.png'),
    'tile_semente':     os.path.join(_PLANTAS, 'trigo_plantado_15-15.png'),
    'tile_semente_esp': os.path.join(_PLANTAS, 'cenoura_plantada_15-15.png'),
    'tile_muda':        os.path.join(_PLANTAS, 'Oak_Tree_Small_12-16.png'),
    'tile_arvore':      os.path.join(_PLANTAS, 'Oak_Tree_42-70.png'),
    'tile_agua':        os.path.join(_TILES,   'Water_Middle_16-16.png'),
    'tile_pier':        os.path.join(_TILES,   'Bridge_Wood_38-30.png'),

    # Bordas da agua
    'agua_borda_cima':  os.path.join(_TILES, 'Water_up_borda_16-16.png'),
    'agua_borda_baixo': os.path.join(_TILES, 'Water_down_borda_16-16.png'),
    'agua_borda_esq':   os.path.join(_TILES, 'Water_left_borda_16-16.png'),
    'agua_borda_dir':   os.path.join(_TILES, 'Water_right_borda_16-16.png'),
    'agua_quina':       os.path.join(_TILES, 'Water_quina_16-16.png'),

    # Chao da cidade
    'chao_cidade': os.path.join(_TILES, 'Path_Middle_16-16.png'),

    # Predios
    'casa':          os.path.join(_PREDIOS, 'House_75-115.png'),
    'casa_vila':     os.path.join(_PREDIOS, 'casa_vila_63-74.png'),
    'casa_pescador': os.path.join(_PREDIOS, 'casa_pescador_76-76.png'),
    'estabulo':      os.path.join(_PREDIOS, 'barn_140-140.png'),
    'cerca':         os.path.join(_PREDIOS, 'Fences_8-17.png'),
    'lampada':       os.path.join(_PREDIOS, 'lampada_16-42.png'),

    # Animais
    'animal_galinha':     os.path.join(_ANIMAIS, 'Chicken_16-16.png'),
    'animal_galinha_dir': os.path.join(_ANIMAIS, 'Chicken_16-16-dir.png'),
    'animal_vaca':        os.path.join(_ANIMAIS, 'Cow_25-20.png'),
    'animal_vaca_dir':    os.path.join(_ANIMAIS, 'Cow_25-20-dir.png'),

    # Colheitas
    'colheita':     os.path.join(_PLANTAS, 'trigo_pronto_15-15.png'),
    'colheita_esp': os.path.join(_PLANTAS, 'cenoura_pronta_15-15.png'),

    # UI
    'titlescreen': os.path.join(_UI, 'Titlescreen.png'),
}

CAMINHOS_SOM = {
    # SFX
    'arando':   os.path.join(DIR_SONS, 'somArando.mp3'),
    'colhendo': os.path.join(DIR_SONS, 'somColhendo.mp3'),
    'tecla':    os.path.join(DIR_SONS, 'somTecla.mp3'),
    'galinha':  os.path.join(DIR_SONS, 'somGalinha.mp3'),
    'vaca':     os.path.join(DIR_SONS, 'somVaca.mp3'),
    # Legado (mantido para compatibilidade)
    'vender':   os.path.join(DIR_SONS, 'somTecla.mp3'),
}

CAMINHOS_MUSICA = {
    'musica_fazenda': os.path.join(DIR_SONS, 'somFazenda.mp3'),
    'musica_cidade':  os.path.join(DIR_SONS, 'somCidade.mp3'),
}

_CACHE_IMAGEM: dict = {}
_CACHE_SOM:    dict = {}
_MUSICA_ATUAL: str  = ''


def obter_imagem(chave: str, tamanho: tuple | None = None) -> pygame.Surface:
    from src.constants import TAM_TILE
    if tamanho is None:
        tamanho = (TAM_TILE, TAM_TILE)

    chave_cache = (chave, tamanho)
    if chave_cache in _CACHE_IMAGEM:
        return _CACHE_IMAGEM[chave_cache]

    caminho = CAMINHOS_IMG.get(chave, '')
    surf    = None
    if caminho and os.path.isfile(caminho):
        try:
            surf = pygame.transform.scale(
                pygame.image.load(caminho).convert_alpha(), tamanho)
        except Exception:
            pass

    if surf is None:
        surf = pygame.Surface(tamanho, pygame.SRCALPHA)
        surf.fill((180, 0, 180, 180))

    _CACHE_IMAGEM[chave_cache] = surf
    return surf


def obter_imagem_original(chave: str) -> pygame.Surface | None:
    """Retorna a imagem em tamanho original (sem escalar)."""
    caminho = CAMINHOS_IMG.get(chave, '')
    if caminho and os.path.isfile(caminho):
        try:
            return pygame.image.load(caminho).convert_alpha()
        except Exception:
            pass
    return None


def obter_som(chave: str) -> pygame.mixer.Sound | None:
    if chave in _CACHE_SOM:
        return _CACHE_SOM[chave]
    caminho = CAMINHOS_SOM.get(chave, '')
    som     = None
    if caminho and os.path.isfile(caminho):
        try:
            som = pygame.mixer.Sound(caminho)
        except Exception:
            pass
    _CACHE_SOM[chave] = som
    return som


def tocar_som(chave: str, volumes: dict | None = None):
    """Toca um SFX aplicando o volume geral."""
    som = obter_som(chave)
    if som:
        vol = volumes.get('geral', 1.0) if volumes else 1.0
        som.set_volume(max(0.0, min(1.0, vol)))
        som.play()


def tocar_musica(chave: str, volumes: dict | None = None):
    """Inicia uma musica em loop. Se ja estiver tocando a mesma, nao reinicia."""
    global _MUSICA_ATUAL
    caminho = CAMINHOS_MUSICA.get(chave, '')
    if not caminho or not os.path.isfile(caminho):
        return
    if _MUSICA_ATUAL == chave:
        # Apenas atualiza o volume
        atualizar_volume_musica(volumes)
        return
    try:
        pygame.mixer.music.load(caminho)
        vol = volumes.get('musica', 0.5) if volumes else 0.5
        pygame.mixer.music.set_volume(max(0.0, min(1.0, vol)))
        pygame.mixer.music.play(-1)  # -1 = loop infinito
        _MUSICA_ATUAL = chave
    except Exception:
        pass


def parar_musica():
    global _MUSICA_ATUAL
    try:
        pygame.mixer.music.stop()
    except Exception:
        pass
    _MUSICA_ATUAL = ''


def atualizar_volume_musica(volumes: dict | None = None):
    """Atualiza o volume da musica em reproducao."""
    vol = volumes.get('musica', 0.5) if volumes else 0.5
    try:
        pygame.mixer.music.set_volume(max(0.0, min(1.0, vol)))
    except Exception:
        pass


def limpar_cache():
    _CACHE_IMAGEM.clear()


def criar_pastas():
    for pasta in [_JOGADOR, _TILES, _PREDIOS, _ANIMAIS, _PLANTAS, _UI]:
        os.makedirs(pasta, exist_ok=True)
