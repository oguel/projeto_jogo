"""
fazenda_estado.py / farm_state.py — Estado da Fazenda (jogador único).

Funcionalidades:
  • Casa com cama para dormir (E perto da cama = novo dia)
  • Estábulo  — prédio rústico escuro, animais visíveis apenas dentro
  • Galinheiro — madeira clara, cerca na frente, animais visíveis apenas dentro
  • Plantio, colheita, corte de árvores, pesca no pier
  • HUD: dinheiro, madeira, semente ativa, relógio
  • Inventário completo (tecla I)
  • Cheat de debug: F12 = +$200 e +50 madeiras
"""
import pygame
import math
import random

from src.states    import EstadoBase, FONTES
from src.constants import (
    TAM_TILE, COLUNAS, LINHAS,
    GRAMA, SOLO, SEMENTE, SEMENTE_ESP,
    MUDA, ARVORE, AGUA, PIER,
    ID_SEMENTE, ID_SEMENTE_ESP, ID_MUDA,
    ID_COLHEITA, ID_COLHEITA_ESP, ID_MADEIRA,
    PRECOS_VENDA,
    COLS_LAGO, LINHAS_LAGO, COLS_PIER, LINHAS_PIER, COL_PESCAR,
    RET_CASA, RET_ESTABULO, RET_GALINHEIRO,
    COR_GRAMA, COR_SOLO, COR_PLANTADO, COR_ESP, COR_MUDA, COR_ARVORE, COR_AGUA, COR_PIER,
    TEMPO_SEMENTE, TEMPO_ESPECIAL, TEMPO_MUDA,
    ESTABULO_QUEBRADO, ESTABULO_FIXO, GALINHEIRO_QUEBRADO, GALINHEIRO_FIXO,
    SPAWN_X, SPAWN_Y,
)
from src import assets as RECURSOS
from src.entities import Jogador, atualizar_animais, desenhar_animais

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Conjuntos de tiles especiais
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TILES_LAGO   = frozenset((c, r) for c in COLS_LAGO   for r in LINHAS_LAGO)
TILES_PIER   = frozenset((c, r) for c in COLS_PIER   for r in LINHAS_PIER
                          if c != COL_PESCAR)
TILES_PESCA  = frozenset((COL_PESCAR, r) for r in LINHAS_PIER)
TILES_AGUA   = TILES_LAGO | TILES_PIER | TILES_PESCA


def _tiles_predio(col, lin, larg, alt):
    return frozenset((col + x, lin + y) for x in range(larg) for y in range(alt))


TILES_CASA       = _tiles_predio(*RET_CASA)
TILES_ESTABULO   = _tiles_predio(*RET_ESTABULO)
TILES_GALINHEIRO = _tiles_predio(*RET_GALINHEIRO)
TILES_BLOQUEADOS = TILES_CASA | TILES_ESTABULO | TILES_GALINHEIRO


def _tiles_para_pixels(col, lin, larg, alt):
    return pygame.Rect(col * TAM_TILE, lin * TAM_TILE, larg * TAM_TILE, alt * TAM_TILE)


RET_PX_CASA       = _tiles_para_pixels(*RET_CASA)         # Rect em pixels da casa
RET_PX_ESTABULO   = _tiles_para_pixels(*RET_ESTABULO)     # Rect em pixels do estábulo
RET_PX_GALINHEIRO = _tiles_para_pixels(*RET_GALINHEIRO)   # Rect em pixels do galinheiro

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
        pygame.Rect(x,     y,     w,             4),    # norte
        pygame.Rect(x,     y,     4,             h),    # oeste
        pygame.Rect(x+w-4, y,     4,             h),    # leste
        pygame.Rect(x,     y+h-4, esq_porta - x, 4),   # sul-esquerda
        pygame.Rect(dir_porta, y+h-4, x+w-dir_porta, 4), # sul-direita
    ]


