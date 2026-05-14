import pygame

from src.states    import EstadoBase, FONTES
from src.constants import TAM_TILE, COLUNAS
from src.entities  import NPCFazendeiro, NPCPescador, NPCVendedorAnimais, NPCConstrutor
from src import assets as RECURSOS

# Geometria dos 4 predios em pixels
_NW = pygame.Rect(  0,   0, 165, 210)
_NE = pygame.Rect(635,   0, 165, 210)
_SW = pygame.Rect(  0, 390, 165, 210)
_SE = pygame.Rect(635, 390, 165, 210)

# Aberturas das portas (areas SEM cerca, para o jogador entrar/sair)
# NW e NE tem porta na borda sul; SW e SE tem porta na borda norte
_PORTA_W  = 60   # largura da abertura da porta em px

# Colisoes estaticas da cidade
def _gerar_colisoes():
    rects = []

    # Os 4 predios solidos
    for r in (_NW, _NE, _SW, _SE):
        rects.append(r)

    # Cercas nas bordas laterais (nao bloqueiam as portas)
    FW, FH = 12, 21
    cx_porta = 165 // 2  # centro x da porta dos predios NW/SW

    # NW: borda leste (x=165) sem abertura, borda sul com gap central
    rects.append(pygame.Rect(165, 0, FW, _NW.height))   # lateral leste
    # borda sul com gap para a porta
    porta_x_nw = _NW.x + _NW.width // 2 - _PORTA_W // 2
    if porta_x_nw > 0:
        rects.append(pygame.Rect(0, 210 - FH, porta_x_nw, FH))
    fim_porta_nw = porta_x_nw + _PORTA_W
    if fim_porta_nw < _NW.width:
        rects.append(pygame.Rect(fim_porta_nw, 210 - FH, _NW.width - fim_porta_nw, FH))

    # NE: borda oeste (x=625), borda sul com gap central
    rects.append(pygame.Rect(625, 0, FW, _NE.height))
    porta_x_ne = _NE.x + _NE.width // 2 - _PORTA_W // 2
    if porta_x_ne > _NE.x:
        rects.append(pygame.Rect(_NE.x, 210 - FH, porta_x_ne - _NE.x, FH))
    fim_porta_ne = porta_x_ne + _PORTA_W
    if fim_porta_ne < _NE.right:
        rects.append(pygame.Rect(fim_porta_ne, 210 - FH, _NE.right - fim_porta_ne, FH))

    # SW: borda leste (x=165), borda norte com gap central
    rects.append(pygame.Rect(165, 390, FW, _SW.height))
    porta_x_sw = _SW.x + _SW.width // 2 - _PORTA_W // 2
    if porta_x_sw > 0:
        rects.append(pygame.Rect(0, 390, porta_x_sw, FH))
    fim_porta_sw = porta_x_sw + _PORTA_W
    if fim_porta_sw < _SW.width:
        rects.append(pygame.Rect(fim_porta_sw, 390, _SW.width - fim_porta_sw, FH))

    # SE: borda oeste (x=625), borda norte com gap central
    rects.append(pygame.Rect(625, 390, FW, _SE.height))
    porta_x_se = _SE.x + _SE.width // 2 - _PORTA_W // 2
    if porta_x_se > _SE.x:
        rects.append(pygame.Rect(_SE.x, 390, porta_x_se - _SE.x, FH))
    fim_porta_se = porta_x_se + _PORTA_W
    if fim_porta_se < _SE.right:
        rects.append(pygame.Rect(fim_porta_se, 390, _SE.right - fim_porta_se, FH))

    # Arvores (tronco solido 24x24)
    rects.append(pygame.Rect(252 - 12, 450 - 12, 24, 24))
    rects.append(pygame.Rect(548 - 12, 450 - 12, 24, 24))

    # Postes (8x40)
    rects.append(pygame.Rect(315 - 4, 246, 8, 40))
    rects.append(pygame.Rect(485 - 4, 246, 8, 40))

    return rects

COLISOES_CIDADE = _gerar_colisoes()


