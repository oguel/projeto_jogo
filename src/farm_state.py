import pygame
import math
import random

from src.states    import EstadoBase, FONTES
from src.constants import (
    TAM_TILE, COLUNAS, LINHAS,
    GRAMA, SOLO, SEMENTE, SEMENTE_ESP,
    MUDA, ARVORE, AGUA, PIER, COLHEITA, COLHEITA_ESP,
    ID_SEMENTE, ID_SEMENTE_ESP, ID_MUDA,
    ID_COLHEITA, ID_COLHEITA_ESP, ID_MADEIRA,
    COLS_LAGO, LINHAS_LAGO, COLS_PIER, LINHAS_PIER, COL_PESCAR,
    RET_CASA, RET_ESTABULO, RET_GALINHEIRO,
    TEMPO_SEMENTE, TEMPO_ESPECIAL, TEMPO_MUDA,
    ESTABULO_QUEBRADO, ESTABULO_FIXO, GALINHEIRO_QUEBRADO, GALINHEIRO_FIXO,
    SPAWN_X, SPAWN_Y,
)
from src import assets as RECURSOS
from src.entities import Jogador, atualizar_animais, desenhar_animais


# Conjuntos de tiles especiais

TILES_LAGO   = frozenset((c, r) for c in COLS_LAGO   for r in LINHAS_LAGO)
TILES_PIER   = frozenset((c, r) for c in COLS_PIER   for r in LINHAS_PIER
                          if c != COL_PESCAR)
TILES_PESCA  = frozenset((COL_PESCAR, r) for r in LINHAS_PIER)
TILES_AGUA   = TILES_LAGO | TILES_PIER | TILES_PESCA

# Tamanho da quina de agua em pixels
QUINA_TAM = 52 


def _tiles_predio(col, lin, larg, alt):
    return frozenset((col + x, lin + y) for x in range(larg) for y in range(alt))


TILES_CASA       = _tiles_predio(*RET_CASA)
TILES_ESTABULO   = _tiles_predio(*RET_ESTABULO)
TILES_GALINHEIRO = _tiles_predio(*RET_GALINHEIRO)
TILES_BLOQUEADOS = TILES_CASA | TILES_ESTABULO | TILES_GALINHEIRO


def _tiles_para_pixels(col, lin, larg, alt):
    return pygame.Rect(col * TAM_TILE, lin * TAM_TILE, larg * TAM_TILE, alt * TAM_TILE)


RET_PX_CASA       = _tiles_para_pixels(*RET_CASA)         
RET_PX_ESTABULO   = _tiles_para_pixels(*RET_ESTABULO)     
RET_PX_GALINHEIRO = _tiles_para_pixels(*RET_GALINHEIRO)   

# Caixa de venda (canto superior direito)
CAIXA_VENDA = pygame.Rect(COLUNAS * TAM_TILE - 90, 10, 80, 34)

# Cama dentro da casa
RET_CAMA = pygame.Rect(
    RET_PX_CASA.x + RET_PX_CASA.width  - 52,
    RET_PX_CASA.y + 22,
    44, 28
)


def _criar_paredes(ret, larg_porta):
    """Cria 5 retângulos de colisão com abertura de porta no centro-sul."""
    x, y, w, h = ret.x, ret.y, ret.width, ret.height
    esq_porta  = x + w // 2 - larg_porta // 2
    dir_porta  = esq_porta + larg_porta
    return [
        pygame.Rect(x,     y,     w,             4),    
        pygame.Rect(x,     y,     4,             h),   
        pygame.Rect(x+w-4, y,     4,             h),    
        pygame.Rect(x,     y+h-4, esq_porta - x, 4),  
        pygame.Rect(dir_porta, y+h-4, x+w-dir_porta, 4), 
    ]


def _criar_paredes_casa():
    r  = RET_PX_CASA
    x, y, w, h = r.x, r.y, r.width, r.height
    larg_porta = 60
    esq_porta  = x + 68 - larg_porta // 2   # porta ~68px da esquerda no sprite
    dir_porta  = esq_porta + larg_porta
    return [
        pygame.Rect(x,         y,     w,             4),
        pygame.Rect(x,         y,     4,             h),
        pygame.Rect(x+w-4,     y,     4,             h),
        pygame.Rect(x,         y+h-4, esq_porta - x, 4),
        pygame.Rect(dir_porta, y+h-4, x+w-dir_porta, 4),
    ]


PAREDES_CASA       = _criar_paredes_casa()
PAREDES_ESTABULO   = _criar_paredes(RET_PX_ESTABULO,   80)
PAREDES_GALINHEIRO = _criar_paredes(RET_PX_GALINHEIRO, 56)


def _inicializar_mapa():
    """Cria o mapa inicial da fazenda com grama e água nos tiles certos."""
    grade = [[GRAMA] * COLUNAS for _ in range(LINHAS)]
    for (c, r) in TILES_AGUA:
        if 0 <= r < LINHAS and 0 <= c < COLUNAS:
            grade[r][c] = AGUA
    return grade




