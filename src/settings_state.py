import pygame
import sys

from src.states import EstadoBase, FONTES

ABAS = ['[ Tela ]', '[ Teclas ]', '[ Som ]']

LABELS_ACAO = {
    'cima':       'Cima',
    'baixo':      'Baixo',
    'esquerda':   'Esquerda',
    'direita':    'Direita',
    'interagir':  'Interagir',
    'plantar':    'Plantar',
    'colher':     'Colher',
    'pescar':     'Pescar',
    'cortar':     'Cortar Arvore',
    'ciclar':     'Trocar Semente',
}

LARG_PAINEL = 620
ALT_PAINEL  = 460
LARG_BARRA  = 300


def _nome_tecla(k: int) -> str:
    try:    return pygame.key.name(k).upper()
    except: return '???'


class EstadoConfiguracoes(EstadoBase):
    def __init__(self, dados_jogo, estado_anterior: EstadoBase):
        self.gd          = dados_jogo
        self.anterior    = estado_anterior
        self.cfg         = dados_jogo.configuracao
        self.aba         = 0
        self.linha       = 0
        self.rebindando  = None
        self.arrastando  = False
        self._fechar     = False
        self._sair       = False

    @property
    def _px(self): return 800 // 2 - LARG_PAINEL // 2
    @property
    def _py(self): return 600 // 2 - ALT_PAINEL  // 2
    @property
    def _cx(self): return self._px + 20
    @property
    def _cy(self): return self._py + 108

    def processar_eventos(self, eventos: list):
        for evento in eventos:
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                self._ao_clicar(evento.pos)
            elif evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
                self.arrastando = False
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

        from src.assets import tocar_som

        if self.rebindando:
            return

        # Troca de aba
        larg_aba = LARG_PAINEL // len(ABAS)
        for i in range(len(ABAS)):
            tx = px + i * larg_aba
            if tx <= mx <= tx + larg_aba and py + 50 <= my <= py + 88:
                self.aba   = i
                self.linha = 0
                tocar_som('tecla', self.cfg.volumes)
                return

        # Botao Voltar
        if pygame.Rect(px + 16, py + ALT_PAINEL - 52, 130, 36).collidepoint(mx, my):
            tocar_som('tecla', self.cfg.volumes)
            self._fechar = True
            return

        # Botao Sair
        if pygame.Rect(px + LARG_PAINEL - 148, py + ALT_PAINEL - 52, 132, 36).collidepoint(mx, my):
            tocar_som('tecla', self.cfg.volumes)
            self._sair = True
            return

        if self.aba == 0:   # Tela
            btn = pygame.Rect(cx, cy + 20, 320, 44)
            if btn.collidepoint(mx, my):
                tocar_som('tecla', self.cfg.volumes)
                self.cfg.tela_cheia        = not self.cfg.tela_cheia
                self.cfg.mudanca_resolucao = True
            if pygame.Rect(cx, cy + 84, 260, 36).collidepoint(mx, my):
                tocar_som('tecla', self.cfg.volumes)
                self.gd.inventario.dinheiro += 10_000

        elif self.aba == 1:  # Teclas
            acoes  = list(LABELS_ACAO.keys())
            alt_li = 30
            for i, acao in enumerate(acoes):
                if pygame.Rect(cx-4, cy + i * alt_li - 2, LARG_PAINEL-32, alt_li).collidepoint(mx, my):
                    tocar_som('tecla', self.cfg.volumes)
                    self.linha      = i
                    self.rebindando = acao
                    break

        elif self.aba == 2:  # Som
            bar_x  = cx + 140
            slider_g = pygame.Rect(bar_x, cy + 20, LARG_BARRA, 22)
            slider_m = pygame.Rect(bar_x, cy + 60, LARG_BARRA, 22)
            if slider_g.collidepoint(mx, my):
                self.arrastando = 'geral'
                self.linha = 0
                tocar_som('tecla', self.cfg.volumes)
                self._arrastar(mx)
            elif slider_m.collidepoint(mx, my):
                self.arrastando = 'musica'
                self.linha = 1
                tocar_som('tecla', self.cfg.volumes)
                self._arrastar(mx)

    def _arrastar(self, mx: int):
        if not self.arrastando:
            return
        bar_x = self._cx + 140
        valor = (mx - bar_x) / LARG_BARRA
        self.cfg.volumes[self.arrastando] = max(0.0, min(1.0, valor))
        if self.arrastando == 'musica':
            from src.assets import atualizar_volume_musica
            atualizar_volume_musica(self.cfg.volumes)

    def _ao_pressionar_tecla(self, tecla: int):
        from src.assets import tocar_som
        if self.rebindando:
            if tecla != pygame.K_ESCAPE:
                self.cfg.teclas[self.rebindando] = tecla
                tocar_som('tecla', self.cfg.volumes)
            self.rebindando = None
            return

        tocar_som('tecla', self.cfg.volumes)
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
        if self.aba == 1: return len(LABELS_ACAO) - 1
        if self.aba == 2: return 1
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
            chave = 'geral' if self.linha == 0 else 'musica'
            v = self.cfg.volumes.get(chave, 0.7 if chave == 'geral' else 0.5)
            self.cfg.volumes[chave] = max(0.0, min(1.0, v + delta))
            if chave == 'musica':
                from src.assets import atualizar_volume_musica
                atualizar_volume_musica(self.cfg.volumes)

    # -- Desenho -------------------------------------------------------
    def desenhar(self, tela: pygame.Surface):
        largura, altura = tela.get_size()
        px, py = self._px, self._py
        cx, cy = self._cx, self._cy
        mx, my = pygame.mouse.get_pos()

        self.anterior.desenhar(tela)
        overlay = pygame.Surface((largura, altura), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 192))
        tela.blit(overlay, (0, 0))

        painel = pygame.Surface((LARG_PAINEL, ALT_PAINEL), pygame.SRCALPHA)
        painel.fill((16, 18, 44, 252))
        pygame.draw.rect(painel, (70, 80, 175, 255), painel.get_rect(), 3, border_radius=16)
        tela.blit(painel, (px, py))

        fonte_g = FONTES.get('grande', pygame.font.SysFont('arial', 28, bold=True))
        fonte_n = FONTES.get('normal', pygame.font.SysFont('arial', 18))
        fonte_p = FONTES.get('pequena', pygame.font.SysFont('arial', 14))

        titulo = fonte_g.render('Configuracoes', True, (255, 238, 120))
        tela.blit(titulo, (px + LARG_PAINEL // 2 - titulo.get_width() // 2, py + 12))

        larg_aba = LARG_PAINEL // len(ABAS)
        for i, label in enumerate(ABAS):
            tx     = px + i * larg_aba
            sel    = i == self.aba
            hover  = tx <= mx <= tx + larg_aba and py + 50 <= my <= py + 88
            bg_cor = (50, 65, 160) if sel else (35, 35, 70) if hover else (25, 26, 55)
            brd_cor = (110, 140, 255) if sel else (60, 60, 100)
            pygame.draw.rect(tela, bg_cor,  (tx,   py+50, larg_aba,   38), border_radius=7)
            pygame.draw.rect(tela, brd_cor, (tx+1, py+51, larg_aba-2, 36), 2, border_radius=7)
            ts = fonte_n.render(label, True, (255, 255, 255) if sel else (140, 140, 170))
            tela.blit(ts, (tx + larg_aba // 2 - ts.get_width() // 2, py + 58))

        pygame.draw.line(tela, (50, 50, 100), (px+8, py+92), (px+LARG_PAINEL-8, py+92), 1)

        if self.aba == 0:   self._desenhar_aba_tela(tela, cx, cy, fonte_n, fonte_p, mx, my)
        elif self.aba == 1: self._desenhar_aba_teclas(tela, cx, cy, fonte_p, mx, my)
        elif self.aba == 2: self._desenhar_aba_som(tela, cx, cy, fonte_n, fonte_p, mx, my)

        # Botao Voltar
        ret_vol = pygame.Rect(px + 16, py + ALT_PAINEL - 52, 130, 36)
        hover_v = ret_vol.collidepoint(mx, my)
        pygame.draw.rect(tela, (45, 90, 160) if hover_v else (30, 65, 120), ret_vol, border_radius=9)
        pygame.draw.rect(tela, (80, 140, 255), ret_vol, 2, border_radius=9)
        tv = fonte_n.render('< Voltar', True, (255, 255, 255))
        tela.blit(tv, (ret_vol.centerx - tv.get_width()//2, ret_vol.centery - tv.get_height()//2))

        # Botao Sair
        ret_sai = pygame.Rect(px + LARG_PAINEL - 148, py + ALT_PAINEL - 52, 132, 36)
        hover_s = ret_sai.collidepoint(mx, my)
        pygame.draw.rect(tela, (160, 40, 40) if hover_s else (110, 28, 28), ret_sai, border_radius=9)
        pygame.draw.rect(tela, (255, 80, 80), ret_sai, 2, border_radius=9)
        ts = fonte_n.render('Sair do Jogo', True, (255, 220, 220))
        tela.blit(ts, (ret_sai.centerx - ts.get_width()//2, ret_sai.centery - ts.get_height()//2))

        dica = fonte_p.render('ESC = Salvar e voltar  |  TAB = trocar aba', True, (70, 70, 90))
        tela.blit(dica, (px + LARG_PAINEL//2 - dica.get_width()//2, py + ALT_PAINEL - 18))

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
        status = 'ATIVA' if self.cfg.tela_cheia else 'DESATIVADA'
        btn    = pygame.Rect(cx, cy + 20, 320, 44)
        hover  = btn.collidepoint(mx, my)
        pygame.draw.rect(tela, (55, 75, 160) if hover else (38, 45, 110), btn, border_radius=10)
        pygame.draw.rect(tela, (100, 130, 255), btn, 2, border_radius=10)
        ls = fonte_n.render(f'Tela Cheia: [ {status} ]', True, (255, 255, 100))
        tela.blit(ls, (btn.centerx - ls.get_width()//2, btn.centery - ls.get_height()//2))

    def _desenhar_aba_teclas(self, tela, cx, cy, fonte_p, mx, my):
        acoes  = list(LABELS_ACAO.keys())
        alt_li = 30
        cabec  = fonte_p.render(f"{'Acao':<22}{'Tecla Atual':>80}", True, (140, 140, 210))
        tela.blit(cabec, (cx, cy - 20))

        for i, acao in enumerate(acoes):
            ry    = cy + i * alt_li
            sel   = i == self.linha
            hover = pygame.Rect(cx-4, ry-2, LARG_PAINEL-32, alt_li).collidepoint(mx, my)
            if sel or hover:
                fundo = pygame.Surface((LARG_PAINEL-32, alt_li-2), pygame.SRCALPHA)
                fundo.fill((50, 60, 160, 180) if sel else (30, 30, 70, 120))
                tela.blit(fundo, (cx-4, ry))

            cor   = (255, 255, 100) if sel else (200, 200, 200)
            pref  = '> ' if sel else '  '
            tela.blit(fonte_p.render(pref + LABELS_ACAO[acao], True, cor),  (cx,     ry + 5))
            tela.blit(fonte_p.render(f'[ {_nome_tecla(self.cfg.teclas.get(acao, 0))} ]',
                                     True, (160, 210, 255)), (cx+400, ry + 5))

        nota = fonte_p.render('Clique ou ENTER para rebind  (ESC cancela)', True, (80, 80, 80))
        tela.blit(nota, (cx, cy + len(acoes) * alt_li + 8))

    def _desenhar_aba_som(self, tela, cx, cy, fonte_n, fonte_p, mx, my):
        # Volume Geral
        vol_g = self.cfg.volumes.get('geral', 0.7)
        label_g_cor = (255, 255, 100) if (self.linha == 0) else (200, 200, 200)
        pref_g = '> ' if (self.linha == 0) else '  '
        label_g = fonte_n.render(pref_g + 'Volume Geral', True, label_g_cor)
        tela.blit(label_g, (cx, cy + 24))

        # Slider Geral
        bar_x = cx + 140
        bar_y_g = cy + 20
        slider_ret_g = pygame.Rect(bar_x, bar_y_g, LARG_BARRA, 22)
        pygame.draw.rect(tela, (40, 42, 75), slider_ret_g, border_radius=6)
        preen_g = int(LARG_BARRA * vol_g)
        if preen_g > 0:
            pygame.draw.rect(tela, (80, 180, 255), (bar_x, bar_y_g, preen_g, 22), border_radius=6)
        hx_g = bar_x + preen_g
        h_cor_g = (255, 255, 255) if slider_ret_g.collidepoint(mx, my) else (200, 200, 220)
        pygame.draw.circle(tela, h_cor_g, (hx_g, bar_y_g + 11), 11)
        pygame.draw.circle(tela, (80, 80, 140), (hx_g, bar_y_g + 11), 11, 2)
        pct_g = fonte_n.render(f'{int(vol_g * 100)}%', True, label_g_cor)
        tela.blit(pct_g, (bar_x + LARG_BARRA + 14, bar_y_g + 2))

        # Music Volume
        vol_m = self.cfg.volumes.get('musica', 0.5)
        label_m_cor = (255, 255, 100) if (self.linha == 1) else (200, 200, 200)
        pref_m = '> ' if (self.linha == 1) else '  '
        label_m = fonte_n.render(pref_m + 'Musica', True, label_m_cor)
        tela.blit(label_m, (cx, cy + 64))

        # Slider Musica
        bar_y_m = cy + 60
        slider_ret_m = pygame.Rect(bar_x, bar_y_m, LARG_BARRA, 22)
        pygame.draw.rect(tela, (40, 42, 75), slider_ret_m, border_radius=6)
        preen_m = int(LARG_BARRA * vol_m)
        if preen_m > 0:
            pygame.draw.rect(tela, (80, 180, 255), (bar_x, bar_y_m, preen_m, 22), border_radius=6)
        hx_m = bar_x + preen_m
        h_cor_m = (255, 255, 255) if slider_ret_m.collidepoint(mx, my) else (200, 200, 220)
        pygame.draw.circle(tela, h_cor_m, (hx_m, bar_y_m + 11), 11)
        pygame.draw.circle(tela, (80, 80, 140), (hx_m, bar_y_m + 11), 11, 2)
        pct_m = fonte_n.render(f'{int(vol_m * 100)}%', True, label_m_cor)
        tela.blit(pct_m, (bar_x + LARG_BARRA + 14, bar_y_m + 2))

        nota = fonte_p.render('Clique/arraste  ou  <- -> para ajustar', True, (80, 80, 80))
        tela.blit(nota, (cx, cy + 110))