class EstadoCidade(EstadoBase):

    def __init__(self, dados_jogo):
        self.gd  = dados_jogo
        self.cfg = dados_jogo.configuracao
        self.inv = dados_jogo.inventario
        self.hor = dados_jogo.horario
        self.jog = dados_jogo.jogador

        self.npcs = [
            NPCFazendeiro(       82,  80),
            NPCPescador(        718,  80),
            NPCVendedorAnimais( 718, 490),
            NPCConstrutor(       82, 490),
        ]

        self._nomes   = ['Loja do Fazendeiro', 'Loja do Pescador',
                         'Loja do Construtor',  'Loja do Vendedor de Animais']
        self._npc_idx = [0, 1, 3, 2]

        self.dialogo       = None
        self.carregamento  = None
        self.ver_inv       = False
        self.cooldown_loja = 0
        self.loja_proxima  = None

        dados_jogo.ultimo_mapa = 'cidade'

    def _loja_na_frente(self):
        cx   = self.jog.x + 16
        topo = self.jog.y
        base = self.jog.y + 48
        if 207 <= topo <= 222:
            if   0 <= cx <= 165: return 0
            if 635 <= cx <= 800: return 1
        if 383 <= base <= 400:
            if   0 <= cx <= 165: return 2
            if 635 <= cx <= 800: return 3
        return None

    def _abrir_loja(self, indice: int):
        npc = self.npcs[self._npc_idx[indice]]
        self.carregamento = {
            'npc': npc, 'nome': self._nomes[indice],
            'fase': 'entrar', 'alfa': 0,
            'inicio': pygame.time.get_ticks(),
        }

    def processar_eventos(self, eventos: list):
        if self.dialogo:
            if not self.dialogo.processar_eventos(eventos, self.cfg.teclas):
                self.dialogo = None
                self.carregamento['fase']   = 'sair'
                self.carregamento['alfa']   = 255
                self.carregamento['inicio'] = pygame.time.get_ticks()
            return self

        for ev in eventos:
            if ev.type != pygame.KEYDOWN:
                continue
            k = ev.key
            t = self.cfg.teclas
            if k == pygame.K_ESCAPE:
                if self.ver_inv:
                    self.ver_inv = False
                    continue
                from src.settings_state import EstadoConfiguracoes
                return EstadoConfiguracoes(self.gd, estado_anterior=self)
            if k == t.get('inventario', pygame.K_i):
                self.ver_inv = not self.ver_inv
            elif k in (pygame.K_RETURN, pygame.K_KP_ENTER):
                agora = pygame.time.get_ticks()
                if self.loja_proxima is not None and agora > self.cooldown_loja:
                    self._abrir_loja(self.loja_proxima)
        return self

    def atualizar(self):
        if not self.dialogo and not self.carregamento:
            self.jog.mover(pygame.key.get_pressed(), self.cfg.teclas, COLISOES_CIDADE)

        self.jog.x = max(0.0, min(self.jog.x, 790.0))
        self.jog.y = max(0.0, min(self.jog.y, 555.0))

        if self.jog.x < 5:
            self.jog.x = float((COLUNAS - 2) * TAM_TILE)
            self.jog.y = 300.0
            from src.farm_state import EstadoFazenda
            return EstadoFazenda(self.gd)

        self.loja_proxima = self._loja_na_frente()

        if self.carregamento:
            agora   = pygame.time.get_ticks()
            passado = agora - self.carregamento['inicio']
            fase    = self.carregamento['fase']
            if fase == 'entrar':
                self.carregamento['alfa'] = min(255, int(passado / 400 * 255))
                if passado >= 400:
                    self.carregamento['fase']  = 'mostrar'
                    self.carregamento['inicio'] = agora
            elif fase == 'mostrar':
                self.carregamento['alfa'] = 255
                if passado >= 700:
                    self.dialogo              = self.carregamento['npc'].obter_dialogo(self.gd)
                    self.carregamento['fase'] = 'dialogo'
            elif fase == 'sair':
                self.carregamento['alfa'] = max(0, 255 - int(passado / 400 * 255))
                if passado >= 400:
                    self.carregamento  = None
                    self.cooldown_loja = pygame.time.get_ticks() + 2000

        if self.hor.eh_meia_noite():
            self.jog.x, self.jog.y = 200.0, 280.0
            from src.states import EstadoDesmaio
            return EstadoDesmaio(self.gd)

        if self.hor.hora_cansado() and not self.hor.notificado_cansado:
            self.hor.notificado_cansado = True
            self.gd.msg_cansado         = True
            self.gd.timer_msg_cansado   = pygame.time.get_ticks()

        return None

    def desenhar(self, tela: pygame.Surface):
        W, H = tela.get_size()
        fonte_p = FONTES.get('pequena', pygame.font.SysFont('arial', 14))
        fonte_n = FONTES.get('normal',  pygame.font.SysFont('arial', 18))
        fonte_g = FONTES.get('grande',  pygame.font.SysFont('arial', 28, bold=True))

        # Fundo: tile de grama cobrindo tudo
        g = RECURSOS.obter_imagem('tile_grama', (TAM_TILE, TAM_TILE))
        for ty in range(0, H, TAM_TILE):
            for tx in range(0, W, TAM_TILE):
                tela.blit(g, (tx, ty))

        # Estrada central
        cam = RECURSOS.obter_imagem('chao_cidade', (TAM_TILE, TAM_TILE))
        for ty in range(0, H, TAM_TILE):
            for tx in range(165, 635, TAM_TILE):
                tela.blit(cam, (tx, ty))

        # 4 predios
        self._desenhar_predio(tela, fonte_p, _NW, 'Sementes',   porta_sul=True,  sprite='casa_vila')
        self._desenhar_predio(tela, fonte_p, _NE, 'Pesca',      porta_sul=True,  sprite='casa_pescador')
        self._desenhar_predio(tela, fonte_p, _SW, 'Construcao', porta_sul=False, sprite='casa_vila')
        self._desenhar_predio(tela, fonte_p, _SE, 'Animais',    porta_sul=False, sprite='casa_vila')

        # Cercas ao redor (com gap nas portas)
        self._desenhar_cercas(tela)

        # Arvores e postes
        self._desenhar_decoracoes(tela, W, H)

        if self.loja_proxima is not None and not self.carregamento and not self.dialogo:
            dica = fonte_n.render('[ ENTER ] Entrar na loja', True, (255, 240, 140))
            somz = fonte_n.render('[ ENTER ] Entrar na loja', True, (0, 0, 0))
            tela.blit(somz, (W//2 - dica.get_width()//2 + 1, H//2 - 25))
            tela.blit(dica, (W//2 - dica.get_width()//2,     H//2 - 26))

        self.jog.desenhar(tela)
        self.inv.desenhar_hud(tela, fonte_p, fonte_normal=fonte_n, dia=self.hor.dia)
        self._desenhar_relogio(tela, W, fonte_n)

        seta = fonte_p.render('<- Sair (Fazenda)', True, (255, 242, 215))
        pygame.draw.rect(tela, (28, 22, 12),  (4, H//2-11, seta.get_width()+12, 22), border_radius=5)
        pygame.draw.rect(tela, (135,108, 60), (4, H//2-11, seta.get_width()+12, 22), 2, border_radius=5)
        tela.blit(seta, (10, H//2-7))

        tecla_inv = self.cfg.teclas.get('inventario', pygame.K_i)
        di = fonte_p.render(f'[{pygame.key.name(tecla_inv).upper()}] Inventario', True, (135,118,88))
        tela.blit(di, (W - di.get_width() - 8, H - 22))

        escuro = self.hor.nivel_escuridao()
        if escuro > 0:
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((0, 0, 30, int(escuro * 190)))
            tela.blit(ov, (0, 0))

        if self.gd.msg_cansado:
            idade = pygame.time.get_ticks() - self.gd.timer_msg_cansado
            if idade < 5000:
                alfa  = max(0, 255 - int((idade-3000)/2000*255)) if idade > 3000 else 255
                caixa = pygame.Surface((520, 68), pygame.SRCALPHA)
                caixa.fill((35, 18, 0, 220))
                pygame.draw.rect(caixa, (200,145,50), caixa.get_rect(), 2, border_radius=12)
                msg = fonte_g.render('Voce esta ficando cansado...', True, (255,200,50))
                caixa.blit(msg, (260 - msg.get_width()//2, 14))
                caixa.set_alpha(alfa)
                tela.blit(caixa, (W//2-260, H//2-34))
            else:
                self.gd.msg_cansado = False

        if self.carregamento and self.carregamento['fase'] in ('entrar','mostrar','dialogo','sair'):
            self._desenhar_loading(tela, W, H, fonte_g, fonte_n)

        if self.ver_inv:
            self.inv.desenhar_painel(tela, FONTES, self.gd.tem_vara)

        if self.dialogo:
            self.dialogo.desenhar(tela, FONTES)

    def _desenhar_relogio(self, tela, largura, fonte):
        hora_str, hora, _ = self.hor.hora_atual()
        noite  = hora >= 20
        surf   = fonte.render(hora_str, True, (255, 200, 100) if noite else (255, 255, 220))
        larg_b = surf.get_width() + 16
        x_b    = largura - larg_b - 4
        pygame.draw.rect(tela, (12,8,28) if noite else (18,18,45), (x_b, 4, larg_b, 30), border_radius=8)
        pygame.draw.rect(tela, (110,75,200) if noite else (75,75,155), (x_b, 4, larg_b, 30), 2, border_radius=8)
        tela.blit(surf, (x_b+8, 9))

    def _desenhar_loading(self, tela, W, H, fonte_g, fonte_n):
        alfa  = self.carregamento.get('alfa', 255)
        fase  = self.carregamento.get('fase', 'entrar')
        fundo = pygame.Surface((W, H))
        fundo.fill((12, 8, 4))
        fundo.set_alpha(alfa)
        tela.blit(fundo, (0, 0))
        if fase in ('mostrar', 'dialogo') and alfa >= 200:
            nome    = self.carregamento.get('nome', '')
            fonte_p = FONTES.get('pequena', pygame.font.SysFont('arial', 14))
            t1 = fonte_n.render('Entrando em:', True, (162, 142, 102))
            t2 = fonte_g.render(nome,           True, (255, 228, 155))
            t3 = fonte_p.render('Aguarde...',   True, (80,  72,  55))
            tela.blit(t1, (W//2 - t1.get_width()//2, H//2 - 48))
            tela.blit(t2, (W//2 - t2.get_width()//2, H//2 - 16))
            tela.blit(t3, (W//2 - t3.get_width()//2, H//2 + 30))

    def _desenhar_predio(self, tela, fonte_p, ret, placa, porta_sul, sprite='casa_vila'):
        x, y, larg, alt = ret.x, ret.y, ret.width, ret.height
        surf = RECURSOS.obter_imagem(sprite, (larg, alt))
        if not porta_sul:
            surf = pygame.transform.flip(surf, False, True)
        tela.blit(surf, (x, y))
        tp   = fonte_p.render(placa, True, (255, 240, 200))
        lp2  = tp.get_width() + 14
        xp2  = x + larg//2 - lp2//2
        y_pl = y + alt - 30 if porta_sul else y + 10
        pygame.draw.rect(tela, (115, 86, 44), (xp2, y_pl, lp2, 20), border_radius=4)
        pygame.draw.rect(tela, (90,  66, 30), (xp2, y_pl, lp2, 20), 2, border_radius=4)
        tela.blit(tp, (xp2+7, y_pl+3))

    def _desenhar_cercas(self, tela):
        FW, FH = 12, 21
        surf = RECURSOS.obter_imagem('cerca', (FW, FH))
        px2  = _PORTA_W // 2

        def faixa_h(x0, x1, y, gap_cx=None):
            for bx in range(x0, x1, FW):
                if gap_cx and abs(bx + FW//2 - gap_cx) < px2:
                    continue
                tela.blit(surf, (bx, y - FH//2))

        def faixa_v(x, y0, y1):
            for by in range(y0, y1, FH):
                tela.blit(surf, (x - FW//2, by))

        # NW
        faixa_h(0,   165, 210, _NW.x + _NW.width//2)
        faixa_v(165, 0,   210)
        # NE
        faixa_h(635, 800, 210, _NE.x + _NE.width//2)
        faixa_v(625, 0,   210)
        # SW
        faixa_h(0,   165, 390, _SW.x + _SW.width//2)
        faixa_v(165, 390, 600)
        # SE
        faixa_h(635, 800, 390, _SE.x + _SE.width//2)
        faixa_v(625, 390, 600)

    def _desenhar_decoracoes(self, tela, W, H):
        tree_w, tree_h = 44, 72
        for px in [252, 548]:
            surf = RECURSOS.obter_imagem('tile_arvore', (tree_w, tree_h))
            tela.blit(surf, (px - tree_w//2, H - 150 - tree_h//2))

        lw, lh = 24, 64
        for px in [315, 485]:
            surf = RECURSOS.obter_imagem('lampada', (lw, lh))
            tela.blit(surf, (px - lw//2, H//2 - lh + 10))