# EstadoFazenda

class EstadoFazenda(EstadoBase):
    def __init__(self, dados_jogo):
        self.gd  = dados_jogo
        self.cfg = dados_jogo.configuracao
        self.inv = dados_jogo.inventario
        self.hor = dados_jogo.horario
        self.jog = dados_jogo.jogador

        if dados_jogo.mapa_fazenda is None:
            dados_jogo.mapa_fazenda = _inicializar_mapa()
        self.mapa = dados_jogo.mapa_fazenda
        self.tp   = dados_jogo.timer_plantas   # timer_plantas: {(col,lin): timestamp}

        self._tick_agua   = 0
        self._msg_venda   = ''
        self._timer_msg   = 0
        self.dialogo      = None
        self._ver_inv     = False

        dados_jogo.ultimo_mapa = 'fazenda'

        # Inicia musica da fazenda
        RECURSOS.tocar_musica('musica_fazenda', self.cfg.volumes)

        # Timers para sons de animais (intervalo minimo de 7 segundos)
        agora = pygame.time.get_ticks()
        self._ultimo_som_galinha = agora
        self._intervalo_galinha  = random.randint(7000, 16000)
        self._ultimo_som_vaca    = agora
        self._intervalo_vaca     = random.randint(7000, 16000)

 
    # Processar eventos

    def processar_eventos(self, eventos: list):
        # Repassa eventos para o diálogo se estiver aberto
        if self.dialogo:
            if not self.dialogo.processar_eventos(eventos, self.cfg.teclas, self.cfg.volumes):
                self.dialogo = None
            return self

        for evento in eventos:
            if evento.type != pygame.KEYDOWN:
                continue
            tecla  = evento.key
            mapa_t = self.cfg.teclas   # mapa de teclas do jogador

            # ESC: fecha inventário ou abre configurações
            if tecla == pygame.K_ESCAPE:
                if self._ver_inv:
                    self._ver_inv = False
                    continue
                from src.settings_state import EstadoConfiguracoes
                return EstadoConfiguracoes(self.gd, estado_anterior=self)

            # I: abre/fecha inventário completo
            if tecla == mapa_t.get('inventario', pygame.K_i):
                self._ver_inv = not self._ver_inv
                continue

            # F12: cheat de debug
            if tecla == pygame.K_F12:
                self.inv.dinheiro += 200
                self.inv.madeira  += 50
                self._msg_venda = 'Debug: +$200 e +50 madeiras'
                self._timer_msg = pygame.time.get_ticks()
                continue

            # Bloqueia outras ações com inventário aberto
            if self._ver_inv:
                continue

            col_tile, lin_tile = self.jog.posicao_tile()

            # TAB / ciclar: troca semente ativa
            if tecla == mapa_t.get('ciclar', pygame.K_TAB):
                self.inv.ciclar_semente()

            # E / interagir: dormir, arar terra, vender
            if tecla == mapa_t.get('interagir', pygame.K_e):
                if self._perto_da_cama():
                    return self._dormir()
                self._tentar_arar(col_tile, lin_tile)
                self._tentar_vender()

            # P / plantar
            if tecla == mapa_t.get('plantar', pygame.K_p):
                self._tentar_plantar(col_tile, lin_tile)

            # C / colher
            if tecla == mapa_t.get('colher', pygame.K_c):
                self._tentar_colher(col_tile, lin_tile)

            # X / cortar árvore
            if tecla == mapa_t.get('cortar', pygame.K_x):
                self._tentar_cortar(col_tile, lin_tile)

            # F / pescar
            if tecla == mapa_t.get('pescar', pygame.K_f):
                if self._no_ponto_de_pesca():
                    if not self.gd.tem_vara:
                        self._msg_venda = 'Compre uma Vara de Pesca com o Pescador!'
                        self._timer_msg = pygame.time.get_ticks()
                    else:
                        from src.fishing_state import EstadoPesca
                        return EstadoPesca(self.gd)

        return self

    # Ações do jogador

    def _perto_da_cama(self) -> bool:
        return RET_CAMA.inflate(30, 30).colliderect(self.jog.obter_ret())

    def _dormir(self):
        """Inicia a sequência de dormir voluntariamente."""
        self.gd.dormiu_voluntario = True
        self.gd.horario.reiniciar_dia()
        jog = self.gd.jogador
        if jog:
            jog.x       = float(SPAWN_X)
            jog.y       = float(SPAWN_Y)
            jog.pescando = False
            jog.direcao  = 'baixo'
        self.gd.salvar()   # salva ao dormir
        from src.states import EstadoDesmaio
        return EstadoDesmaio(self.gd)

    def _tentar_arar(self, col, lin):
        if not self._tile_valido(col, lin): return
        if self.mapa[lin][col] == GRAMA:
            self.mapa[lin][col] = SOLO
            RECURSOS.tocar_som('arando', self.cfg.volumes)

    def _tentar_vender(self):
        if CAIXA_VENDA.colliderect(self.jog.obter_ret()):
            ganhou = self.inv.vender_tudo()
            if ganhou:
                self._msg_venda = f'Vendido: ${ganhou}!'
                self._timer_msg = pygame.time.get_ticks()
                RECURSOS.tocar_som('tecla', self.cfg.volumes)

    def _tentar_plantar(self, col, lin):
        if not self._tile_valido(col, lin): return
        if self.mapa[lin][col] != SOLO: return
        ativa = self.inv.semente_ativa
        agora = pygame.time.get_ticks()
        tocou = False
        if ativa == ID_SEMENTE and self.inv.semente > 0:
            self.inv.semente        -= 1
            self.mapa[lin][col]      = SEMENTE
            self.tp[(col, lin)]     = agora
            tocou = True
        elif ativa == ID_SEMENTE_ESP and self.inv.semente_esp > 0:
            self.inv.semente_esp    -= 1
            self.mapa[lin][col]      = SEMENTE_ESP
            self.tp[(col, lin)]     = agora
            tocou = True
        elif ativa == ID_MUDA and self.inv.muda > 0:
            self.inv.muda           -= 1
            self.mapa[lin][col]      = MUDA
            self.tp[(col, lin)]     = agora
            tocou = True

        if tocou:
            RECURSOS.tocar_som('colhendo', self.cfg.volumes)

    def _tentar_colher(self, col, lin):
        if not self._tile_valido(col, lin): return
        tile = self.mapa[lin][col]
        tocou = False
        if tile == COLHEITA:
            self.mapa[lin][col]   = SOLO
            self.inv.colheita    += 1
            del self.tp[(col, lin)]
            tocou = True
        elif tile == COLHEITA_ESP:
            self.mapa[lin][col]   = SOLO
            self.inv.colheita_esp += 1
            del self.tp[(col, lin)]
            tocou = True

        if tocou:
            RECURSOS.tocar_som('colhendo', self.cfg.volumes)

    def _tentar_cortar(self, col, lin):
        if not self._tile_valido(col, lin): return
        tile  = self.mapa[lin][col]
        idade = pygame.time.get_ticks() - self.tp.get((col, lin), pygame.time.get_ticks())
        if tile == MUDA and idade >= TEMPO_MUDA:
            self.mapa[lin][col] = GRAMA
            self.inv.madeira   += random.randint(2, 4)
            self.tp.pop((col, lin), None)
            RECURSOS.tocar_som('tecla', self.cfg.volumes)
        elif tile == ARVORE:
            self.mapa[lin][col] = GRAMA
            self.inv.madeira   += random.randint(3, 6)
            self.tp.pop((col, lin), None)
            RECURSOS.tocar_som('tecla', self.cfg.volumes)

    def _no_ponto_de_pesca(self) -> bool:
        col, lin = self.jog.posicao_tile()
        return (col, lin) in TILES_PESCA and self.jog.direcao == 'direita'

    def _tile_valido(self, col, lin) -> bool:
        if not (0 <= col < COLUNAS and 0 <= lin < LINHAS): return False
        if (col, lin) in TILES_BLOQUEADOS:                  return False
        if (col, lin) in TILES_AGUA:                        return False
        return True


    # Atualização por frame
 
    def atualizar(self):
        teclas_press = pygame.key.get_pressed()
        colisoes     = self._colisoes()
        self.jog.mover(teclas_press, self.cfg.teclas, colisoes)

        # Limita o jogador ao mapa
        self.jog.x = max(0.0, min(self.jog.x, (COLUNAS - 1) * TAM_TILE - 4))
        self.jog.y = max(0.0, min(self.jog.y, (LINHAS  - 1) * TAM_TILE - 4))

        # Jogador chegou à borda direita -> vai para a cidade
        if self.jog.x > (COLUNAS - 1) * TAM_TILE - 8:
            self.jog.x = 300.0
            self.jog.y = 300.0
            self.gd.salvar()   # salva ao entrar na cidade
            from src.town_state import EstadoCidade
            return EstadoCidade(self.gd)

        # Muda crescida em árvore
        agora = pygame.time.get_ticks()
        for (c, l), t in list(self.tp.items()):
            tile = self.mapa[l][c]
            if tile == SEMENTE     and agora - t >= TEMPO_SEMENTE:  self.mapa[l][c] = COLHEITA
            elif tile == SEMENTE_ESP and agora - t >= TEMPO_ESPECIAL: self.mapa[l][c] = COLHEITA_ESP
            elif tile == MUDA        and agora - t >= TEMPO_MUDA:     self.mapa[l][c] = ARVORE

        # Atualiza animais
        atualizar_animais(self.gd.animais)
        self._tick_agua += 1

        # Sons de animais aleatorios (cooldown minimo de 7 segundos)
        tem_galinha = any(a['tipo'] == 'galinha' for a in self.gd.animais)
        tem_vaca    = any(a['tipo'] == 'vaca' for a in self.gd.animais)

        if tem_galinha and (agora - self._ultimo_som_galinha > self._intervalo_galinha):
            RECURSOS.tocar_som('galinha', self.cfg.volumes)
            self._ultimo_som_galinha = agora
            self._intervalo_galinha  = random.randint(7000, 16000)

        if tem_vaca and (agora - self._ultimo_som_vaca > self._intervalo_vaca):
            RECURSOS.tocar_som('vaca', self.cfg.volumes)
            self._ultimo_som_vaca = agora
            self._intervalo_vaca  = random.randint(7000, 16000)

        return self._verificar_hora()

    def _colisoes(self) -> list:
        """Retorna todos os retângulos de colisão do mapa."""
        rects = list(PAREDES_CASA) + list(PAREDES_ESTABULO) + list(PAREDES_GALINHEIRO)
        for (c, r) in TILES_LAGO:
            if (c, r) not in TILES_PIER and (c, r) not in TILES_PESCA:
                rects.append(pygame.Rect(c * TAM_TILE, r * TAM_TILE, TAM_TILE, TAM_TILE))
        return rects

    def _verificar_hora(self):
        """Verifica se chegou meia-noite ou horário de ficar cansado."""
        if self.hor.eh_meia_noite():
            self.gd.horario.reiniciar_dia()
            self.gd.salvar()   # salva ao ser forçado a dormir
            from src.states import EstadoDesmaio
            return EstadoDesmaio(self.gd)
        if self.hor.hora_cansado() and not self.hor.notificado_cansado:
            self.hor.notificado_cansado = True
            self.gd.msg_cansado         = True
            self.gd.timer_msg_cansado   = pygame.time.get_ticks()
        return None

    # Propriedades: jogador dentro dos prédios
    @property
    def _dentro_casa(self):
        return RET_PX_CASA.inflate(-6, -6).colliderect(self.jog.obter_ret())

    @property
    def _dentro_estabulo(self):
        return RET_PX_ESTABULO.inflate(-6, -6).colliderect(self.jog.obter_ret())

    @property
    def _dentro_galinheiro(self):
        return RET_PX_GALINHEIRO.inflate(-6, -6).colliderect(self.jog.obter_ret())


    # Desenho
   
    def desenhar(self, tela: pygame.Surface):
        largura, altura = tela.get_size()
        fonte_p = FONTES.get('pequena', pygame.font.SysFont('arial', 14))
        fonte_n = FONTES.get('normal',  pygame.font.SysFont('arial', 18))
        fonte_g = FONTES.get('grande',  pygame.font.SysFont('arial', 28, bold=True))
        agora   = pygame.time.get_ticks()

        def _agua_base(rx, ry, col, lin):
            onda = math.sin(self._tick_agua * 0.05 + col * 0.5 + lin * 0.3)
            nv   = int(onda * 10)
            sa   = RECURSOS.obter_imagem('tile_agua', (TAM_TILE, TAM_TILE)).copy()
            if nv != 0:
                t = pygame.Surface((TAM_TILE, TAM_TILE), pygame.SRCALPHA)
                v = max(0, min(30, nv + 15))
                t.fill((0, v, v, 0))
                sa.blit(t, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            tela.blit(sa, (rx, ry))

        _grama  = RECURSOS.obter_imagem('tile_grama',       (TAM_TILE, TAM_TILE))
        _bc     = RECURSOS.obter_imagem('agua_borda_cima',  (TAM_TILE, TAM_TILE))
        _bb     = RECURSOS.obter_imagem('agua_borda_baixo', (TAM_TILE, TAM_TILE))
        _be     = RECURSOS.obter_imagem('agua_borda_esq',   (TAM_TILE, TAM_TILE))
        _bd     = RECURSOS.obter_imagem('agua_borda_dir',   (TAM_TILE, TAM_TILE))
        _bq     = RECURSOS.obter_imagem('agua_quina',       (TAM_TILE, TAM_TILE))

        # Tiles do mapa
        for lin in range(LINHAS):
            for col in range(COLUNAS):
                rx, ry = col * TAM_TILE, lin * TAM_TILE
                pos    = (col, lin)
                tile   = self.mapa[lin][col]

                if pos in TILES_PESCA or pos in TILES_PIER:
                    if pos in TILES_LAGO:
                        _agua_base(rx, ry, col, lin)
                        if (col-1, lin) not in TILES_LAGO:
                            tela.blit(_be, (rx, ry))
                    else:
                        tela.blit(_grama, (rx, ry))
                    if pos in TILES_PESCA:
                        pygame.draw.circle(tela, (80, 200, 255),
                                           (rx + TAM_TILE//2, ry + TAM_TILE//2), 6)

                elif pos in TILES_LAGO:
                    _agua_base(rx, ry, col, lin)

                    tc = (col, lin-1) not in TILES_LAGO
                    tb = (col, lin+1) not in TILES_LAGO
                    te = (col-1, lin) not in TILES_LAGO
                    td = (col+1, lin) not in TILES_LAGO

                    if tc: tela.blit(_bc, (rx, ry))
                    if tb: tela.blit(_bb, (rx, ry))
                    if te: tela.blit(_be, (rx, ry))
                    if td: tela.blit(_bd, (rx, ry))

                    if tc and te and (col-1, lin-1) not in TILES_LAGO:
                        q = pygame.transform.scale(_bq, (QUINA_TAM, QUINA_TAM))
                        tela.blit(q, (rx, ry))
                    if tc and td and (col+1, lin-1) not in TILES_LAGO:
                        q = pygame.transform.scale(pygame.transform.flip(_bq, True, False), (QUINA_TAM, QUINA_TAM))
                        tela.blit(q, (rx + TAM_TILE - QUINA_TAM, ry))
                    if tb and te and (col-1, lin+1) not in TILES_LAGO:
                        q = pygame.transform.scale(pygame.transform.flip(_bq, False, True), (QUINA_TAM, QUINA_TAM))
                        tela.blit(q, (rx, ry + TAM_TILE - QUINA_TAM))
                    if tb and td and (col+1, lin+1) not in TILES_LAGO:
                        q = pygame.transform.scale(pygame.transform.flip(_bq, True, True), (QUINA_TAM, QUINA_TAM))
                        tela.blit(q, (rx + TAM_TILE - QUINA_TAM, ry + TAM_TILE - QUINA_TAM))


                else:
                    # -- Grama base para tudo --
                    tela.blit(RECURSOS.obter_imagem('tile_grama', (TAM_TILE, TAM_TILE)), (rx, ry))

                    if tile == SOLO:
                        tela.blit(RECURSOS.obter_imagem('tile_solo', (TAM_TILE, TAM_TILE)), (rx, ry))

                    elif tile == SEMENTE:
                        tela.blit(RECURSOS.obter_imagem('tile_solo',    (TAM_TILE, TAM_TILE)), (rx, ry))
                        # Sprite de planta centralizado sobre o tile
                        sp  = RECURSOS.obter_imagem('tile_semente', (TAM_TILE - 8, TAM_TILE - 8))
                        tela.blit(sp, (rx + 4, ry + 4))
                        # Barra de progresso
                        pct = min(1.0, (agora - self.tp.get(pos, agora)) / TEMPO_SEMENTE)
                        pygame.draw.rect(tela, (40, 200, 40),
                                         (rx, ry + TAM_TILE - 5, int(TAM_TILE * pct), 4))

                    elif tile == SEMENTE_ESP:
                        tela.blit(RECURSOS.obter_imagem('tile_solo',        (TAM_TILE, TAM_TILE)), (rx, ry))
                        sp  = RECURSOS.obter_imagem('tile_semente_esp', (TAM_TILE - 8, TAM_TILE - 8))
                        tela.blit(sp, (rx + 4, ry + 4))
                        pct = min(1.0, (agora - self.tp.get(pos, agora)) / TEMPO_ESPECIAL)
                        pygame.draw.rect(tela, (200, 80, 220),
                                         (rx, ry + TAM_TILE - 5, int(TAM_TILE * pct), 4))

                    elif tile == COLHEITA:
                        tela.blit(RECURSOS.obter_imagem('tile_solo',     (TAM_TILE, TAM_TILE)), (rx, ry))
                        sp = RECURSOS.obter_imagem('colheita', (TAM_TILE - 4, TAM_TILE - 4))
                        tela.blit(sp, (rx + 2, ry + 2))
                        pygame.draw.rect(tela, (255, 220, 30), (rx, ry, TAM_TILE, TAM_TILE), 2)

                    elif tile == COLHEITA_ESP:
                        tela.blit(RECURSOS.obter_imagem('tile_solo',         (TAM_TILE, TAM_TILE)), (rx, ry))
                        sp = RECURSOS.obter_imagem('colheita_esp', (TAM_TILE - 4, TAM_TILE - 4))
                        tela.blit(sp, (rx + 2, ry + 2))
                        pygame.draw.rect(tela, (180, 60, 220), (rx, ry, TAM_TILE, TAM_TILE), 2)

                    elif tile == MUDA:
                        # Muda pequena sobre grama
                        sp  = RECURSOS.obter_imagem('tile_muda', (TAM_TILE - 14, TAM_TILE - 6))
                        tela.blit(sp, (rx + 7, ry + 3))
                        pct = min(1.0, (agora - self.tp.get(pos, agora)) / TEMPO_MUDA)
                        pygame.draw.rect(tela, (80, 200, 80),
                                         (rx, ry + TAM_TILE - 5, int(TAM_TILE * pct), 4))

                    elif tile == ARVORE:
                        sw, sh = 44, 72
                        sp = RECURSOS.obter_imagem('tile_arvore', (sw, sh))
                        tela.blit(sp, (rx - 2, ry - 32))

        # Ponte: um sprite por coluna cobrindo as 2 linhas do pier
        lin_topo = min(LINHAS_PIER)
        bw = 38
        bh = len(LINHAS_PIER) * TAM_TILE
        surf_pier = RECURSOS.obter_imagem('tile_pier', (bw, bh))
        todas_cols_pier = set(c for (c, r) in TILES_PIER | TILES_PESCA)
        for cp in sorted(todas_cols_pier):
            px = cp * TAM_TILE + (TAM_TILE - bw) // 2
            py = lin_topo * TAM_TILE
            tela.blit(surf_pier, (px, py))
            if (cp, lin_topo) in TILES_PESCA or (cp, lin_topo+1) in TILES_PESCA:
                pygame.draw.circle(tela, (80, 200, 255),
                                   (cp * TAM_TILE + TAM_TILE//2, py + bh//2), 6)

        self._desenhar_casa(tela, fonte_p)
        self._desenhar_estabulo(tela, fonte_p)
        self._desenhar_galinheiro(tela, fonte_p)
        self._desenhar_cerca_galinheiro(tela)

        # -- Interiores (só visíveis ao entrar) -------------------
        if self._dentro_casa:
            self._desenhar_interior_casa(tela)
        if self._dentro_estabulo:
            self._desenhar_interior_estabulo(tela)
            vacas = [a for a in self.gd.animais if a['tipo'] == 'vaca']
            desenhar_animais(tela, vacas)
        if self._dentro_galinheiro:
            self._desenhar_interior_galinheiro(tela)
            galinhas = [a for a in self.gd.animais if a['tipo'] == 'galinha']
            desenhar_animais(tela, galinhas)

        # -- Caixa de venda ---------------------------------------
        pygame.draw.rect(tela, (200, 165, 0), CAIXA_VENDA, border_radius=6)
        pygame.draw.rect(tela, (255, 215, 50), CAIXA_VENDA, 2, border_radius=6)
        rv = fonte_p.render('VENDA', True, (25, 16, 0))
        tela.blit(rv, (CAIXA_VENDA.centerx - rv.get_width()//2,
                        CAIXA_VENDA.centery - rv.get_height()//2))

        # -- Jogador ----------------------------------------------
        self.jog.desenhar(tela)

        # -- Dicas contextuais ------------------------------------
        # Dica de pesca
        if self._no_ponto_de_pesca():
            tecla_p = self.cfg.teclas.get('pescar', pygame.K_f)
            if self.gd.tem_vara:
                tip = fonte_n.render(f'[{pygame.key.name(tecla_p).upper()}] Pescar ->', True, (150, 255, 200))
            else:
                tip = fonte_n.render('Compre uma Vara de Pesca no Pescador!', True, (255, 200, 80))
            tela.blit(tip, (largura // 2 - tip.get_width() // 2, altura - 58))

        # Dica de cama
        if self._perto_da_cama():
            tecla_i = self.cfg.teclas.get('interagir', pygame.K_e)
            tip_c   = fonte_p.render(f'[{pygame.key.name(tecla_i).upper()}] Dormir', True, (255, 230, 140))
            tela.blit(tip_c, (RET_CAMA.x - 8, RET_CAMA.y - 20))

        # Dica de prédios quebrados: lembrar de ir à cidade consertar
        estab_quebrado = self.gd.predios.get(ESTABULO_QUEBRADO) == ESTABULO_QUEBRADO
        gal_quebrado   = self.gd.predios.get(GALINHEIRO_QUEBRADO) == GALINHEIRO_QUEBRADO
        if estab_quebrado and RET_PX_ESTABULO.inflate(60, 60).colliderect(self.jog.obter_ret()):
            tip_q = fonte_p.render('-> Cidade: conserte o Estábulo com o Construtor!', True, (255, 195, 80))
            tela.blit(tip_q, (RET_PX_ESTABULO.centerx - tip_q.get_width() // 2,
                               RET_PX_ESTABULO.bottom + 6))
        elif gal_quebrado and RET_PX_GALINHEIRO.inflate(60, 60).colliderect(self.jog.obter_ret()):
            tip_q = fonte_p.render('-> Cidade: conserte o Galinheiro com o Construtor!', True, (255, 195, 80))
            tela.blit(tip_q, (RET_PX_GALINHEIRO.centerx - tip_q.get_width() // 2,
                               RET_PX_GALINHEIRO.bottom + 6))

        # Seta -> Cidade
        arr = fonte_p.render('-> Cidade', True, (255, 245, 200))
        pygame.draw.rect(tela, (25, 20, 10),
                         (largura - arr.get_width() - 16, altura//2 - 12,
                          arr.get_width() + 12, 22), border_radius=5)
        pygame.draw.rect(tela, (130, 105, 55),
                         (largura - arr.get_width() - 16, altura//2 - 12,
                          arr.get_width() + 12, 22), 2, border_radius=5)
        tela.blit(arr, (largura - arr.get_width() - 10, altura//2 - 8))

        # -- HUD --------------------------------------------------
        self.inv.desenhar_hud(tela, fonte_p, fonte_normal=fonte_n, dia=self.hor.dia)
        self._desenhar_relogio(tela, largura, fonte_n)

        # Dica de inventário
        tecla_inv = self.cfg.teclas.get('inventario', pygame.K_i)
        dica_inv  = fonte_p.render(f'[{pygame.key.name(tecla_inv).upper()}] Inventário', True, (140, 125, 95))
        tela.blit(dica_inv, (largura - dica_inv.get_width() - 8, altura - 22))

        # Mensagem de venda/debug
        if self._msg_venda and agora - self._timer_msg < 2500:
            ms = fonte_n.render(self._msg_venda, True, (100, 255, 150))
            tela.blit(ms, (largura // 2 - ms.get_width() // 2, 60))

        # Resultado de pesca
        if self.gd.ultimo_resultado:
            cor_res = (80, 255, 130) if self.gd.ultimo_resultado == 'capturado' else (255, 80, 80)
            txt_res = 'Peixe capturado!' if self.gd.ultimo_resultado == 'capturado' else 'Peixe escapou...'
            fs  = fonte_n.render(txt_res, True, cor_res)
            tela.blit(fs, (largura // 2 - fs.get_width() // 2, 80))
            if not hasattr(self, '_timer_resultado_pesca'):
                self._timer_resultado_pesca = agora
            elif agora - self._timer_resultado_pesca > 3000:
                self.gd.ultimo_resultado = None
                del self._timer_resultado_pesca

        # Mensagem de cansaço
        self._desenhar_msg_cansado(tela, largura, fonte_g)

        # Escuridão noturna
        escuridao = self.hor.nivel_escuridao()
        if escuridao > 0:
            ov = pygame.Surface((largura, altura), pygame.SRCALPHA)
            ov.fill((0, 0, 30, int(escuridao * 190)))
            tela.blit(ov, (0, 0))

        # Painel de inventário
        if self._ver_inv:
            self.inv.desenhar_painel(tela, FONTES, self.gd.tem_vara)

        # Diálogo
        if self.dialogo:
            self.dialogo.desenhar(tela, FONTES)

    # -- Helpers de HUD -------------------------------------------
    def _desenhar_relogio(self, tela, largura, fonte):
        hora_str, hora, _ = self.hor.hora_atual()
        noite = hora >= 20
        cor_t = (255, 200, 100) if noite else (255, 255, 220)
        tc    = fonte.render(hora_str, True, cor_t)
        larg  = tc.get_width() + 16
        bx    = largura - larg - 4
        pygame.draw.rect(tela, (12, 8, 28) if noite else (18, 18, 45),
                         (bx, 4, larg, 30), border_radius=8)
        pygame.draw.rect(tela, (110, 75, 200) if noite else (75, 75, 155),
                         (bx, 4, larg, 30), 2, border_radius=8)
        tela.blit(tc, (bx + 8, 9))

    def _desenhar_msg_cansado(self, tela, largura, fonte):
        if not self.gd.msg_cansado:
            return
        idade = pygame.time.get_ticks() - self.gd.timer_msg_cansado
        if idade > 5000:
            self.gd.msg_cansado = False
            return
        alfa     = max(0, 255 - int((idade - 3000) / 2000 * 255)) if idade > 3000 else 255
        caixa    = pygame.Surface((520, 68), pygame.SRCALPHA)
        caixa.fill((35, 18, 0, 220))
        pygame.draw.rect(caixa, (200, 145, 50), caixa.get_rect(), 2, border_radius=12)
        msg      = fonte.render('Você está ficando cansado...', True, (255, 200, 50))
        caixa.blit(msg, (260 - msg.get_width() // 2, 14))
        caixa.set_alpha(alfa)
        tela.blit(caixa, (largura // 2 - 260, tela.get_height() // 2 - 34))

    # ----------------------------------------------------------
    # Desenho dos prédios
    # ----------------------------------------------------------
    def _desenhar_casa(self, tela, fonte_p):
        r = RET_PX_CASA
        x, y, w, h = r.x, r.y, r.width, r.height

        # Sprite da casa escalado para a area do predio
        surf_casa = RECURSOS.obter_imagem('casa', (w, h))
        tela.blit(surf_casa, (x, y))

        # Label
        label = fonte_p.render('Casa', True, (255, 242, 208))
        bg    = pygame.Surface((label.get_width()+8, label.get_height()+4), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 155))
        tela.blit(bg,    (x + w//2 - label.get_width()//2 - 4, y - 22))
        tela.blit(label, (x + w//2 - label.get_width()//2,     y - 20))

    def _desenhar_estabulo(self, tela, fonte_p):
        r = RET_PX_ESTABULO
        x, y, w, h = r.x, r.y, r.width, r.height
        quebrado   = self.gd.predios.get(ESTABULO_QUEBRADO) == ESTABULO_QUEBRADO

        # Sprite do celeiro (barn) escalado para a area do predio
        surf_barn = RECURSOS.obter_imagem('estabulo', (w, h))
        if quebrado:
            surf_barn = surf_barn.copy()
            escurece = pygame.Surface((w, h), pygame.SRCALPHA)
            escurece.fill((60, 30, 10, 100))
            surf_barn.blit(escurece, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        tela.blit(surf_barn, (x, y))

        label  = 'Estábulo' + (' (quebrado)' if quebrado else '')
        cor_l  = (230, 140, 70) if quebrado else (255, 222, 172)
        rot    = fonte_p.render(label, True, cor_l)
        bg     = pygame.Surface((rot.get_width()+8, rot.get_height()+4), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 155))
        tela.blit(bg,  (x + w//2 - rot.get_width()//2 - 4, y - 22))
        tela.blit(rot, (x + w//2 - rot.get_width()//2,     y - 20))

    def _desenhar_galinheiro(self, tela, fonte_p):
        r = RET_PX_GALINHEIRO
        x, y, w, h = r.x, r.y, r.width, r.height
        quebrado   = self.gd.predios.get(GALINHEIRO_QUEBRADO) == GALINHEIRO_QUEBRADO

        # Usa o sprite de casa como galinheiro (escalonado para a area)
        surf_gal = RECURSOS.obter_imagem('casa', (w, h))
        if quebrado:
            surf_gal = surf_gal.copy()
            escurece = pygame.Surface((w, h), pygame.SRCALPHA)
            escurece.fill((60, 30, 10, 100))
            surf_gal.blit(escurece, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        tela.blit(surf_gal, (x, y))

        label  = 'Galinheiro' + (' (quebrado)' if quebrado else '')
        cor_l  = (230, 140, 70) if quebrado else (255, 232, 188)
        rot    = fonte_p.render(label, True, cor_l)
        bg     = pygame.Surface((rot.get_width()+8, rot.get_height()+4), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 155))
        tela.blit(bg,  (x + w//2 - rot.get_width()//2 - 4, y - 22))
        tela.blit(rot, (x + w//2 - rot.get_width()//2,     y - 20))

    def _desenhar_cerca_galinheiro(self, tela):
        r   = RET_PX_GALINHEIRO
        fx  = r.x - 8
        fy  = r.bottom + 2
        fw  = r.width + 16

        # Cerca: Fences_8-17.png repetida ao longo da faixa
        # Escala para 10x22 por estaca para cobrir os 30px de altura
        sw, sh = 10, 30
        surf_cerca = RECURSOS.obter_imagem('cerca', (sw, sh))
        for px5 in range(fx, fx + fw, sw):
            tela.blit(surf_cerca, (px5, fy - 2))

        # Portão central (2 estacas maiores com abertura)
        gx = fx + fw//2 - 14
        surf_portao = RECURSOS.obter_imagem('cerca', (sw+4, sh+4))
        tela.blit(surf_portao, (gx, fy - 4))
        tela.blit(surf_portao, (gx + 18, fy - 4))

    def _desenhar_interior_casa(self, tela):
        r = RET_PX_CASA
        # Piso de madeira aquecido
        piso = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
        piso.fill((192, 165, 120, 218))
        for fy in range(0, r.height, 12):
            pygame.draw.line(piso, (172, 145, 100), (0, fy), (r.width, fy), 1)
        tela.blit(piso, (r.x, r.y))

        # Parede interna superior
        pygame.draw.rect(tela, (170, 143, 98), (r.x, r.y, r.width, 18))

        # Cama
        bx, by = RET_CAMA.x, RET_CAMA.y
        bw, bh = RET_CAMA.width, RET_CAMA.height
        pygame.draw.rect(tela, (95, 62, 30),   RET_CAMA)
        pygame.draw.rect(tela, (228, 215, 195), (bx+3, by+3, bw-6, bh-6))
        pygame.draw.rect(tela, (185, 55, 55),   (bx+3, by+3, bw-6, 9))
        pygame.draw.rect(tela, (205, 170, 130), (bx+3, by+3, bw-6, bh-6), 1)

        # Mesinha de canto com vela
        tx, ty = r.x + 6, r.y + 22
        pygame.draw.rect(tela, (125, 86, 40),  (tx, ty, 22, 14))
        pygame.draw.rect(tela, (155, 115, 62), (tx+2, ty-3, 18, 5))
        pygame.draw.rect(tela, (238, 232, 212), (tx+8, ty-8, 5, 8))
        pygame.draw.circle(tela, (255, 200, 50), (tx+10, ty-10), 3)

    def _desenhar_interior_estabulo(self, tela):
        r = RET_PX_ESTABULO
        piso = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
        piso.fill((180, 148, 95, 218))
        for fy in range(0, r.height, 12):
            pygame.draw.line(piso, (160, 130, 80), (0, fy), (r.width, fy), 1)
        tela.blit(piso, (r.x, r.y))
        pygame.draw.rect(tela, (155, 125, 80), (r.x, r.y, r.width, 18))

    def _desenhar_interior_galinheiro(self, tela):
        r = RET_PX_GALINHEIRO
        piso = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
        piso.fill((210, 188, 130, 218))
        for fy in range(0, r.height, 12):
            pygame.draw.line(piso, (190, 168, 110), (0, fy), (r.width, fy), 1)
        tela.blit(piso, (r.x, r.y))
        pygame.draw.rect(tela, (190, 165, 105), (r.x, r.y, r.width, 18))

    def _desenhar_piso_interior(self, tela, ret, cor_piso):
        pass
