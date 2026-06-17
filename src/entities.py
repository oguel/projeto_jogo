import pygame
import random
import math

from src.constants import (
    TAM_TILE, PRECOS_VENDA, PRECOS_COMPRA, CUSTO_ANIMAIS, CUSTO_REPARO,
    ESTABULO_QUEBRADO, ESTABULO_FIXO, GALINHEIRO_QUEBRADO, GALINHEIRO_FIXO,
    ID_SEMENTE, ID_SEMENTE_ESP, ID_MUDA,
    ID_PEIXE_COMUM, ID_PEIXE_DOURADO, ID_PEIXE_RARO,
    ID_COLHEITA, ID_COLHEITA_ESP, ID_MADEIRA,
    RET_ESTABULO, RET_GALINHEIRO,
)
from src import assets as RECURSOS


# Jogador - sprite direcional, um unico jogador

LARG_JOG = 32
ALT_JOG  = 48

class Jogador:
    def __init__(self):
        self.x: float    = 300.0
        self.y: float    = 280.0
        self.velocidade   = 4
        self.direcao      = 'baixo'
        self.pescando     = False

    def mover(self, teclas_pressionadas, mapa_teclas: dict,
              colisoes: list | None = None):
        """Move o jogador com base nas teclas pressionadas."""
        dx = dy = 0
        if teclas_pressionadas[mapa_teclas.get('esquerda', pygame.K_a)]:  dx -= self.velocidade
        if teclas_pressionadas[mapa_teclas.get('direita',  pygame.K_d)]:  dx += self.velocidade
        if teclas_pressionadas[mapa_teclas.get('cima',     pygame.K_w)]:  dy -= self.velocidade
        if teclas_pressionadas[mapa_teclas.get('baixo',    pygame.K_s)]:  dy += self.velocidade

        if   dx < 0: self.direcao = 'esquerda'
        elif dx > 0: self.direcao = 'direita'
        elif dy < 0: self.direcao = 'cima'
        elif dy > 0: self.direcao = 'baixo'

        novo_x, novo_y = self.x + dx, self.y + dy
        ret = pygame.Rect(int(novo_x), int(novo_y), LARG_JOG, ALT_JOG)
        if colisoes and any(ret.colliderect(col) for col in colisoes):
            return
        self.x, self.y = novo_x, novo_y

    def posicao_tile(self) -> tuple[int, int]:
        """Retorna o tile onde o jogador está (base dos pés)."""
        cx = int(self.x + LARG_JOG // 2)
        cy = int(self.y + ALT_JOG - 4)   # base dos pes
        return cx // TAM_TILE, cy // TAM_TILE

    def obter_ret(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), LARG_JOG, ALT_JOG)

    def desenhar(self, tela: pygame.Surface):
        mapa_dir = {'cima': 'up', 'baixo': 'down', 'esquerda': 'left', 'direita': 'right'}
        sufixo   = mapa_dir.get(self.direcao, 'down')
        surf     = RECURSOS.obter_imagem(f'jogador_{sufixo}', (LARG_JOG, ALT_JOG))
        tela.blit(surf, (int(self.x), int(self.y)))




# Diálogo

class OpcaoDialogo:
    """Uma opção clicável dentro de um diálogo de NPC."""
    def __init__(self, rotulo: str, acao, habilitado: bool = True):
        self.rotulo    = rotulo
        self.acao      = acao
        self.habilitado = habilitado


class ItemVenda:
    """Um item vendável com quantidade selecionável."""
    def __init__(self, rotulo: str, id_item: str, preco_unitario: int, cor: tuple):
        self.rotulo          = rotulo
        self.id_item         = id_item
        self.preco_unitario  = preco_unitario
        self.cor             = cor
        self.quantidade      = 1   # quantidade selecionada para vender


