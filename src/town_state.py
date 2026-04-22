"""
cidade_estado.py / town_state.py — Cidade Rústica (jogador único).

Como funciona:
  • O jogador entra pela borda direita vindo da fazenda
  • 4 lojas nos cantos: Sementes (NW), Pesca (NE), Construção (SW), Animais (SE)
  • Para entrar numa loja: aproxime da porta e pressione ENTER
  • Para sair da cidade: caminhe até a borda esquerda (x < 5)
  • Tecla [I] abre o inventário completo
"""
import pygame
import math

from src.states    import EstadoBase, FONTES
from src.constants import TAM_TILE, COLUNAS
from src.entities  import NPCFazendeiro, NPCPescador, NPCVendedorAnimais, NPCConstrutor
from src import assets as RECURSOS


class EstadoCidade(EstadoBase):
    """Estado da cidade com 4 lojas nos cantos e visual rústico de roça velha."""

    def __init__(self, dados_jogo):
        self.gd  = dados_jogo
        self.cfg = dados_jogo.configuracao
        self.inv = dados_jogo.inventario
        self.hor = dados_jogo.horario
        self.jog = dados_jogo.jogador

        # NPCs de cada loja
        self.npcs = [
            NPCFazendeiro(       82,  80),   # NW — Fazendeiro (sementes)
            NPCPescador(        718,  80),   # NE — Pescador
            NPCVendedorAnimais( 718, 490),   # SE — Vendedor de Animais
            NPCConstrutor(       82, 490),   # SW — Construtor
        ]

        # Retângulos de colisão dos 4 prédios
        self.ret_predios = [
            pygame.Rect(  0,   0, 165, 210),  # NW — Sementes
            pygame.Rect(635,   0, 165, 210),  # NE — Pesca
            pygame.Rect(  0, 390, 165, 210),  # SW — Construção
            pygame.Rect(635, 390, 165, 210),  # SE — Animais
        ]

        NOMES_LOJAS   = ['Loja do Fazendeiro', 'Loja do Pescador',
                         'Loja do Construtor',  'Loja do Vendedor de Animais']
        # Índice em self.npcs para cada loja (0=NW, 1=NE, 2=SW, 3=SE)
        NPC_DA_LOJA   = [0, 1, 3, 2]
        self._nomes   = NOMES_LOJAS
        self._npc_idx = NPC_DA_LOJA

        # Estado interno
        self.dialogo      = None    # diálogo aberto (None = nenhum)
        self.carregamento = None    # animação de loading ao entrar/sair
        self.ver_inv      = False   # painel de inventário aberto?
        self.cooldown_loja = 0      # ms mínimo antes de entrar em nova loja
        self.loja_proxima  = None   # índice da loja próxima (ou None)

        dados_jogo.ultimo_mapa = 'cidade'

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Detecção de loja na frente do jogador
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _loja_na_frente(self):
        """
        Retorna o índice da loja (0–3) se o jogador estiver na porta.
        Retorna None se estiver longe de qualquer loja.
        """
        cx   = self.jog.x + 16   # centro horizontal do jogador
        topo = self.jog.y         # borda superior
        base = self.jog.y + 48   # borda inferior

        # Lojas do topo (NW=0 e NE=1): jogador encosta pela base dos prédios
        if 207 <= topo <= 220:
            if   0 <= cx <= 165: return 0
            if 635 <= cx <= 800: return 1

        # Lojas de baixo (SW=2 e SE=3): jogador encosta pelo topo dos prédios
        if 385 <= base <= 398:
            if   0 <= cx <= 165: return 2
            if 635 <= cx <= 800: return 3

        return None

    def _abrir_loja(self, indice: int):
        """Inicia animação de loading e depois abre o diálogo."""
        npc              = self.npcs[self._npc_idx[indice]]
        self.carregamento = {
            'npc':   npc,
            'nome':  self._nomes[indice],
            'fase':  'entrar',    # entrar → mostrar → dialogo → sair
            'alfa':  0,
            'inicio': pygame.time.get_ticks(),
        }

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Processar eventos
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def processar_eventos(self, eventos: list):
        # Repassa eventos para o diálogo ativo
        if self.dialogo:
            aberto = self.dialogo.processar_eventos(eventos, self.cfg.teclas)
            if not aberto:
                self.dialogo = None
                self.carregamento['fase']  = 'sair'
                self.carregamento['alfa']  = 255
                self.carregamento['inicio'] = pygame.time.get_ticks()
            return self

        for evento in eventos:
            if evento.type != pygame.KEYDOWN:
                continue
            tecla  = evento.key
            mapa_t = self.cfg.teclas

            # ESC
            if tecla == pygame.K_ESCAPE:
                if self.ver_inv:
                    self.ver_inv = False
                    continue
                from src.settings_state import EstadoConfiguracoes
                return EstadoConfiguracoes(self.gd, estado_anterior=self)

            # I — inventário
            if tecla == mapa_t.get('inventario', pygame.K_i):
                self.ver_inv = not self.ver_inv
                continue

            # ENTER — entrar na loja
            if tecla in (pygame.K_RETURN, pygame.K_KP_ENTER):
                agora = pygame.time.get_ticks()
                if self.loja_proxima is not None and agora > self.cooldown_loja:
                    self._abrir_loja(self.loja_proxima)

        return self

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Atualização por frame
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def atualizar(self):
        # Movimentação de jogador (bloqueia durante loading ou diálogo)
        if not self.dialogo and not self.carregamento:
            teclas_press = pygame.key.get_pressed()
            self.jog.mover(teclas_press, self.cfg.teclas, self.ret_predios)

        # Limitar posição
        self.jog.x = max(0.0, min(self.jog.x, 790.0))
        self.jog.y = max(0.0, min(self.jog.y, 555.0))

        # Sair da cidade pela borda esquerda → vai para fazenda
        if self.jog.x < 5:
            self.jog.x = float((COLUNAS - 2) * TAM_TILE)
            self.jog.y = 300.0
            from src.farm_state import EstadoFazenda
            return EstadoFazenda(self.gd)

        # Detectar loja próxima
        self.loja_proxima = self._loja_na_frente()

        # Máquina de estados do loading
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

        # Verificar meia-noite
        if self.hor.eh_meia_noite():
            self.jog.x, self.jog.y = 200.0, 280.0
            from src.states import EstadoDesmaio
            return EstadoDesmaio(self.gd)

        # Verificar cansaço
        if self.hor.hora_cansado() and not self.hor.notificado_cansado:
            self.hor.notificado_cansado = True
            self.gd.msg_cansado         = True
            self.gd.timer_msg_cansado   = pygame.time.get_ticks()

        return None

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Desenho
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def desenhar(self, tela: pygame.Surface):
        largura, altura = tela.get_size()
        fonte_p = FONTES.get('pequena', pygame.font.SysFont('arial', 14))
        fonte_n = FONTES.get('normal',  pygame.font.SysFont('arial', 18))
        fonte_g = FONTES.get('grande',  pygame.font.SysFont('arial', 28, bold=True))

        # Chão rústico
        tela.fill((172, 140, 88))

        # Estrada central
        x_est, larg_est = 165, 470
        pygame.draw.rect(tela, (155, 122, 74), (x_est, 0, larg_est, altura))
        for linha_y in range(0, altura, 5):
            e = 6 if (linha_y // 4) % 2 == 0 else 0
            pygame.draw.line(tela, (155-e, 122-e, 74-e),
                             (x_est, linha_y), (x_est + larg_est, linha_y), 1)

        # Calçada de pedras
        cor_pc = (148, 135, 112)
        cor_pe = (125, 112, 90)
        for linha_y in range(0, altura, 16):
            for base_x in [x_est, x_est + larg_est - 22]:
                for col_p in range(5):
                    px = base_x + col_p * 4 + ((linha_y // 16) % 2) * 2
                    cor = cor_pc if (linha_y + col_p) % 2 == 0 else cor_pe
                    pygame.draw.rect(tela, cor, (px, linha_y+2, 14, 10), border_radius=2)

        # Prédios dos 4 cantos
        self._desenhar_loja(tela, fonte_p, pygame.Rect(0, 0, 165, 210),
                             (185,158,108), (132,72,22), (62,112,38),
                             '🌾 Sementes', 196, porta_sul=True,
                             extras=self._extras_sementes)
        self._desenhar_loja(tela, fonte_p, pygame.Rect(635, 0, 165, 210),
                             (145,162,172), (62,88,115), (35,72,128),
                             '🐟 Pesca & Cia', 196, porta_sul=True,
                             extras=self._extras_pesca)
        self._desenhar_loja(tela, fonte_p, pygame.Rect(0, 390, 165, 210),
                             (162,145,122), (92,75,58), (85,55,26),
                             '🔨 Construção', 375, porta_sul=False,
                             extras=self._extras_construcao)
        self._desenhar_loja(tela, fonte_p, pygame.Rect(635, 390, 165, 210),
                             (172,155,115), (122,85,36), (125,70,26),
                             '🐄 Animais', 375, porta_sul=False,
                             extras=self._extras_animais)

        # Centro (poço, árvores, lanternas)
        self._desenhar_centro(tela, largura, altura)

        # Dica de entrada na loja
        if self.loja_proxima is not None and not self.carregamento and not self.dialogo:
            dica = fonte_n.render('[ ENTER ] Entrar na loja', True, (255, 240, 140))
            somz = fonte_n.render('[ ENTER ] Entrar na loja', True, (0, 0, 0))
            cx_d = largura // 2 - dica.get_width() // 2
            cy_d = altura  // 2 - 24
            tela.blit(somz, (cx_d + 1, cy_d + 1))
            tela.blit(dica, (cx_d, cy_d))

        # Jogador
        self.jog.desenhar(tela)

        # HUD
        self.inv.desenhar_hud(tela, fonte_p)
        self._desenhar_relogio(tela, largura, fonte_n)

        # Seta ← Fazenda
        seta = fonte_p.render('← Sair (Fazenda)', True, (255, 242, 215))
        pygame.draw.rect(tela, (28, 22, 12),  (4, altura//2-11, seta.get_width()+12, 22), border_radius=5)
        pygame.draw.rect(tela, (135,108, 60), (4, altura//2-11, seta.get_width()+12, 22), 2, border_radius=5)
        tela.blit(seta, (10, altura//2-7))

        # Dica inventário
        tecla_inv = self.cfg.teclas.get('inventario', pygame.K_i)
        di = fonte_p.render(f'[{pygame.key.name(tecla_inv).upper()}] Inventário', True, (135,118,88))
        tela.blit(di, (largura - di.get_width() - 8, altura - 22))

        # Escuridão noturna
        escuro = self.hor.nivel_escuridao()
        if escuro > 0:
            ov = pygame.Surface((largura, altura), pygame.SRCALPHA)
            ov.fill((0, 0, 30, int(escuro * 190)))
            tela.blit(ov, (0, 0))

        # Aviso de cansaço
        if self.gd.msg_cansado:
            idade = pygame.time.get_ticks() - self.gd.timer_msg_cansado
            if idade < 5000:
                alfa  = max(0, 255 - int((idade-3000)/2000*255)) if idade > 3000 else 255
                caixa = pygame.Surface((520, 68), pygame.SRCALPHA)
                caixa.fill((35, 18, 0, 220))
                pygame.draw.rect(caixa, (200,145,50), caixa.get_rect(), 2, border_radius=12)
                msg = fonte_g.render('Você está ficando cansado...', True, (255,200,50))
                caixa.blit(msg, (260 - msg.get_width()//2, 14))
                caixa.set_alpha(alfa)
                tela.blit(caixa, (largura//2-260, altura//2-34))
            else:
                self.gd.msg_cansado = False

        # Tela de loading
        if self.carregamento and self.carregamento['fase'] in ('entrar','mostrar','dialogo','sair'):
            self._desenhar_loading(tela, largura, altura, fonte_g, fonte_n)

        # Painel de inventário
        if self.ver_inv:
            self.inv.desenhar_painel(tela, FONTES, self.gd.tem_vara)

        # Diálogo
        if self.dialogo:
            self.dialogo.desenhar(tela, FONTES)

    # ── Helpers de desenho ───────────────────────────────────────
    def _desenhar_relogio(self, tela, largura, fonte):
        hora_str, hora, _ = self.hor.hora_atual()
        noite   = hora >= 20
        cor_h   = (255, 200, 100) if noite else (255, 255, 220)
        surf    = fonte.render(f'🕐 {hora_str}', True, cor_h)
        larg_b  = surf.get_width() + 16
        x_b     = largura - larg_b - 4
        pygame.draw.rect(tela, (12,8,28) if noite else (18,18,45),
                         (x_b, 4, larg_b, 30), border_radius=8)
        pygame.draw.rect(tela, (110,75,200) if noite else (75,75,155),
                         (x_b, 4, larg_b, 30), 2, border_radius=8)
        tela.blit(surf, (x_b+8, 9))

    def _desenhar_loading(self, tela, largura, altura, fonte_g, fonte_n):
        alfa  = self.carregamento.get('alfa', 255)
        fase  = self.carregamento.get('fase', 'entrar')
        fundo = pygame.Surface((largura, altura))
        fundo.fill((12, 8, 4))
        fundo.set_alpha(alfa)
        tela.blit(fundo, (0, 0))

        if fase in ('mostrar', 'dialogo') and alfa >= 200:
            nome    = self.carregamento.get('nome', '')
            fonte_p = FONTES.get('pequena', pygame.font.SysFont('arial', 14))
            t1 = fonte_n.render('Entrando em:', True, (162, 142, 102))
            t2 = fonte_g.render(nome,           True, (255, 228, 155))
            t3 = fonte_p.render('Aguarde...',   True, (80,  72,  55))
            tela.blit(t1, (largura//2 - t1.get_width()//2, altura//2 - 48))
            tela.blit(t2, (largura//2 - t2.get_width()//2, altura//2 - 16))
            tela.blit(t3, (largura//2 - t3.get_width()//2, altura//2 + 30))

    def _desenhar_loja(self, tela, fonte_p, ret, cor_parede, cor_telhado,
                       cor_porta, placa, y_placa, porta_sul, extras=None):
        """Desenha um prédio rústico de loja num dos cantos da cidade."""
        x, y, larg, alt = ret.x, ret.y, ret.width, ret.height
        y_parede = y + alt // 3

        # Sombra
        sombra = pygame.Surface((larg+6, alt+6), pygame.SRCALPHA)
        sombra.fill((0, 0, 0, 78))
        tela.blit(sombra, (x+5, y+5))

        # Parede
        pygame.draw.rect(tela, cor_parede, (x, y_parede, larg, alt - alt//3))
        cor_tab = (max(0,cor_parede[0]-18), max(0,cor_parede[1]-14), max(0,cor_parede[2]-10))
        for lpy in range(y_parede+7, y+alt, 9):
            pygame.draw.line(tela, cor_tab, (x, lpy), (x+larg, lpy), 1)

        # Telhado
        if porta_sul:
            pts = [(x-5, y_parede+2), (x+larg//2, y+2), (x+larg+5, y_parede+2)]
        else:
            pts = [(x-5, y_parede-2), (x+larg//2, y+alt-2), (x+larg+5, y_parede-2)]
        pygame.draw.polygon(tela, cor_telhado, pts)
        cor_te = (max(0,cor_telhado[0]-20), max(0,cor_telhado[1]-16), max(0,cor_telhado[2]-12))
        pygame.draw.polygon(tela, cor_te, pts, 3)
        for i in range(5, 28, 6):
            fr  = i / 28
            if porta_sul:
                ry2 = int(y + 3 + (y_parede - y - 3) * fr)
            else:
                ry2 = int(y_parede - 2 - (y_parede - y - alt + alt//3) * fr * 0.5)
            rx1 = int((x-5) + i*(larg//2+5)/28)
            rx2 = int((x+larg+5) - i*(larg//2+5)/28)
            pygame.draw.line(tela, cor_te, (rx1, ry2), (rx2, ry2), 1)

        # Porta
        lp, ap = 26, 36
        xp = x + larg//2 - lp//2
        yp = y + alt - ap if porta_sul else y + 2
        pygame.draw.rect(tela, cor_porta, (xp, yp, lp, ap), border_radius=4)
        cor_pe2 = (max(0,cor_porta[0]-22), max(0,cor_porta[1]-16), max(0,cor_porta[2]-12))
        pygame.draw.rect(tela, cor_pe2, (xp, yp, lp, ap), 2, border_radius=4)
        pygame.draw.circle(tela, (198,172,48), (xp+lp-6, yp+ap//2), 3)

        # Janelas
        for xj in [x+10, x+larg-30]:
            yj = y_parede + 14
            pygame.draw.rect(tela, (188,222,255), (xj, yj, 20, 16))
            pygame.draw.line(tela, (120,155,190), (xj+10, yj), (xj+10, yj+16), 1)
            pygame.draw.line(tela, (120,155,190), (xj, yj+8), (xj+20, yj+8), 1)

        # Extras decorativos
        if extras:
            extras(tela, ret)

        # Placa pendurada
        tp = fonte_p.render(placa, True, (255, 240, 200))
        lp2 = tp.get_width() + 14
        xp2 = x + larg//2 - lp2//2
        pygame.draw.line(tela, (88,70,36), (xp2+8, y_placa-10), (xp2+8, y_placa), 2)
        pygame.draw.line(tela, (88,70,36), (xp2+lp2-8, y_placa-10), (xp2+lp2-8, y_placa), 2)
        pygame.draw.rect(tela, (115,86,44), (xp2, y_placa, lp2, 20), border_radius=4)
        pygame.draw.rect(tela, (90,66,30),  (xp2, y_placa, lp2, 20), 2, border_radius=4)
        tela.blit(tp, (xp2+7, y_placa+3))

    # ── Extras decorativos por tipo de loja ─────────────────────
    def _extras_sementes(self, tela, ret):
        x, y, larg, alt = ret.x, ret.y, ret.width, ret.height
        for bx in [x+10, x+28]:
            pygame.draw.ellipse(tela, (128,88,42),  (bx, y+alt-44, 18, 8))
            pygame.draw.rect(tela,    (148,108,55),  (bx, y+alt-52, 18, 20))
            pygame.draw.ellipse(tela, (148,108,55),  (bx, y+alt-52, 18, 8))
            pygame.draw.line(tela, (108,78,38), (bx, y+alt-42), (bx+18, y+alt-42), 2)
        pygame.draw.rect(tela, (155,76,36), (x+larg-22, y+alt-30, 14, 12))
        pygame.draw.circle(tela, (72,188,72), (x+larg-15, y+alt-32), 8)

    def _extras_pesca(self, tela, ret):
        x, y, larg, alt = ret.x, ret.y, ret.width, ret.height
        for nx in range(x+6, x+44, 10):
            pygame.draw.line(tela, (78,78,78), (nx, y+95), (nx+8, y+125), 1)
        pygame.draw.line(tela, (78,78,78), (x+6, y+95), (x+44, y+95), 1)
        pygame.draw.ellipse(tela, (78,98,125),  (x+larg-26, y+alt-44, 18, 8))
        pygame.draw.rect(tela,    (92,115,145),  (x+larg-26, y+alt-52, 18, 20))
        pygame.draw.ellipse(tela, (92,115,145),  (x+larg-26, y+alt-52, 18, 8))

    def _extras_construcao(self, tela, ret):
        x, y, larg, alt = ret.x, ret.y, ret.width, ret.height
        for i in range(3):
            pygame.draw.rect(tela, (145,105,52), (x+8, y+alt-50+i*10, 44, 8))
            pygame.draw.line(tela, (115,80,36), (x+8, y+alt-46+i*10), (x+52, y+alt-46+i*10), 1)
        pygame.draw.rect(tela, (98,62,26),   (x+larg-24, y+alt-52, 5, 22))
        pygame.draw.rect(tela, (152,152,158),(x+larg-28, y+alt-52, 14, 9))

    def _extras_animais(self, tela, ret):
        x, y, larg, alt = ret.x, ret.y, ret.width, ret.height
        for fx in range(x+6, x+40, 10):
            pygame.draw.rect(tela, (135,95,45), (fx, y+alt-38, 5, 24))
        pygame.draw.line(tela, (152,112,56), (x+6, y+alt-30), (x+40, y+alt-30), 3)
        pygame.draw.line(tela, (152,112,56), (x+6, y+alt-20), (x+40, y+alt-20), 3)
        pygame.draw.circle(tela, (255,232,55), (x+larg-20, y+alt-44), 8)
        pygame.draw.ellipse(tela, (255,232,55), (x+larg-28, y+alt-36, 22, 14))

    def _desenhar_centro(self, tela, largura, altura):
        """Poço, árvores decorativas e postes de lanterna."""
        cx, cy = largura // 2, altura // 2

        # Poço
        pygame.draw.ellipse(tela, (165,142,105), (cx-30, cy-4,  60, 20))
        pygame.draw.ellipse(tela, (108,95,75),   (cx-30, cy-4,  60, 20), 3)
        pygame.draw.ellipse(tela, (82,72,60),    (cx-24, cy-8,  48, 16))
        pygame.draw.ellipse(tela, (28,38,50),    (cx-22, cy-6,  44, 12))
        pygame.draw.rect(tela, (128,115,95), (cx-24, cy-28, 6, 24))
        pygame.draw.rect(tela, (128,115,95), (cx+18, cy-28, 6, 24))
        pygame.draw.rect(tela, (108,95,75),  (cx-26, cy-32, 54, 7))
        pygame.draw.line(tela, (75,58,35),   (cx+3, cy-26), (cx+3, cy-8), 1)
        pygame.draw.rect(tela, (88,65,35),   (cx-1, cy-8, 8, 6))

        # Árvores decorativas
        for pos_a in [largura//2 - 145, largura//2 + 105]:
            pygame.draw.rect(tela, (88,55,22),  (pos_a, altura-110, 12, 42))
            pygame.draw.circle(tela, (35,118,35), (pos_a+6, altura-115), 22)
            pygame.draw.circle(tela, (28,98,28),  (pos_a+6, altura-118), 16)

        # Postes de lanterna
        for pos_p in [largura//2 - 85, largura//2 + 65]:
            pygame.draw.rect(tela, (68,52,32),  (pos_p, altura//2-55, 5, 65))
            pygame.draw.rect(tela, (68,68,42),  (pos_p-6, altura//2-60, 17, 12))
            pygame.draw.rect(tela, (248,215,95),(pos_p-4, altura//2-58, 13, 8))
