"""
configuracoes_estado.py / settings_state.py — Tela de Configurações (ESC).

3 Abas (clicáveis com mouse):
  🖥 Tela   – fullscreen / janela
  ⌨ Teclas  – rebind de teclas (click ou ENTER)
  🔊 Sons   – sliders de volume com mouse

Botões: [Voltar] e [Sair do Jogo]
Salva config.json ao sair.
"""
import pygame
import sys

from src.states   import EstadoBase, FONTES

ABAS = ['🖥  Tela', '⌨  Teclas', '🔊  Sons']

# Labels das ações de teclado (chaves PT → texto exibido)
LABELS_ACAO = {
    'cima':       'Cima',
    'baixo':      'Baixo',
    'esquerda':   'Esquerda',
    'direita':    'Direita',
    'interagir':  'Interagir',
    'plantar':    'Plantar',
    'colher':     'Colher',
    'pescar':     'Pescar',
    'cortar':     'Cortar Árvore',
    'ciclar':     'Trocar Semente',
}

LABELS_VOLUME = {
    'animais':    '🐄 Animais',
    'plantas':    '🌱 Plantas',
    'pesca':      '🎣 Pesca',
    'interface':  '🖱 Interface',
    'musica':     '🎵 Música',
}

LARG_PAINEL = 620
ALT_PAINEL  = 460
LARG_BARRA  = 200


def _nome_tecla(k: int) -> str:
    try:    return pygame.key.name(k).upper()
    except: return '???'