class DialogoNPC:
    """Caixa de diálogo com lista de opções (mouse + teclado)."""
    LARG = 440
    ALT  = 320

    def __init__(self, titulo: str, opcoes: list):
        self.titulo    = titulo
        self.opcoes    = list(opcoes)
        self.selecionado = 0
        self.mensagem  = ''
        self.timer_msg = 0
        # Sempre adiciona a opção "Fechar" no final se não existir
        if not any(o.rotulo == 'Fechar' for o in self.opcoes):
            self.opcoes.append(OpcaoDialogo('Fechar', lambda dados: None))

    def processar_eventos(self, eventos: list, teclas: dict, volumes: dict | None = None) -> bool:
        """
        Processa eventos do diálogo.
        Retorna False quando o diálogo deve ser fechado.
        """
        largura, altura = 800, 600
        bx    = largura // 2 - self.LARG // 2
        by    = altura  // 2 - self.ALT  // 2
        alt_linha = 34

        for evento in eventos:
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                mx, my = evento.pos
                for i, opcao in enumerate(self.opcoes):
                    linha_y = by + 60 + i * alt_linha
                    if bx <= mx <= bx + self.LARG and linha_y <= my <= linha_y + alt_linha:
                        self.selecionado = i
                        RECURSOS.tocar_som('tecla', volumes)
                        if opcao.rotulo == 'Fechar':
                            return False
                        if opcao.habilitado:
                            resultado       = opcao.acao(None)
                            self.mensagem   = resultado or ''
                            self.timer_msg  = pygame.time.get_ticks()
                        break

            elif evento.type == pygame.KEYDOWN:
                tecla_cima     = teclas.get('cima',     pygame.K_w)
                tecla_baixo    = teclas.get('baixo',    pygame.K_s)
                tecla_interagir = teclas.get('interagir', pygame.K_e)

                if evento.key in (tecla_cima, pygame.K_UP):
                    self.selecionado = (self.selecionado - 1) % len(self.opcoes)
                    RECURSOS.tocar_som('tecla', volumes)
                elif evento.key in (tecla_baixo, pygame.K_DOWN):
                    self.selecionado = (self.selecionado + 1) % len(self.opcoes)
                    RECURSOS.tocar_som('tecla', volumes)
                elif evento.key in (tecla_interagir, pygame.K_RETURN):
                    opcao = self.opcoes[self.selecionado]
                    RECURSOS.tocar_som('tecla', volumes)
                    if opcao.rotulo == 'Fechar':
                        return False
                    if opcao.habilitado:
                        resultado       = opcao.acao(None)
                        self.mensagem   = resultado or ''
                        self.timer_msg  = pygame.time.get_ticks()
                elif evento.key == pygame.K_ESCAPE:
                    RECURSOS.tocar_som('tecla', volumes)
                    return False

        return True

    def desenhar(self, tela: pygame.Surface, fontes: dict):
        """Desenha a caixa de diálogo na tela."""
        largura, altura = tela.get_size()
        bx = largura // 2 - self.LARG // 2
        by = altura  // 2 - self.ALT  // 2
        alt_linha = 34
        mx, my    = pygame.mouse.get_pos()

        fundo = pygame.Surface((self.LARG, self.ALT), pygame.SRCALPHA)
        fundo.fill((18, 18, 40, 240))
        pygame.draw.rect(fundo, (80, 80, 180), fundo.get_rect(), 3, border_radius=14)
        tela.blit(fundo, (bx, by))

        fonte_g = fontes.get('grande', pygame.font.SysFont('arial', 24, bold=True))
        fonte_n = fontes.get('normal', pygame.font.SysFont('arial', 18))
        fonte_p = fontes.get('pequena', pygame.font.SysFont('arial', 14))

        titulo = fonte_g.render(self.titulo, True, (255, 240, 140))
        tela.blit(titulo, (bx + self.LARG // 2 - titulo.get_width() // 2, by + 12))

        for i, opcao in enumerate(self.opcoes):
            linha_y = by + 60 + i * alt_linha
            hover  = bx <= mx <= bx + self.LARG and linha_y <= my <= linha_y + alt_linha
            sel    = i == self.selecionado
            cor_fundo = (60, 60, 180, 160) if sel else (40, 40, 80, 80) if hover else (0, 0, 0, 0)
            bg_linha  = pygame.Surface((self.LARG - 16, alt_linha - 2), pygame.SRCALPHA)
            bg_linha.fill(cor_fundo)
            tela.blit(bg_linha, (bx + 8, linha_y + 1))
            cor   = (255, 255, 100) if sel else (200, 200, 200) if opcao.habilitado else (100, 100, 100)
            pref  = '> ' if sel else '  '
            linha = fonte_n.render(pref + opcao.rotulo, True, cor)
            tela.blit(linha, (bx + 18, linha_y + 6))

        if self.mensagem and pygame.time.get_ticks() - self.timer_msg < 2500:
            msg = fonte_p.render(self.mensagem, True, (100, 255, 150))
            tela.blit(msg, (bx + 12, by + self.ALT - 28))

        dica = fonte_p.render('W/S = navegar  Enter = selecionar  ESC = fechar', True, (70, 70, 70))
        tela.blit(dica, (bx + self.LARG // 2 - dica.get_width() // 2, by + self.ALT - 14))


class DialogoNPCAbas:
    """
    Caixa de diálogo com múltiplas abas.
    - Aba de compra: lista de OpcaoDialogo (padrão)
    - Aba de venda: lista de ItemVenda com seletor de quantidade
    Q / E (ou seta esquerda/direita) trocam de aba.
    Na aba de venda: W/S selecionam item, </> ajustam quantidade, Enter confirma.
    """
    LARG = 500
    ALT  = 400

    # Paleta
    COR_FUNDO      = (14, 14, 36, 248)
    COR_BORDA      = (70, 70, 180)
    COR_ABA_ATIVA  = (50, 50, 160, 230)
    COR_ABA_INATI  = (25, 25, 70, 180)
    COR_TITULO     = (255, 240, 140)
    COR_SEL        = (60, 60, 200, 180)
    COR_HOVER      = (40, 40, 100, 100)
    COR_MSG_OK     = (80, 255, 140)
    COR_MSG_ERR    = (255, 100, 100)
    COR_DICA       = (70, 70, 120)

    def __init__(self, titulo: str, abas: list):
        """
        abas: lista de dicts com chaves:
          'nome'  : str - rotulo da aba
          'tipo'  : 'compra' | 'venda'
          'itens' : list[OpcaoDialogo] ou list[ItemVenda]
        """
        self.titulo       = titulo
        self.abas         = abas
        self.aba_atual    = 0
        self.selecionado  = 0
        self.mensagem     = ''
        self.timer_msg    = 0
        self.cor_msg      = self.COR_MSG_OK

    # -- utilidades internas --?
    def _itens(self):
        return self.abas[self.aba_atual]['itens']

    def _tipo(self):
        return self.abas[self.aba_atual]['tipo']

    def _trocar_aba(self, delta: int):
        self.aba_atual   = (self.aba_atual + delta) % len(self.abas)
        self.selecionado = 0

    def _msg(self, texto: str, ok: bool = True):
        self.mensagem  = texto
        self.timer_msg = pygame.time.get_ticks()
        self.cor_msg   = self.COR_MSG_OK if ok else self.COR_MSG_ERR

    # -- eventos --
    def processar_eventos(self, eventos: list, teclas: dict, volumes: dict | None = None) -> bool:
        """Retorna False quando o diálogo deve ser fechado."""
        mods = pygame.key.get_mods()
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                k    = evento.key
                t    = teclas
                ctrl = mods & pygame.KMOD_SHIFT  # Shift = grandes saltos

                # Fechar
                if k == pygame.K_ESCAPE:
                    RECURSOS.tocar_som('tecla', volumes)
                    return False

                # Trocar aba: Tab / Q (anterior) / E (próxima)
                if k == pygame.K_TAB:
                    delta = -1 if (mods & pygame.KMOD_SHIFT) else +1
                    self._trocar_aba(delta)
                    RECURSOS.tocar_som('tecla', volumes)
                    continue
                if k == pygame.K_q:
                    self._trocar_aba(-1)
                    RECURSOS.tocar_som('tecla', volumes)
                    continue
                if k == pygame.K_e:
                    self._trocar_aba(+1)
                    RECURSOS.tocar_som('tecla', volumes)
                    continue

                itens = self._itens()
                if not itens:
                    continue

                # Navegar linhas: W/S
                cima  = t.get('cima',  pygame.K_w)
                baixo = t.get('baixo', pygame.K_s)
                if k in (cima, pygame.K_UP):
                    self.selecionado = (self.selecionado - 1) % len(itens)
                    RECURSOS.tocar_som('tecla', volumes)

                elif k in (baixo, pygame.K_DOWN):
                    self.selecionado = (self.selecionado + 1) % len(itens)
                    RECURSOS.tocar_som('tecla', volumes)

                # Ajustar quantidade com setas </> (apenas na aba de venda)
                elif k == pygame.K_LEFT and self._tipo() == 'venda':
                    item = itens[self.selecionado]
                    passo = 10 if ctrl else 1
                    item.quantidade = max(1, item.quantidade - passo)
                    RECURSOS.tocar_som('tecla', volumes)

                elif k == pygame.K_RIGHT and self._tipo() == 'venda':
                    item = itens[self.selecionado]
                    passo = 10 if ctrl else 1
                    item.quantidade += passo
                    RECURSOS.tocar_som('tecla', volumes)

                # Confirmar com Enter
                elif k == pygame.K_RETURN:
                    RECURSOS.tocar_som('tecla', volumes)
                    if self._tipo() == 'compra':
                        opcao = itens[self.selecionado]
                        if isinstance(opcao, OpcaoDialogo):
                            if opcao.rotulo == 'Fechar':
                                return False
                            if opcao.habilitado:
                                res = opcao.acao(None)
                                ok  = res is None or 'Precisa' not in res
                                self._msg(res or '', ok)
                    else:  # venda
                        item = itens[self.selecionado]
                        res  = item.acao(item.quantidade)
                        ok   = res is None or ('Sem ' not in res and 'Nada' not in res)
                        self._msg(res or '', ok)

            # Clique do mouse
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                mx, my = evento.pos
                bx = 800 // 2 - self.LARG // 2
                by = 600 // 2 - self.ALT  // 2

                # Clique nas abas (faixa logo abaixo do titulo)
                alt_titulo = 30
                aba_y      = by + alt_titulo + 1
                alt_aba    = 34
                larg_aba   = self.LARG // len(self.abas)
                if aba_y <= my <= aba_y + alt_aba:
                    for i in range(len(self.abas)):
                        ax0 = bx + i * larg_aba
                        if ax0 <= mx <= ax0 + larg_aba:
                            self.aba_atual   = i
                            self.selecionado = 0
                            RECURSOS.tocar_som('tecla', volumes)
                            break
                    continue

                # Clique nas linhas da aba
                itens     = self._itens()
                alt_linha = 44
                y_ini     = aba_y + alt_aba + 24
                for i, item in enumerate(itens):
                    ly = y_ini + i * alt_linha
                    if bx + 8 <= mx <= bx + self.LARG - 8 and ly <= my <= ly + alt_linha:
                        self.selecionado = i
                        RECURSOS.tocar_som('tecla', volumes)
                        if self._tipo() == 'compra':
                            opcao = item
                            if isinstance(opcao, OpcaoDialogo):
                                if opcao.rotulo == 'Fechar':
                                    return False
                                if opcao.habilitado:
                                    res = opcao.acao(None)
                                    ok  = res is None or 'Precisa' not in res
                                    self._msg(res or '', ok)
                        # Na venda, clique so seleciona
                        break

            # Scroll do mouse para ajustar quantidade na aba de venda
            elif evento.type == pygame.MOUSEWHEEL and self._tipo() == 'venda':
                itens = self._itens()
                if itens:
                    item = itens[self.selecionado]
                    item.quantidade = max(1, item.quantidade + evento.y)
                    RECURSOS.tocar_som('tecla', volumes)

        return True

    # -- desenho --
    def desenhar(self, tela: pygame.Surface, fontes: dict):
        largura, altura = tela.get_size()
        bx = largura // 2 - self.LARG // 2
        by = altura  // 2 - self.ALT  // 2

        fonte_g = fontes.get('grande',  pygame.font.SysFont('arial', 22, bold=True))
        fonte_n = fontes.get('normal',  pygame.font.SysFont('arial', 16))
        fonte_p = fontes.get('pequena', pygame.font.SysFont('arial', 13))

        # Fundo principal
        fundo = pygame.Surface((self.LARG, self.ALT), pygame.SRCALPHA)
        fundo.fill(self.COR_FUNDO)
        pygame.draw.rect(fundo, self.COR_BORDA, fundo.get_rect(), 2, border_radius=14)
        tela.blit(fundo, (bx, by))

        # Titulo no topo
        alt_titulo = 30
        txt_tit = fonte_g.render(self.titulo, True, self.COR_TITULO)
        tela.blit(txt_tit, (bx + self.LARG // 2 - txt_tit.get_width() // 2,
                             by + alt_titulo // 2 - txt_tit.get_height() // 2 + 2))
        pygame.draw.line(tela, self.COR_BORDA,
                         (bx + 10, by + alt_titulo), (bx + self.LARG - 10, by + alt_titulo), 1)

        # Abas
        larg_aba  = self.LARG // len(self.abas)
        alt_aba   = 34
        aba_y     = by + alt_titulo + 1
        for i, aba in enumerate(self.abas):
            ax0   = bx + i * larg_aba
            ativa = (i == self.aba_atual)
            cor_a = self.COR_ABA_ATIVA if ativa else self.COR_ABA_INATI
            surf_aba = pygame.Surface((larg_aba, alt_aba), pygame.SRCALPHA)
            surf_aba.fill(cor_a)
            if ativa:
                pygame.draw.line(surf_aba, (120, 140, 255), (0, 0), (larg_aba, 0), 3)
            pygame.draw.rect(surf_aba, self.COR_BORDA, surf_aba.get_rect(), 1)
            tela.blit(surf_aba, (ax0, aba_y))
            txt_aba = fonte_n.render(aba['nome'], True,
                                     (255, 255, 180) if ativa else (140, 140, 180))
            tela.blit(txt_aba, (ax0 + larg_aba // 2 - txt_aba.get_width() // 2,
                                aba_y + alt_aba // 2 - txt_aba.get_height() // 2))

        # Conteudo da aba
        itens     = self._itens()
        alt_linha = 44
        y_ini     = aba_y + alt_aba + 24
        mx, my    = pygame.mouse.get_pos()

        if self._tipo() == 'compra':
            self._desenhar_compra(tela, fontes, itens, bx, y_ini, alt_linha, mx, my,
                                  fonte_n, fonte_p)
        else:
            self._desenhar_venda(tela, fontes, itens, bx, y_ini, alt_linha, mx, my,
                                 fonte_n, fonte_p)

        # Mensagem de feedback
        if self.mensagem and pygame.time.get_ticks() - self.timer_msg < 2800:
            msg_surf = fonte_p.render(self.mensagem, True, self.cor_msg)
            tela.blit(msg_surf, (bx + self.LARG // 2 - msg_surf.get_width() // 2,
                                  by + self.ALT - 44))

        # Dica de teclado
        if self._tipo() == 'compra':
            dica = 'W/S navegar  Enter confirmar  Q/E ou Tab trocar aba  ESC fechar'
        else:
            dica = 'W/S item  </> qtd  Shift+</> x10  Scroll  Enter vender  Q/E aba'
        txt_dica = fonte_p.render(dica, True, self.COR_DICA)
        tela.blit(txt_dica, (bx + self.LARG // 2 - txt_dica.get_width() // 2,
                              by + self.ALT - 20))

    def _desenhar_compra(self, tela, fontes, itens, bx, y_ini, alt_linha, mx, my,
                         fonte_n, fonte_p):
        for i, opcao in enumerate(itens):
            ly  = y_ini + i * alt_linha
            sel = (i == self.selecionado)
            hov = bx + 8 <= mx <= bx + self.LARG - 8 and ly <= my <= ly + alt_linha
            cor_bg = self.COR_SEL if sel else (self.COR_HOVER if hov else (0, 0, 0, 0))
            bg = pygame.Surface((self.LARG - 16, alt_linha - 4), pygame.SRCALPHA)
            bg.fill(cor_bg)
            tela.blit(bg, (bx + 8, ly + 2))

            pref = '> ' if sel else '  '
            cor  = (255, 255, 100) if sel else ((200, 200, 200) if opcao.habilitado else (90, 90, 90))
            txt  = fonte_n.render(pref + opcao.rotulo, True, cor)
            tela.blit(txt, (bx + 18, ly + (alt_linha - txt.get_height()) // 2))

    def _desenhar_venda(self, tela, fontes, itens, bx, y_ini, alt_linha, mx, my,
                        fonte_n, fonte_p):
        # cabeçalho de colunas
        fonte_p.render('Item', True, (140, 140, 200))
        cab_itens  = fonte_p.render('Item',       True, (140, 140, 200))
        cab_est    = fonte_p.render('Estoque',    True, (140, 140, 200))
        cab_qtd    = fonte_p.render('Quantidade', True, (140, 140, 200))
        cab_preco  = fonte_p.render('Valor',      True, (140, 140, 200))
        tela.blit(cab_itens, (bx + 18,                       y_ini - 18))
        tela.blit(cab_est,   (bx + self.LARG - 280,          y_ini - 18))
        tela.blit(cab_qtd,   (bx + self.LARG - 200,          y_ini - 18))
        tela.blit(cab_preco, (bx + self.LARG - 90,           y_ini - 18))
        pygame.draw.line(tela, (50, 50, 100),
                         (bx + 8, y_ini - 4), (bx + self.LARG - 8, y_ini - 4))

        for i, item in enumerate(itens):
            ly  = y_ini + i * alt_linha
            sel = (i == self.selecionado)
            hov = bx + 8 <= mx <= bx + self.LARG - 8 and ly <= my <= ly + alt_linha
            cor_bg = self.COR_SEL if sel else (self.COR_HOVER if hov else (0, 0, 0, 0))
            bg = pygame.Surface((self.LARG - 16, alt_linha - 4), pygame.SRCALPHA)
            bg.fill(cor_bg)
            tela.blit(bg, (bx + 8, ly + 2))

            cy = ly + (alt_linha - fonte_n.get_height()) // 2

            # Bolinha colorida + nome
            pygame.draw.circle(tela, item.cor, (bx + 18, cy + fonte_n.get_height() // 2), 7)
            pref = '> ' if sel else '  '
            nome_surf = fonte_n.render(pref + item.rotulo, True,
                                       (255, 255, 120) if sel else (210, 210, 210))
            tela.blit(nome_surf, (bx + 28, cy))

            # Estoque
            est = item.estoque_fn()
            cor_est = (100, 200, 100) if est > 0 else (180, 80, 80)
            est_surf = fonte_n.render(str(est), True, cor_est)
            tela.blit(est_surf, (bx + self.LARG - 280, cy))

            # Seletor de quantidade
            qtd_max = est
            item.quantidade = max(1, min(item.quantidade, max(1, qtd_max)))
            qtd_surf = fonte_n.render(str(item.quantidade), True,
                                      (255, 220, 80) if sel else (200, 200, 120))
            tela.blit(qtd_surf, (bx + self.LARG - 200 + 30 - qtd_surf.get_width() // 2, cy))
            if sel:
                arr_l = fonte_p.render('<', True, (160, 160, 255))
                arr_r = fonte_p.render('>', True, (160, 160, 255))
                tela.blit(arr_l, (bx + self.LARG - 200,      cy + 3))
                tela.blit(arr_r, (bx + self.LARG - 200 + 54, cy + 3))

            # Valor total
            valor = item.quantidade * item.preco_unitario
            cor_v = (100, 240, 120) if est >= item.quantidade else (180, 80, 80)
            val_surf = fonte_n.render(f'${valor}', True, cor_v)
            tela.blit(val_surf, (bx + self.LARG - 90, cy))


# NPCs - base

LARG_NPC = 32
ALT_NPC  = 48

class NPCBase:
    def __init__(self, nome: str, chave_recurso: str, x: int, y: int):
        self.nome           = nome
        self.chave_recurso  = chave_recurso
        self.x, self.y     = x, y
        self.ret_interacao  = pygame.Rect(x - 36, y - 24, LARG_NPC + 72, ALT_NPC + 48)

    def desenhar(self, tela: pygame.Surface, fontes: dict, jogador_perto: bool = False):
        surf = RECURSOS.obter_imagem(self.chave_recurso, (LARG_NPC, ALT_NPC))
        tela.blit(surf, (self.x, self.y))
        fonte_p = fontes.get('pequena', pygame.font.SysFont('arial', 13))
        rotulo  = fonte_p.render(self.nome, True, (255, 255, 200))
        tela.blit(rotulo, (self.x + LARG_NPC // 2 - rotulo.get_width() // 2, self.y - 18))
        if jogador_perto:
            dica = fonte_p.render('[E] Falar', True, (180, 255, 180))
            tela.blit(dica, (self.x + LARG_NPC // 2 - dica.get_width() // 2, self.y + ALT_NPC + 4))

    def esta_perto(self, jogador) -> bool:
        """Verifica se o jogador está próximo o suficiente para interagir."""
        return self.ret_interacao.colliderect(jogador.obter_ret())

    def obter_dialogo(self, dados_jogo) -> DialogoNPC:
        return DialogoNPC(self.nome, [])

# NPCs específicos

class NPCFazendeiro(NPCBase):
    def __init__(self, x, y):
        super().__init__('Fazendeiro', 'npc_fazendeiro', x, y)

    def obter_dialogo(self, dados_jogo) -> DialogoNPCAbas:
        inv = dados_jogo.inventario

        # Aba Comprar
        def comprar(id_item, preco, atributo):
            def _comprar(dados):
                if inv.dinheiro >= preco:
                    inv.dinheiro -= preco
                    setattr(inv, atributo, getattr(inv, atributo) + 1)
                    return f'Comprado! Dinheiro: ${inv.dinheiro}'
                return f'Precisa de ${preco}!'
            return _comprar

        opcoes_compra = [
            OpcaoDialogo(f'Semente  (${PRECOS_COMPRA[ID_SEMENTE]} cada)',
                         comprar(ID_SEMENTE, PRECOS_COMPRA[ID_SEMENTE], 'semente')),
            OpcaoDialogo(f'Semente Especial  (${PRECOS_COMPRA[ID_SEMENTE_ESP]} cada)',
                         comprar(ID_SEMENTE_ESP, PRECOS_COMPRA[ID_SEMENTE_ESP], 'semente_esp')),
            OpcaoDialogo(f'Muda de Arvore  (${PRECOS_COMPRA[ID_MUDA]} cada)',
                         comprar(ID_MUDA, PRECOS_COMPRA[ID_MUDA], 'muda')),
            OpcaoDialogo('Fechar', lambda d: None),
        ]

        # Aba Vender
        def fazer_item_venda(rotulo, id_item, preco, cor):
            it = ItemVenda(rotulo, id_item, preco, cor)
            it.estoque_fn = lambda i=id_item: inv.quantidade(i)
            def _vender(qtd):
                est = inv.quantidade(id_item)
                if est <= 0:
                    return f'Sem {rotulo} no inventário!'
                qtd_real = min(qtd, est)
                total = qtd_real * preco
                inv.remover(id_item, qtd_real)
                inv.dinheiro += total
                return f'Vendeu {qtd_real}x {rotulo}: +${total}  (saldo: ${inv.dinheiro})'
            it.acao = _vender
            return it

        itens_venda = [
            fazer_item_venda('Trigo colhido',   ID_COLHEITA,     PRECOS_VENDA[ID_COLHEITA],     (240, 210,  50)),
            fazer_item_venda('Cenoura colhida', ID_COLHEITA_ESP, PRECOS_VENDA[ID_COLHEITA_ESP], (240, 100,  60)),
            fazer_item_venda('Madeira',         ID_MADEIRA,      PRECOS_VENDA[ID_MADEIRA],      (160, 110,  50)),
        ]

        return DialogoNPCAbas('Loja do Fazendeiro', [
            {'nome': 'Comprar',  'tipo': 'compra', 'itens': opcoes_compra},
            {'nome': 'Vender',   'tipo': 'venda',  'itens': itens_venda},
        ])


class NPCPescador(NPCBase):
    def __init__(self, x, y):
        super().__init__('Pescador', 'npc_pescador', x, y)

    def obter_dialogo(self, dados_jogo) -> DialogoNPCAbas:
        inv        = dados_jogo.inventario
        preco_vara = 30

        # Aba Comprar
        def comprar_vara(dados):
            if dados_jogo.tem_vara:
                return 'Voce ja tem uma vara de pesca!'
            if inv.dinheiro >= preco_vara:
                inv.dinheiro        -= preco_vara
                dados_jogo.tem_vara  = True
                return 'Vara comprada! Va ate o pier e pressione F.'
            return f'Precisa de ${preco_vara}!'

        rotulo_vara = f'Vara de Pesca (${preco_vara})' + \
                      (' [Comprada]' if dados_jogo.tem_vara else '')
        opcoes_compra = [
            OpcaoDialogo(rotulo_vara, comprar_vara, habilitado=not dados_jogo.tem_vara),
            OpcaoDialogo('Fechar', lambda d: None),
        ]

        # Aba Vender Peixes
        def fazer_item_peixe(rotulo, id_item, preco, cor):
            it = ItemVenda(rotulo, id_item, preco, cor)
            it.estoque_fn = lambda i=id_item: inv.quantidade(i)
            def _vender(qtd):
                est = inv.quantidade(id_item)
                if est <= 0:
                    return f'Sem {rotulo} no inventario!'
                qtd_real = min(qtd, est)
                total = qtd_real * preco
                inv.remover(id_item, qtd_real)
                inv.dinheiro += total
                return f'Vendeu {qtd_real}x {rotulo}: +${total}  (saldo: ${inv.dinheiro})'
            it.acao = _vender
            return it

        itens_peixes = [
            fazer_item_peixe('Peixe Comum',   ID_PEIXE_COMUM,   PRECOS_VENDA[ID_PEIXE_COMUM],   ( 80, 160, 255)),
            fazer_item_peixe('Peixe Dourado', ID_PEIXE_DOURADO, PRECOS_VENDA[ID_PEIXE_DOURADO], (255, 200,  40)),
            fazer_item_peixe('Peixe Raro',    ID_PEIXE_RARO,    PRECOS_VENDA[ID_PEIXE_RARO],    (180,  80, 240)),
        ]

        return DialogoNPCAbas('Pescador', [
            {'nome': 'Comprar',        'tipo': 'compra', 'itens': opcoes_compra},
            {'nome': 'Vender Peixes',  'tipo': 'venda',  'itens': itens_peixes},
        ])


class NPCVendedorAnimais(NPCBase):
    def __init__(self, x, y):
        super().__init__('Vendedor de Animais', 'npc_vendedor', x, y)

    def obter_dialogo(self, dados_jogo) -> DialogoNPC:
        inv     = dados_jogo.inventario
        predios = dados_jogo.predios
        opcoes  = []

        for tipo_animal, info in CUSTO_ANIMAIS.items():
            def criar_compra(a=tipo_animal, dados_animal=info):
                def comprar(dados):
                    # Verifica se o prédio está consertado
                    predio_req_quebrado = ESTABULO_QUEBRADO if dados_animal['predio'] == ESTABULO_FIXO \
                                         else GALINHEIRO_QUEBRADO
                    if predios.get(predio_req_quebrado) != dados_animal['predio']:
                        nome_predio = 'estábulo' if dados_animal['predio'] == ESTABULO_FIXO else 'galinheiro'
                        return f'Conserte o {nome_predio} primeiro!'
                    if inv.dinheiro >= dados_animal['dinheiro']:
                        inv.dinheiro -= dados_animal['dinheiro']
                        import random as _r
                        if a == 'galinha':
                            # Nasce dentro do galinheiro
                            ax, ay = _r.uniform(210, 300), _r.uniform(8, 100)
                        else:
                            # Nasce dentro do estábulo
                            ax, ay = _r.uniform(8, 145), _r.uniform(290, 420)
                        dados_jogo.animais.append({
                            'tipo': a, 'x': ax, 'y': ay,
                            'vx': _r.uniform(-1, 1),
                            'vy': _r.uniform(-1, 1),
                        })
                        return f'{dados_animal["nome"]} comprado!'
                    return f'Precisa de ${dados_animal["dinheiro"]}!'
                return comprar
            opcoes.append(OpcaoDialogo(f'{info["nome"]} (${info["dinheiro"]})', criar_compra()))

        return DialogoNPC('Vendedor de Animais', opcoes)


class NPCConstrutor(NPCBase):
    def __init__(self, x, y):
        super().__init__('Construtor', 'npc_construtor', x, y)

    def obter_dialogo(self, dados_jogo) -> DialogoNPC:
        inv     = dados_jogo.inventario
        predios = dados_jogo.predios
        opcoes  = []

        reparos = [
            (ESTABULO_QUEBRADO,   ESTABULO_FIXO,   'Estábulo'),
            (GALINHEIRO_QUEBRADO, GALINHEIRO_FIXO, 'Galinheiro'),
        ]
        for chave_quebrado, chave_fixo, nome_predio in reparos:
            custo = CUSTO_REPARO[chave_quebrado]
            if predios.get(chave_quebrado) == chave_fixo:
                opcoes.append(OpcaoDialogo(f'{nome_predio} [consertado]',
                                           lambda dados: None, habilitado=False))
            else:
                def criar_reparo(cq=chave_quebrado, cf=chave_fixo, c=custo, n=nome_predio):
                    def reparar(dados):
                        if inv.dinheiro >= c['dinheiro'] and inv.madeira >= c['madeira']:
                            inv.dinheiro -= c['dinheiro']
                            inv.madeira  -= c['madeira']
                            predios[cq]   = cf
                            return f'{n} consertado!'
                        return f'Precisa ${c["dinheiro"]} + {c["madeira"]} madeiras'
                    return reparar
                opcoes.append(OpcaoDialogo(
                    f'Consertar {nome_predio} (${custo["dinheiro"]} + {custo["madeira"]} mad.)',
                    criar_reparo()))

        return DialogoNPC('Construtor', opcoes)

# movimentação animais

def _calc_area_animal(ret_tiles: tuple, margem: int = 6) -> pygame.Rect:
    """Converte um ret de tiles (col, lin, larg, alt) para pixels com margem interna."""
    col, lin, larg, alt = ret_tiles
    px = col * TAM_TILE + margem
    py = lin * TAM_TILE + margem
    pw = larg * TAM_TILE - margem * 2
    ph = alt  * TAM_TILE - margem * 2
    return pygame.Rect(px, py, pw, ph)


AREA_POR_TIPO = {
    'galinha': _calc_area_animal(RET_GALINHEIRO),
    'vaca':    _calc_area_animal(RET_ESTABULO),
}

TAMANHO_ANIMAL = 20   # tamanho de desenho do animal em pixels


def atualizar_animais(lista_animais: list):
    """Move cada animal dentro da sua área de confinamento."""
    for animal in lista_animais:
        tipo = animal.get('tipo', 'galinha')
        area = AREA_POR_TIPO.get(tipo)
        if not area:
            continue

        animal['x'] += animal['vx']
        animal['y'] += animal['vy']

        # Ricochete nas bordas da área
        if animal['x'] < area.x or animal['x'] > area.right  - TAMANHO_ANIMAL:
            animal['vx'] = -animal['vx']
            animal['x']  = max(area.x, min(area.right  - TAMANHO_ANIMAL, animal['x']))
        if animal['y'] < area.y or animal['y'] > area.bottom - TAMANHO_ANIMAL:
            animal['vy'] = -animal['vy']
            animal['y']  = max(area.y, min(area.bottom - TAMANHO_ANIMAL, animal['y']))

        # Pequena chance de mudar direção aleatoriamente
        if random.random() < 0.005:
            animal['vx'] = random.uniform(-1.2, 1.2)
            animal['vy'] = random.uniform(-1.2, 1.2)


def desenhar_animais(tela: pygame.Surface, lista_animais: list):
    for animal in lista_animais:
        ax   = int(animal['x'])
        ay   = int(animal['y'])
        tipo = animal.get('tipo', 'galinha')
        dir_ = animal.get('vx', 0) >= 0

        if tipo == 'vaca':
            chave = 'animal_vaca_dir' if dir_ else 'animal_vaca'
            tela.blit(RECURSOS.obter_imagem(chave, (38, 30)), (ax, ay))
        elif tipo == 'galinha':
            chave = 'animal_galinha_dir' if dir_ else 'animal_galinha'
            tela.blit(RECURSOS.obter_imagem(chave, (20, 20)), (ax, ay))