PAREDES_CASA       = _criar_paredes(RET_PX_CASA,       40)
PAREDES_ESTABULO   = _criar_paredes(RET_PX_ESTABULO,   56)
PAREDES_GALINHEIRO = _criar_paredes(RET_PX_GALINHEIRO, 36)


def _inicializar_mapa():
    """Cria o mapa inicial da fazenda com grama e água nos tiles certos."""
    grade = [[GRAMA] * COLUNAS for _ in range(LINHAS)]
    for (c, r) in TILES_AGUA:
        if 0 <= r < LINHAS and 0 <= c < COLUNAS:
            grade[r][c] = AGUA
    return grade


def _gerar_rachaduras(ret: pygame.Rect, qtd: int):
    """Gera rachaduras aleatórias (mas fixas) para prédios quebrados."""
    rachaduras = []
    random.seed(ret.x + ret.y)
    for _ in range(qtd):
        x1 = random.randint(ret.x + 6, ret.right - 6)
        dx = random.randint(-12, 12)
        dy = ret.height // 3
        rachaduras.append((x1, ret.y + dy, x1 + dx, ret.y + dy * 2))
    random.seed()
    return rachaduras


RACHADURAS_ESTABULO   = _gerar_rachaduras(RET_PX_ESTABULO,   4)
RACHADURAS_GALINHEIRO = _gerar_rachaduras(RET_PX_GALINHEIRO, 3)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EstadoFazenda
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Processar eventos
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def processar_eventos(self, eventos: list):
        # Repassa eventos para o diálogo se estiver aberto
        if self.dialogo:
            if not self.dialogo.processar_eventos(eventos, self.cfg.teclas):
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
                self._msg_venda = '💜 Debug: +$200 e +50 madeiras!'
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

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Ações do jogador
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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
        from src.states import EstadoDesmaio
        return EstadoDesmaio(self.gd)

    def _tentar_arar(self, col, lin):
        if not self._tile_valido(col, lin): return
        if self.mapa[lin][col] == GRAMA:
            self.mapa[lin][col] = SOLO
            RECURSOS.tocar_som('plantar', 'plantas', self.cfg.volumes)

    def _tentar_vender(self):
        if CAIXA_VENDA.colliderect(self.jog.obter_ret()):
            ganhou = self.inv.vender_tudo()
            if ganhou:
                self._msg_venda = f'Vendido: ${ganhou}!'
                self._timer_msg = pygame.time.get_ticks()
                RECURSOS.tocar_som('vender', 'interface', self.cfg.volumes)

    def _tentar_plantar(self, col, lin):
        if not self._tile_valido(col, lin): return
        if self.mapa[lin][col] != SOLO: return
        ativa = self.inv.semente_ativa
        agora = pygame.time.get_ticks()
        if ativa == ID_SEMENTE and self.inv.semente > 0:
            self.inv.semente        -= 1
            self.mapa[lin][col]      = SEMENTE
            self.tp[(col, lin)]     = agora
            RECURSOS.tocar_som('plantar', 'plantas', self.cfg.volumes)
        elif ativa == ID_SEMENTE_ESP and self.inv.semente_esp > 0:
            self.inv.semente_esp    -= 1
            self.mapa[lin][col]      = SEMENTE_ESP
            self.tp[(col, lin)]     = agora
            RECURSOS.tocar_som('plantar', 'plantas', self.cfg.volumes)
        elif ativa == ID_MUDA and self.inv.muda > 0:
            self.inv.muda           -= 1
            self.mapa[lin][col]      = MUDA
            self.tp[(col, lin)]     = agora
            RECURSOS.tocar_som('plantar', 'plantas', self.cfg.volumes)

    def _tentar_colher(self, col, lin):
        if not self._tile_valido(col, lin): return
        tile  = self.mapa[lin][col]
        idade = pygame.time.get_ticks() - self.tp.get((col, lin), pygame.time.get_ticks())
        if tile == SEMENTE and idade >= TEMPO_SEMENTE:
            self.mapa[lin][col]   = SOLO
            self.inv.colheita    += 1
            del self.tp[(col, lin)]
            RECURSOS.tocar_som('colher', 'plantas', self.cfg.volumes)
        elif tile == SEMENTE_ESP and idade >= TEMPO_ESPECIAL:
            self.mapa[lin][col]   = SOLO
            self.inv.colheita_esp += 1
            del self.tp[(col, lin)]
            RECURSOS.tocar_som('colher', 'plantas', self.cfg.volumes)

    def _tentar_cortar(self, col, lin):
        if not self._tile_valido(col, lin): return
        tile  = self.mapa[lin][col]
        idade = pygame.time.get_ticks() - self.tp.get((col, lin), pygame.time.get_ticks())
        if tile == MUDA and idade >= TEMPO_MUDA:
            self.mapa[lin][col] = GRAMA
            self.inv.madeira   += random.randint(2, 4)
            self.tp.pop((col, lin), None)
            RECURSOS.tocar_som('cortar', 'plantas', self.cfg.volumes)
        elif tile == ARVORE:
            self.mapa[lin][col] = GRAMA
            self.inv.madeira   += random.randint(3, 6)
            self.tp.pop((col, lin), None)
            RECURSOS.tocar_som('cortar', 'plantas', self.cfg.volumes)

    def _no_ponto_de_pesca(self) -> bool:
        col, lin = self.jog.posicao_tile()
        return (col, lin) in TILES_PESCA and self.jog.direcao == 'direita'

    def _tile_valido(self, col, lin) -> bool:
        if not (0 <= col < COLUNAS and 0 <= lin < LINHAS): return False
        if (col, lin) in TILES_BLOQUEADOS:                  return False
        if (col, lin) in TILES_AGUA:                        return False
        return True

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Atualização por frame
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def atualizar(self):
        teclas_press = pygame.key.get_pressed()
        colisoes     = self._colisoes()
        self.jog.mover(teclas_press, self.cfg.teclas, colisoes)

        # Limita o jogador ao mapa
        self.jog.x = max(0.0, min(self.jog.x, (COLUNAS - 1) * TAM_TILE - 4))
        self.jog.y = max(0.0, min(self.jog.y, (LINHAS  - 1) * TAM_TILE - 4))

        # Jogador chegou à borda direita → vai para a cidade
        if self.jog.x > (COLUNAS - 1) * TAM_TILE - 8:
            self.jog.x = 300.0
            self.jog.y = 300.0
            from src.town_state import EstadoCidade
            return EstadoCidade(self.gd)

        # Muda crescida em árvore
        agora = pygame.time.get_ticks()
        for (c, l), t in list(self.tp.items()):
            if self.mapa[l][c] == MUDA and agora - t >= TEMPO_MUDA:
                self.mapa[l][c] = ARVORE

        # Atualiza animais
        atualizar_animais(self.gd.animais)
        self._tick_agua += 1

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

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Desenho
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def desenhar(self, tela: pygame.Surface):
        largura, altura = tela.get_size()
        fonte_p = FONTES.get('pequena', pygame.font.SysFont('arial', 14))
        fonte_n = FONTES.get('normal',  pygame.font.SysFont('arial', 18))
        fonte_g = FONTES.get('grande',  pygame.font.SysFont('arial', 28, bold=True))
        agora   = pygame.time.get_ticks()

        # ── Tiles do mapa ────────────────────────────────────────
        for lin in range(LINHAS):
            for col in range(COLUNAS):
                rx, ry = col * TAM_TILE, lin * TAM_TILE
                pos    = (col, lin)
                tile   = self.mapa[lin][col]

                if pos in TILES_PESCA or pos in TILES_PIER:
                    # Deck de madeira
                    pygame.draw.rect(tela, COR_PIER, (rx, ry, TAM_TILE, TAM_TILE))
                    for bx in range(rx + 4, rx + TAM_TILE, 8):
                        pygame.draw.line(tela, (100, 65, 28), (bx, ry), (bx, ry + TAM_TILE), 2)
                    if pos in TILES_PESCA:
                        pygame.draw.circle(tela, (80, 200, 255),
                                           (rx + TAM_TILE // 2, ry + TAM_TILE // 2), 6)
                elif pos in TILES_LAGO:
                    # Água animada
                    onda  = math.sin(self._tick_agua * 0.05 + col * 0.5 + lin * 0.3)
                    nv    = int(onda * 10)
                    cor   = (max(0, 30+nv), max(0, 90+nv), min(255, 200+nv//2))
                    pygame.draw.rect(tela, cor, (rx, ry, TAM_TILE, TAM_TILE))
                    if (col + lin + self._tick_agua // 20) % 3 == 0:
                        pygame.draw.line(tela, (160, 220, 255),
                                         (rx+4, ry+TAM_TILE//2), (rx+TAM_TILE-4, ry+TAM_TILE//2), 1)
                else:
                    # Tile de terreno
                    mapa_cor = {
                        GRAMA:      COR_GRAMA,
                        SOLO:       COR_SOLO,
                        SEMENTE:    COR_PLANTADO,
                        SEMENTE_ESP: COR_ESP,
                        MUDA:       COR_MUDA,
                        ARVORE:     COR_ARVORE,
                    }
                    pygame.draw.rect(tela, mapa_cor.get(tile, COR_GRAMA),
                                     (rx, ry, TAM_TILE, TAM_TILE))
                    # Detalhes visuais
                    if tile == GRAMA and (col + lin) % 6 == 0:
                        pygame.draw.line(tela, (45, 165, 45),
                                         (rx+10, ry+TAM_TILE-4), (rx+14, ry+TAM_TILE-14), 1)
                    if tile == ARVORE:
                        pygame.draw.circle(tela, (20, 105, 20),
                                           (rx + TAM_TILE//2, ry + 8), 15)
                    if tile in (SEMENTE, SEMENTE_ESP, MUDA):
                        tempo_max = {SEMENTE: TEMPO_SEMENTE, SEMENTE_ESP: TEMPO_ESPECIAL,
                                     MUDA: TEMPO_MUDA}[tile]
                        pct = min(1.0, (agora - self.tp.get(pos, agora)) / tempo_max)
                        pygame.draw.rect(tela, (40, 200, 40),
                                         (rx, ry + TAM_TILE - 5, int(TAM_TILE * pct), 4))

                pygame.draw.rect(tela, (0, 0, 0, 18), (rx, ry, TAM_TILE, TAM_TILE), 1)

        # ── Prédios ──────────────────────────────────────────────
        self._desenhar_casa(tela, fonte_p)
        self._desenhar_estabulo(tela, fonte_p)
        self._desenhar_galinheiro(tela, fonte_p)
        self._desenhar_cerca_galinheiro(tela)

        # ── Interiores (só visíveis ao entrar) ───────────────────
        if self._dentro_casa:
            self._desenhar_interior_casa(tela)
        if self._dentro_estabulo:
            self._desenhar_piso_interior(tela, RET_PX_ESTABULO, (155, 125, 82))
            vacas = [a for a in self.gd.animais if a['tipo'] == 'vaca']
            desenhar_animais(tela, vacas)
        if self._dentro_galinheiro:
            self._desenhar_piso_interior(tela, RET_PX_GALINHEIRO, (195, 172, 118))
            galinhas = [a for a in self.gd.animais if a['tipo'] == 'galinha']
            desenhar_animais(tela, galinhas)

        # ── Caixa de venda ───────────────────────────────────────
        pygame.draw.rect(tela, (200, 165, 0), CAIXA_VENDA, border_radius=6)
        pygame.draw.rect(tela, (255, 215, 50), CAIXA_VENDA, 2, border_radius=6)
        rv = fonte_p.render('VENDA', True, (25, 16, 0))
        tela.blit(rv, (CAIXA_VENDA.centerx - rv.get_width()//2,
                        CAIXA_VENDA.centery - rv.get_height()//2))

        # ── Jogador ──────────────────────────────────────────────
        self.jog.desenhar(tela)

        # ── Dicas contextuais ────────────────────────────────────
        # Dica de pesca
        if self._no_ponto_de_pesca():
            tecla_p = self.cfg.teclas.get('pescar', pygame.K_f)
            if self.gd.tem_vara:
                tip = fonte_n.render(f'[{pygame.key.name(tecla_p).upper()}] Pescar →', True, (150, 255, 200))
            else:
                tip = fonte_n.render('Compre uma Vara de Pesca no Pescador!', True, (255, 200, 80))
            tela.blit(tip, (largura // 2 - tip.get_width() // 2, altura - 58))

        # Dica de cama
        if self._perto_da_cama():
            tecla_i = self.cfg.teclas.get('interagir', pygame.K_e)
            tip_c   = fonte_p.render(f'[{pygame.key.name(tecla_i).upper()}] Dormir 🛏️', True, (255, 230, 140))
            tela.blit(tip_c, (RET_CAMA.x - 8, RET_CAMA.y - 20))

        # Dica de prédios quebrados: lembrar de ir à cidade consertar
        estab_quebrado = self.gd.predios.get(ESTABULO_QUEBRADO) == ESTABULO_QUEBRADO
        gal_quebrado   = self.gd.predios.get(GALINHEIRO_QUEBRADO) == GALINHEIRO_QUEBRADO
        if estab_quebrado and RET_PX_ESTABULO.inflate(60, 60).colliderect(self.jog.obter_ret()):
            tip_q = fonte_p.render('→ Cidade: conserte o Estábulo com o Construtor!', True, (255, 195, 80))
            tela.blit(tip_q, (RET_PX_ESTABULO.centerx - tip_q.get_width() // 2,
                               RET_PX_ESTABULO.bottom + 6))
        elif gal_quebrado and RET_PX_GALINHEIRO.inflate(60, 60).colliderect(self.jog.obter_ret()):
            tip_q = fonte_p.render('→ Cidade: conserte o Galinheiro com o Construtor!', True, (255, 195, 80))
            tela.blit(tip_q, (RET_PX_GALINHEIRO.centerx - tip_q.get_width() // 2,
                               RET_PX_GALINHEIRO.bottom + 6))

        # Seta → Cidade
        arr = fonte_p.render('→ Cidade', True, (255, 245, 200))
        pygame.draw.rect(tela, (25, 20, 10),
                         (largura - arr.get_width() - 16, altura//2 - 12,
                          arr.get_width() + 12, 22), border_radius=5)
        pygame.draw.rect(tela, (130, 105, 55),
                         (largura - arr.get_width() - 16, altura//2 - 12,
                          arr.get_width() + 12, 22), 2, border_radius=5)
        tela.blit(arr, (largura - arr.get_width() - 10, altura//2 - 8))

        # ── HUD ──────────────────────────────────────────────────
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
            txt_res = '🐟 Peixe capturado!' if self.gd.ultimo_resultado == 'capturado' else '💨 Peixe escapou...'
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

    # ── Helpers de HUD ───────────────────────────────────────────
    def _desenhar_relogio(self, tela, largura, fonte):
        hora_str, hora, _ = self.hor.hora_atual()
        noite = hora >= 20
        cor_t = (255, 200, 100) if noite else (255, 255, 220)
        tc    = fonte.render(f'🕐 {hora_str}', True, cor_t)
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

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Desenho dos prédios
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _desenhar_casa(self, tela, fonte_p):
        r = RET_PX_CASA
        x, y, w, h = r.x, r.y, r.width, r.height
        parede_y   = y + h // 3

        # Sombra
        ss = pygame.Surface((w+8, h+8), pygame.SRCALPHA)
        ss.fill((0, 0, 0, 80))
        tela.blit(ss, (x+5, y+5))

        # Paredes (tábuas horizontais)
        cor_parede = (188, 162, 115)
        cor_tabua  = (168, 142, 95)
        pygame.draw.rect(tela, cor_parede, (x, parede_y, w, h - h//3))
        for py in range(parede_y + 8, y + h, 10):
            pygame.draw.line(tela, cor_tabua, (x, py), (x+w, py), 1)

        # Telhado de palha
        cor_telha = (132, 74, 24)
        pts_telho = [(x-6, parede_y+2), (x+w//2, y+2), (x+w+6, parede_y+2)]
        pygame.draw.polygon(tela, cor_telha, pts_telho)
        pygame.draw.polygon(tela, (105, 58, 18), pts_telho, 3)
        for i in range(5, 35, 7):
            fr  = i / 35
            ly  = int(y + 4 + (parede_y - y - 4) * fr)
            lx1 = int((x-6) + i * (w//2+6) / 35)
            lx2 = int((x+w+6) - i * (w//2+6) / 35)
            pygame.draw.line(tela, (110, 62, 16), (lx1, ly), (lx2, ly), 2)

        # Chaminé
        cx2 = x + w - 38
        pygame.draw.rect(tela, (118, 72, 42), (cx2, y-20, 16, 27))
        pygame.draw.rect(tela, (92, 55, 32),  (cx2-2, y-22, 20, 6))

        # Porta arqueada
        pw, ph = 28, 40
        px2    = x + w//2 - pw//2
        pyd    = y + h - ph
        pygame.draw.rect(tela, (78, 48, 20), (px2, pyd+8, pw, ph-8))
        pygame.draw.ellipse(tela, (78, 48, 20), (px2, pyd, pw, 16))
        pygame.draw.rect(tela, (55, 32, 10), (px2, pyd+8, pw, ph-8), 2)
        pygame.draw.ellipse(tela, (55, 32, 10), (px2, pyd, pw, 16), 2)
        pygame.draw.circle(tela, (198, 172, 48), (px2+pw-6, pyd+ph-16), 3)

        # Janelas
        for wx in [x+12, x+w-32]:
            wy = parede_y + 14
            pygame.draw.rect(tela, (192, 222, 255), (wx, wy, 20, 18))
            pygame.draw.line(tela, (122, 158, 198), (wx+10, wy), (wx+10, wy+18), 1)
            pygame.draw.line(tela, (122, 158, 198), (wx, wy+9), (wx+20, wy+9), 1)
            pygame.draw.rect(tela, (108, 75, 40), (wx-7, wy-1, 6, 20))
            pygame.draw.rect(tela, (108, 75, 40), (wx+21, wy-1, 6, 20))

        # Caixinha de flores
        fb_y = parede_y + 34
        pygame.draw.rect(tela, (98, 64, 32), (x+9, fb_y, 28, 7))
        for fi, fc in enumerate([(218,62,62),(198,82,28),(182,58,138)]):
            fx2 = x + 16 + fi * 8
            pygame.draw.circle(tela, fc,       (fx2, fb_y-3), 4)
            pygame.draw.line(tela,  (55,128,40),(fx2, fb_y),  (fx2, fb_y+4), 1)

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
        parede_y   = y + h // 4

        cw  = (112, 68, 32)  if quebrado else (138, 88, 44)
        ct  = (78, 48, 22)   if quebrado else (92, 56, 25)
        ctb = (95, 56, 22)   if quebrado else (118, 74, 36)

        # Sombra
        ss = pygame.Surface((w+8, h+8), pygame.SRCALPHA)
        ss.fill((0, 0, 0, 95))
        tela.blit(ss, (x+6, y+6))

        # Paredes (tábuas verticais — estilo celeiro)
        pygame.draw.rect(tela, cw, (x, parede_y, w, h - h//4))
        for px3 in range(x, x+w+1, 16):
            pygame.draw.line(tela, ctb, (px3, parede_y), (px3, y+h), 1)
        for py3 in range(parede_y+10, y+h, 22):
            cor3 = (max(0, cw[0]-12), max(0, cw[1]-8), max(0, cw[2]-4))
            pygame.draw.line(tela, cor3, (x, py3), (x+w, py3), 1)

        # Cruzes diagonais estilo celeiro
        brace  = (max(0, cw[0]-18), max(0, cw[1]-12), max(0, cw[2]-8))
        mid_x  = x + w // 2
        pygame.draw.line(tela, brace, (x+4, parede_y+4), (mid_x-4, y+h-30), 2)
        pygame.draw.line(tela, brace, (mid_x-4, parede_y+4), (x+4, y+h-30), 2)
        pygame.draw.line(tela, brace, (mid_x+4, parede_y+4), (x+w-4, y+h-30), 2)
        pygame.draw.line(tela, brace, (x+w-4, parede_y+4), (mid_x+4, y+h-30), 2)

        # Telhado duas águas
        pts_t = [(x-5, parede_y+2), (x+w//2, y+3), (x+w+5, parede_y+2)]
        pygame.draw.polygon(tela, ct, pts_t)
        ctd = (max(0,ct[0]-18), max(0,ct[1]-12), max(0,ct[2]-8))
        for i in range(5, 32, 6):
            fr   = i / 32
            ry2  = int(y + 4 + (parede_y - y - 4) * fr)
            rx1  = int((x-5) + i*(w//2+5)/32)
            rx2  = int((x+w+5) - i*(w//2+5)/32)
            pygame.draw.line(tela, ctd, (rx1, ry2), (rx2, ry2), 2)

        # Porta dupla
        dw2  = 56
        dx2  = x + w//2 - dw2//2
        dyd2 = y + h - 54
        for px4, pw4 in [(dx2, dw2//2-1), (dx2+dw2//2+1, dw2//2-1)]:
            pygame.draw.rect(tela, (68, 40, 16), (px4, dyd2, pw4, 54))
            pygame.draw.rect(tela, (48, 28, 8),  (px4, dyd2, pw4, 54), 2)
            pygame.draw.line(tela, (48, 28, 8), (px4+2, dyd2+2), (px4+pw4-2, dyd2+50), 1)
            pygame.draw.line(tela, (48, 28, 8), (px4+pw4-2, dyd2+2), (px4+2, dyd2+50), 1)
        pygame.draw.rect(tela, (210, 182, 66), (dx2+4, dyd2+36, dw2-8, 16))

        # Janelas altas
        for wx2 in [x+8, x+w-28]:
            wy2 = parede_y + 14
            pygame.draw.rect(tela, (180, 212, 242), (wx2, wy2, 20, 15))
            pygame.draw.line(tela, (120, 152, 182), (wx2+10, wy2), (wx2+10, wy2+15), 1)

        # Lanterna acima da porta
        lx3 = x + w//2
        ly2 = parede_y + 6
        pygame.draw.line(tela, (80, 55, 25), (lx3, ly2), (lx3, ly2+12), 2)
        pygame.draw.rect(tela, (78, 78, 48), (lx3-5, ly2+12, 10, 12))
        pygame.draw.rect(tela, (255, 222, 100), (lx3-3, ly2+14, 6, 8))

        # Rachaduras se quebrado
        if quebrado:
            for x1, y1, x2, y2 in RACHADURAS_ESTABULO:
                pygame.draw.line(tela, (44, 28, 14), (x1, y1), (x2, y2), 2)

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
        parede_y   = y + h // 3

        cw  = (168, 140, 92) if not quebrado else (140, 115, 70)
        ct  = (145, 98, 44)  if not quebrado else (115, 72, 30)
        ctb = (148, 122, 78) if not quebrado else (122, 98, 58)

        # Sombra
        ss = pygame.Surface((w+6, h+6), pygame.SRCALPHA)
        ss.fill((0, 0, 0, 65))
        tela.blit(ss, (x+4, y+4))

        # Paredes (madeira mais clara)
        pygame.draw.rect(tela, cw, (x, parede_y, w, h - h//3))
        for py4 in range(parede_y+6, y+h, 8):
            pygame.draw.line(tela, ctb, (x, py4), (x+w, py4), 1)

        # Telhado pontiagudo
        pts_t2 = [(x-4, parede_y+2), (x+w//2, y+2), (x+w+4, parede_y+2)]
        pygame.draw.polygon(tela, ct, pts_t2)
        ctd2 = (max(0,ct[0]-22), max(0,ct[1]-18), max(0,ct[2]-10))
        for i in range(4, 24, 5):
            fr   = i / 24
            ry3  = int(y + 3 + (parede_y - y - 3) * fr)
            rx3  = int((x-4) + i*(w//2+4)/24)
            rx4  = int((x+w+4) - i*(w//2+4)/24)
            pygame.draw.line(tela, ctd2, (rx3, ry3), (rx4, ry3), 1)

        # Tela de arame
        for mx2 in range(x+4, x+w-4, 6):
            pygame.draw.line(tela, (155, 132, 88), (mx2, parede_y+4), (mx2, y+h-4), 1)

        # Porta pequena
        sdw, sdh = 18, 22
        sdx  = x + w//2 - sdw//2
        sdy  = y + h - sdh
        pygame.draw.rect(tela, (102, 72, 36), (sdx, sdy, sdw, sdh))
        pygame.draw.rect(tela, (78, 52, 22),  (sdx, sdy, sdw, sdh), 1)

        # Janela lateral
        wy3 = parede_y + 14
        pygame.draw.rect(tela, (182, 218, 252), (x+w-28, wy3, 18, 14))
        pygame.draw.line(tela, (122, 158, 192), (x+w-19, wy3), (x+w-19, wy3+14), 1)

        # Rachaduras se quebrado
        if quebrado:
            for x1b, y1b, x2b, y2b in RACHADURAS_GALINHEIRO:
                pygame.draw.line(tela, (40, 28, 14), (x1b, y1b), (x2b, y2b), 2)

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
        crc = (132, 92, 45)
        crl = (148, 108, 55)

        pygame.draw.line(tela, crl, (fx, fy+6),  (fx+fw, fy+6),  4)
        pygame.draw.line(tela, crl, (fx, fy+18), (fx+fw, fy+18), 4)
        for px5 in range(fx, fx+fw+1, 14):
            pygame.draw.rect(tela, crc, (px5-3, fy-2, 6, 30))

        # Portão central
        gx = fx + fw//2 - 14
        pygame.draw.rect(tela, (162, 122, 62), (gx, fy-2, 28, 30))
        pygame.draw.line(tela, (135, 95, 42), (gx, fy-2), (gx+28, fy+28), 2)
        pygame.draw.circle(tela, (76, 56, 26), (gx, fy+8),  3)
        pygame.draw.circle(tela, (76, 56, 26), (gx, fy+20), 3)

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

    def _desenhar_piso_interior(self, tela, ret, cor_piso):
        """Piso simples para estábulo/galinheiro."""
        piso = pygame.Surface((ret.width, ret.height), pygame.SRCALPHA)
        piso.fill((*cor_piso, 198))
        for fy in range(0, ret.height, 10):
            cor_linha = (max(0, cor_piso[0]-18), max(0, cor_piso[1]-15), max(0, cor_piso[2]-10))
            pygame.draw.line(piso, cor_linha, (0, fy), (ret.width, fy), 1)
        tela.blit(piso, (ret.x, ret.y))
        cor_topo = (max(0, cor_piso[0]-25), max(0, cor_piso[1]-20), max(0, cor_piso[2]-15))
        pygame.draw.rect(tela, cor_topo, (ret.x, ret.y, ret.width, 14))