class EstadoConfiguracoes(EstadoBase):
    def __init__(self, dados_jogo, estado_anterior: EstadoBase):
        self.gd      = dados_jogo
        self.anterior = estado_anterior
        self.cfg     = dados_jogo.configuracao
        self.aba     = 0
        self.linha   = 0
        self.rebindando    = None   # ação sendo rebindada (str) ou None
        self.arrastando    = None   # categoria de volume sendo arrastada
        self._fechar       = False
        self._sair         = False

    # ── Posições do painel ───────────────────────────────────────
    @property
    def _px(self): return 800 // 2 - LARG_PAINEL // 2
    @property
    def _py(self): return 600 // 2 - ALT_PAINEL  // 2
    @property
    def _cx(self): return self._px + 20
    @property
    def _cy(self): return self._py + 108

    # ── Processar eventos ────────────────────────────────────────
    def processar_eventos(self, eventos: list):
        for evento in eventos:
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                self._ao_clicar(evento.pos)
            elif evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
                self.arrastando = None
            elif evento.type == pygame.MOUSEMOTION:
                if self.arrastando and evento.buttons[0]:
                    self._arrastar(evento.pos[0])
            elif evento.type == pygame.KEYDOWN:
                self._ao_pressionar_tecla(evento.key)

        if self._sair:
            self.cfg.salvar()
            pygame.quit()
            sys.exit()
        if self._fechar:
            self.cfg.salvar()
            return self.anterior
        return self

    def _ao_clicar(self, pos):
        mx, my = pos
        px, py = self._px, self._py
        cx, cy = self._cx, self._cy

        if self.rebindando:
            return

        # Troca de aba
        larg_aba = LARG_PAINEL // len(ABAS)
        for i in range(len(ABAS)):
            tx = px + i * larg_aba
            if tx <= mx <= tx + larg_aba and py + 50 <= my <= py + 88:
                self.aba   = i
                self.linha = 0
                return

        # Botão Voltar
        if pygame.Rect(px + 16, py + ALT_PAINEL - 52, 130, 36).collidepoint(mx, my):
            self._fechar = True
            return

        # Botão Sair
        if pygame.Rect(px + LARG_PAINEL - 148, py + ALT_PAINEL - 52, 132, 36).collidepoint(mx, my):
            self._sair = True
            return

        # Conteúdo das abas
        if self.aba == 0:   # Tela
            btn       = pygame.Rect(cx, cy + 20, 320, 44)
            btn_debug = pygame.Rect(cx, cy + 84, 260, 36)
            if btn.collidepoint(mx, my):
                self.cfg.tela_cheia        = not self.cfg.tela_cheia
                self.cfg.mudanca_resolucao = True
            if btn_debug.collidepoint(mx, my):
                self.gd.inventario.dinheiro += 10_000

        elif self.aba == 1:  # Teclas
            acoes  = list(LABELS_ACAO.keys())
            alt_li = 30
            for i, acao in enumerate(acoes):
                if pygame.Rect(cx-4, cy + i * alt_li - 2, LARG_PAINEL-32, alt_li).collidepoint(mx, my):
                    self.linha     = i
                    self.rebindando = acao
                    break

        elif self.aba == 2:  # Sons
            cats  = list(LABELS_VOLUME.keys())
            bar_x = cx + 190
            alt_li = 52
            for i, cat in enumerate(cats):
                slider = pygame.Rect(bar_x, cy + i * alt_li + 2, LARG_BARRA, 22)
                if slider.collidepoint(mx, my):
                    self.arrastando = cat
                    self.linha      = i
                    self._arrastar(mx)
                    break

    def _arrastar(self, mx: int):
        if not self.arrastando:
            return
        bar_x = self._cx + 190
        valor = (mx - bar_x) / LARG_BARRA
        self.cfg.volumes[self.arrastando] = max(0.0, min(1.0, valor))

    def _ao_pressionar_tecla(self, tecla: int):
        if self.rebindando:
            if tecla != pygame.K_ESCAPE:
                self.cfg.teclas[self.rebindando] = tecla
            self.rebindando = None
            return

        if tecla == pygame.K_ESCAPE:
            self._fechar = True
        elif tecla in (pygame.K_UP, pygame.K_w):
            self.linha = max(0, self.linha - 1)
        elif tecla in (pygame.K_DOWN, pygame.K_s):
            self.linha = min(self._max_linha(), self.linha + 1)
        elif tecla == pygame.K_TAB:
            self.aba   = (self.aba + 1) % len(ABAS)
            self.linha = 0
        elif tecla in (pygame.K_RETURN, pygame.K_e):
            self._ao_confirmar()
        elif tecla in (pygame.K_LEFT, pygame.K_a):
            self._ajustar_volume(-0.05)
        elif tecla in (pygame.K_RIGHT, pygame.K_d):
            self._ajustar_volume(+0.05)

    def _max_linha(self):
        if self.aba == 0: return 0
        if self.aba == 1: return len(LABELS_ACAO) - 1
        if self.aba == 2: return len(LABELS_VOLUME) - 1
        return 0

    def _ao_confirmar(self):
        if self.aba == 0:
            self.cfg.tela_cheia        = not self.cfg.tela_cheia
            self.cfg.mudanca_resolucao = True
        elif self.aba == 1:
            acoes = list(LABELS_ACAO.keys())
            if self.linha < len(acoes):
                self.rebindando = acoes[self.linha]

    def _ajustar_volume(self, delta: float):
        if self.aba == 2:
            cats = list(LABELS_VOLUME.keys())
            if self.linha < len(cats):
                cat = cats[self.linha]
                self.cfg.volumes[cat] = max(0.0, min(1.0, self.cfg.volumes.get(cat, 0.5) + delta))

    # ── Desenho ──────────────────────────────────────────────────
    def desenhar(self, tela: pygame.Surface):
        largura, altura = tela.get_size()
        px, py = self._px, self._py
        cx, cy = self._cx, self._cy
        mx, my = pygame.mouse.get_pos()

        # Estado anterior como fundo
        self.anterior.desenhar(tela)
        overlay = pygame.Surface((largura, altura), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 192))
        tela.blit(overlay, (0, 0))

        # Painel
        painel = pygame.Surface((LARG_PAINEL, ALT_PAINEL), pygame.SRCALPHA)
        painel.fill((16, 18, 44, 252))
        pygame.draw.rect(painel, (70, 80, 175, 255), painel.get_rect(), 3, border_radius=16)
        tela.blit(painel, (px, py))

        fonte_g = FONTES.get('grande', pygame.font.SysFont('arial', 28, bold=True))
        fonte_n = FONTES.get('normal', pygame.font.SysFont('arial', 18))
        fonte_p = FONTES.get('pequena', pygame.font.SysFont('arial', 14))

        titulo = fonte_g.render('⚙  Configurações', True, (255, 238, 120))
        tela.blit(titulo, (px + LARG_PAINEL // 2 - titulo.get_width() // 2, py + 12))

        # Abas
        larg_aba = LARG_PAINEL // len(ABAS)
        for i, label in enumerate(ABAS):
            tx      = px + i * larg_aba
            sel     = i == self.aba
            hover   = tx <= mx <= tx + larg_aba and py + 50 <= my <= py + 88
            bg_cor  = (50, 65, 160) if sel else (35, 35, 70) if hover else (25, 26, 55)
            brd_cor = (110, 140, 255) if sel else (60, 60, 100)
            pygame.draw.rect(tela, bg_cor,  (tx,   py+50, larg_aba,   38), border_radius=7)
            pygame.draw.rect(tela, brd_cor, (tx+1, py+51, larg_aba-2, 36), 2, border_radius=7)
            ts = fonte_n.render(label, True, (255,255,255) if sel else (140,140,170))
            tela.blit(ts, (tx + larg_aba // 2 - ts.get_width() // 2, py + 58))

        pygame.draw.line(tela, (50, 50, 100), (px+8, py+92), (px+LARG_PAINEL-8, py+92), 1)

        # Conteúdo
        if self.aba == 0:   self._desenhar_aba_tela(tela, cx, cy, fonte_n, fonte_p, mx, my)
        elif self.aba == 1: self._desenhar_aba_teclas(tela, cx, cy, fonte_p, mx, my)
        elif self.aba == 2: self._desenhar_aba_sons(tela, cx, cy, fonte_n, fonte_p, mx, my)

        # Botão Voltar
        ret_vol = pygame.Rect(px + 16, py + ALT_PAINEL - 52, 130, 36)
        hover_v = ret_vol.collidepoint(mx, my)
        pygame.draw.rect(tela, (45, 90, 160) if hover_v else (30, 65, 120), ret_vol, border_radius=9)
        pygame.draw.rect(tela, (80, 140, 255), ret_vol, 2, border_radius=9)
        tv = fonte_n.render('◀  Voltar', True, (255, 255, 255))
        tela.blit(tv, (ret_vol.centerx - tv.get_width()//2, ret_vol.centery - tv.get_height()//2))

        # Botão Sair
        ret_sai = pygame.Rect(px + LARG_PAINEL - 148, py + ALT_PAINEL - 52, 132, 36)
        hover_s = ret_sai.collidepoint(mx, my)
        pygame.draw.rect(tela, (160, 40, 40) if hover_s else (110, 28, 28), ret_sai, border_radius=9)
        pygame.draw.rect(tela, (255, 80, 80), ret_sai, 2, border_radius=9)
        ts = fonte_n.render('Sair do Jogo', True, (255, 220, 220))
        tela.blit(ts, (ret_sai.centerx - ts.get_width()//2, ret_sai.centery - ts.get_height()//2))

        dica = fonte_p.render('ESC = Salvar e voltar  |  TAB = trocar aba', True, (70, 70, 90))
        tela.blit(dica, (px + LARG_PAINEL//2 - dica.get_width()//2, py + ALT_PAINEL - 18))

        # Overlay de rebind
        if self.rebindando:
            ov2 = pygame.Surface((largura, altura), pygame.SRCALPHA)
            ov2.fill((0, 0, 0, 215))
            tela.blit(ov2, (0, 0))
            label = LABELS_ACAO.get(self.rebindando, self.rebindando)
            msg   = fonte_g.render(f'Nova tecla para: {label}', True, (255, 210, 80))
            tela.blit(msg, (largura//2 - msg.get_width()//2, altura//2 - 22))
            h2    = fonte_n.render('Pressione qualquer tecla  (ESC = cancelar)', True, (160, 160, 160))
            tela.blit(h2,  (largura//2 - h2.get_width()//2, altura//2 + 24))

    def _desenhar_aba_tela(self, tela, cx, cy, fonte_n, fonte_p, mx, my):
        """Aba de configurações de tela."""
        label  = f"Tela Cheia: {'✅  Ativa' if self.cfg.tela_cheia else '☐  Desativada'}"
        btn    = pygame.Rect(cx, cy + 20, 320, 44)
        hover  = btn.collidepoint(mx, my)
        pygame.draw.rect(tela, (55, 75, 160) if hover else (38, 45, 110), btn, border_radius=10)
        pygame.draw.rect(tela, (100, 130, 255), btn, 2, border_radius=10)
        ls = fonte_n.render(label, True, (255, 255, 100))
        tela.blit(ls, (btn.centerx - ls.get_width()//2, btn.centery - ls.get_height()//2))

        # Botão debug
        btn_d  = pygame.Rect(cx, cy + 84, 260, 36)
        hov_d  = btn_d.collidepoint(mx, my)
        pygame.draw.rect(tela, (60, 35, 90) if hov_d else (40, 22, 65), btn_d, border_radius=8)
        pygame.draw.rect(tela, (180, 80, 255), btn_d, 2, border_radius=8)
        dbt = fonte_p.render('💰 +10.000 moedas (debug/teste)', True, (210, 160, 255))
        tela.blit(dbt, (btn_d.x + 10, btn_d.centery - dbt.get_height()//2))

        nota = fonte_p.render('Clique ou ENTER para alternar tela cheia.', True, (90, 90, 90))
        tela.blit(nota, (cx, cy + 132))

    def _desenhar_aba_teclas(self, tela, cx, cy, fonte_p, mx, my):
        """Aba de configurações de teclas."""
        acoes  = list(LABELS_ACAO.keys())
        alt_li = 30
        cabec  = fonte_p.render(f"{'Ação':<30}{'Tecla Atual':>14}", True, (140, 140, 210))
        tela.blit(cabec, (cx, cy - 20))

        for i, acao in enumerate(acoes):
            ry    = cy + i * alt_li
            sel   = i == self.linha
            hover = pygame.Rect(cx-4, ry-2, LARG_PAINEL-32, alt_li).collidepoint(mx, my)
            if sel or hover:
                fundo = pygame.Surface((LARG_PAINEL-32, alt_li-2), pygame.SRCALPHA)
                fundo.fill((50, 60, 160, 180) if sel else (30, 30, 70, 120))
                tela.blit(fundo, (cx-4, ry))

            cor  = (255, 255, 100) if sel else (200, 200, 200)
            pref = '▶ ' if sel else '  '
            label_acao = fonte_p.render(pref + LABELS_ACAO[acao], True, cor)
            label_tecla = fonte_p.render(
                f'[ {_nome_tecla(self.cfg.teclas.get(acao, 0))} ]', True, (160, 210, 255))
            tela.blit(label_acao,  (cx,     ry + 5))
            tela.blit(label_tecla, (cx+400, ry + 5))

        nota = fonte_p.render('Clique ou ENTER para rebind  (ESC cancela rebind)', True, (80, 80, 80))
        tela.blit(nota, (cx, cy + len(acoes) * alt_li + 8))

    def _desenhar_aba_sons(self, tela, cx, cy, fonte_n, fonte_p, mx, my):
        """Aba de configurações de volume."""
        cats   = list(LABELS_VOLUME.keys())
        bar_x  = cx + 190
        alt_li = 52

        for i, cat in enumerate(cats):
            ry   = cy + i * alt_li
            sel  = i == self.linha
            vol  = self.cfg.volumes.get(cat, 0.5)
            cor  = (255, 255, 100) if sel else (200, 200, 200)

            pref  = '▶ ' if sel else '  '
            label = fonte_p.render(pref + LABELS_VOLUME[cat], True, cor)
            tela.blit(label, (cx, ry + 6))

            # Trilha do slider
            slider_ret = pygame.Rect(bar_x, ry + 3, LARG_BARRA, 20)
            pygame.draw.rect(tela, (40, 42, 75), slider_ret, border_radius=6)

            # Preenchimento
            preen = int(LARG_BARRA * vol)
            if preen > 0:
                cor_fill = (80, 180, 255) if sel else (55, 130, 200)
                pygame.draw.rect(tela, cor_fill, (bar_x, ry+3, preen, 20), border_radius=6)

            # Handle
            hx      = bar_x + preen
            h_hover = slider_ret.collidepoint(mx, my)
            h_cor   = (255, 255, 255) if h_hover else (200, 200, 220)
            pygame.draw.circle(tela, h_cor,     (hx, ry + 13), 10)
            pygame.draw.circle(tela, (80,80,140),(hx, ry + 13), 10, 2)

            pct = fonte_p.render(f'{int(vol * 100)}%', True, cor)
            tela.blit(pct, (bar_x + LARG_BARRA + 10, ry + 4))

        nota = fonte_p.render('Clique/arraste a barra  ou  ← → para ajustar', True, (80, 80, 80))
        tela.blit(nota, (cx, cy + len(cats) * alt_li + 8))
