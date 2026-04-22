"""
estados.py / states.py — Tela de título, introdução, seleção de personagem e desmaio.
"""
import pygame
import math

from src.constants import SPAWN_X, SPAWN_Y

# Dicionário global de fontes — inicializado em jogo.py
FONTES: dict = {}


def inicializar_fontes():
    """Carrega e armazena as fontes do jogo na memória."""
    global FONTES
    FONTES = {
        'titulo':  pygame.font.SysFont('arial', 56, bold=True),
        'grande':  pygame.font.SysFont('arial', 32, bold=True),
        'normal':  pygame.font.SysFont('arial', 20),
        'pequena': pygame.font.SysFont('arial', 14),
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EstadoBase — todos os estados herdam daqui
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class EstadoBase:
    def processar_eventos(self, eventos: list) -> 'EstadoBase':
        return self

    def atualizar(self) -> 'EstadoBase | None':
        return None

    def desenhar(self, tela: pygame.Surface):
        pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EstadoTitulo — animação noturna com estrelas e lua
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class EstadoTitulo(EstadoBase):
    def __init__(self, dados_jogo):
        self.gd      = dados_jogo
        self.tick    = 0
        self.estrelas = [(x % 800, (x * 7) % 600) for x in range(0, 20_000, 137)]

    def processar_eventos(self, eventos):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return EstadoIntro(self.gd)
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                return EstadoIntro(self.gd)
        return self

    def desenhar(self, tela: pygame.Surface):
        self.tick += 1
        largura, altura = tela.get_size()

        # Fundo: gradiente de céu noturno
        for linha_y in range(altura):
            p = linha_y / altura
            pygame.draw.line(tela,
                (int(5 + p * 15), int(8 + p * 20), int(35 + p * 40)),
                (0, linha_y), (largura, linha_y))

        # Estrelas cintilando
        for i, (ex, ey) in enumerate(self.estrelas):
            piscar = math.sin(self.tick * 0.04 + i * 0.31)
            alfa   = max(0, min(255, int(100 + piscar * 155)))
            tam    = 1 + (i % 3 == 0)
            s      = pygame.Surface((tam * 2 + 1, tam * 2 + 1), pygame.SRCALPHA)
            s.fill((0, 0, 0, 0))
            pygame.draw.circle(s, (255, 255, 255), (tam, tam), tam)
            s.set_alpha(alfa)
            tela.blit(s, (ex - tam, ey - tam))

        # Lua flutuando
        lua_y = int(70 + 12 * math.sin(self.tick * 0.008))
        pygame.draw.circle(tela, (238, 238, 180), (largura - 120, lua_y), 38)
        pygame.draw.circle(tela, (8, 18, 55),     (largura - 108, lua_y - 6), 30)

        # Árvores silhueta
        for tx in [40, 110, 190, 560, 660, 740]:
            pygame.draw.rect(tela, (8, 40, 8), (tx, altura - 160, 18, 65))
            pygame.draw.polygon(tela, (10, 55, 10), [
                (tx+9, altura-205), (tx-22, altura-140), (tx+40, altura-140)])

        # Casa silhueta
        cx = largura // 2
        pygame.draw.rect(tela, (70, 35, 18), (cx-60, altura-160, 120, 65))
        pygame.draw.polygon(tela, (110, 25, 25), [
            (cx-70, altura-160), (cx, altura-210), (cx+70, altura-160)])
        brilho = int(200 + 55 * math.sin(self.tick * 0.025))
        pygame.draw.rect(tela, (brilho, brilho, 40), (cx-50, altura-148, 22, 22))
        pygame.draw.rect(tela, (brilho, brilho, 40), (cx+28, altura-148, 22, 22))

        # Grama
        pygame.draw.rect(tela, (12, 75, 18), (0, altura - 100, largura, 100))

        # Título
        fonte_t  = FONTES.get('titulo', pygame.font.SysFont('arial', 56, bold=True))
        sombra   = fonte_t.render('FAZENDA', True, (100, 80, 0))
        titulo   = fonte_t.render('FAZENDA', True, (255, 230, 80))
        larg_t   = titulo.get_width()
        tela.blit(sombra, (largura // 2 - larg_t // 2 + 3, 83))
        tela.blit(titulo, (largura // 2 - larg_t // 2, 80))

        fonte_g  = FONTES.get('grande', pygame.font.SysFont('arial', 32, bold=True))
        subtitulo = fonte_g.render('Vida no Campo', True, (160, 240, 160))
        tela.blit(subtitulo, (largura // 2 - subtitulo.get_width() // 2, 155))

        pulso   = int(255 * (0.65 + 0.35 * math.sin(self.tick * 0.07)))
        fonte_n = FONTES.get('normal', pygame.font.SysFont('arial', 20))
        botao   = fonte_n.render('Pressione ENTER  ou  clique para começar', True, (pulso, pulso, pulso))
        tela.blit(botao, (largura // 2 - botao.get_width() // 2, altura - 70))

        fonte_p = FONTES.get('pequena', pygame.font.SysFont('arial', 14))
        versao  = fonte_p.render('v0.4  •  ESC = Configurações', True, (70, 70, 70))
        tela.blit(versao, (8, altura - 22))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EstadoIntro — slides de história
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class EstadoIntro(EstadoBase):
    SLIDES = [
        "Uma antiga fazenda está sendo leiloada...",
        "Você decide participar do leilão...",
        "Você venceu o leilão!",
        "A fazenda agora é sua!",
        "Boa sorte, fazendeiro!",
    ]

    def __init__(self, dados_jogo):
        self.gd        = dados_jogo
        self.slide_idx = 0

    def processar_eventos(self, eventos):
        for evento in eventos:
            avancar = (evento.type == pygame.KEYDOWN and evento.key == pygame.K_RETURN) \
                      or evento.type == pygame.MOUSEBUTTONDOWN
            if avancar:
                self.slide_idx += 1
                if self.slide_idx >= len(self.SLIDES):
                    return EstadoSelecao(self.gd)
        return self

    def desenhar(self, tela: pygame.Surface):
        largura, altura = tela.get_size()
        for linha_y in range(altura):
            p = linha_y / altura
            pygame.draw.line(tela,
                (int(8 + p * 18), int(8 + p * 10), int(22 + p * 28)),
                (0, linha_y), (largura, linha_y))

        fonte_g = FONTES.get('grande', pygame.font.SysFont('arial', 30, bold=True))
        texto   = fonte_g.render(self.SLIDES[self.slide_idx], True, (220, 215, 170))
        tela.blit(texto, (largura // 2 - texto.get_width() // 2, altura // 2 - 20))

        fonte_p = FONTES.get('pequena', pygame.font.SysFont('arial', 14))
        dica    = fonte_p.render(
            f'({self.slide_idx+1}/{len(self.SLIDES)})  ENTER ou clique para continuar',
            True, (100, 100, 100))
        tela.blit(dica, (largura // 2 - dica.get_width() // 2, altura // 2 + 38))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EstadoSelecao — escolha de personagem (homem ou mulher)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class EstadoSelecao(EstadoBase):
    def __init__(self, dados_jogo):
        self.gd      = dados_jogo
        self.escolha = 0   # 0 = homem, 1 = mulher
        self.tick    = 0

    def processar_eventos(self, eventos):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key in (pygame.K_LEFT, pygame.K_a):   self.escolha = 0
                if evento.key in (pygame.K_RIGHT, pygame.K_d):  self.escolha = 1
                if evento.key == pygame.K_RETURN:
                    return self._confirmar()
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                mx, my       = evento.pos
                larg, alt    = pygame.display.get_surface().get_size()
                if larg // 2 - 140 <= mx <= larg // 2 - 10 and 140 <= my <= 330:
                    self.escolha = 0
                    return self._confirmar()
                if larg // 2 + 10 <= mx <= larg // 2 + 140 and 140 <= my <= 330:
                    self.escolha = 1
                    return self._confirmar()
        return self

    def _confirmar(self):
        """Cria o jogador e vai para a fazenda."""
        from src.entities import Jogador
        jogador     = Jogador(self.escolha)
        jogador.x   = float(SPAWN_X)
        jogador.y   = float(SPAWN_Y)
        self.gd.jogador = jogador
        from src.farm_state import EstadoFazenda
        return EstadoFazenda(self.gd)

    def desenhar(self, tela: pygame.Surface):
        self.tick += 1
        largura, altura = tela.get_size()
        tela.fill((22, 22, 44))

        fonte_g  = FONTES.get('grande', pygame.font.SysFont('arial', 28, bold=True))
        fonte_n  = FONTES.get('normal', pygame.font.SysFont('arial', 18))

        titulo = fonte_g.render('Escolha seu personagem', True, (255, 240, 170))
        tela.blit(titulo, (largura // 2 - titulo.get_width() // 2, 50))

        dica = fonte_n.render('← → ou clique  •  ENTER ou clique para confirmar', True, (120, 120, 120))
        tela.blit(dica, (largura // 2 - dica.get_width() // 2, 100))

        personagens = [
            (0, 'Homem',  (0, 100, 255),   largura // 2 - 130),
            (1, 'Mulher', (255, 100, 200), largura // 2 + 10),
        ]
        mx, my = pygame.mouse.get_pos()

        for (genero, nome, cor, pos_x) in personagens:
            selecionado = self.escolha == genero
            hover       = pos_x <= mx <= pos_x + 120 and 140 <= my <= 330
            cor_borda   = (120, 200, 255) if selecionado else (80, 80, 130) if hover else (50, 50, 90)
            alfa_fundo  = 100 if selecionado else 50

            caixa = pygame.Surface((120, 180), pygame.SRCALPHA)
            caixa.fill((*cor[:3], alfa_fundo))
            pygame.draw.rect(caixa, cor_borda, caixa.get_rect(), 3, border_radius=12)
            tela.blit(caixa, (pos_x, 140))

            from src.entities import Jogador
            temp   = Jogador(genero)
            temp.x = pos_x + 28
            temp.y = 152
            temp.desenhar(tela)

            rotulo = fonte_n.render(nome, True, (255,255,255) if selecionado else (130,130,130))
            tela.blit(rotulo, (pos_x + 60 - rotulo.get_width() // 2, 330))

            if selecionado:
                seta   = fonte_g.render('▲', True, (255, 240, 100))
                quique = int(math.sin(self.tick * 0.1) * 4)
                tela.blit(seta, (pos_x + 60 - seta.get_width() // 2, 354 + quique))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EstadoDesmaio — tela de desmaio (meia-noite) ou dormir
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class EstadoDesmaio(EstadoBase):
    def __init__(self, dados_jogo):
        self.gd    = dados_jogo
        self.timer = pygame.time.get_ticks()
        self.fase  = 0   # 0 = fade para preto, 1 = aguardando e mostrando mensagem
        self.alfa  = 0

    def atualizar(self):
        tempo = pygame.time.get_ticks() - self.timer

        if self.fase == 0:
            self.alfa = min(255, tempo // 8)
            if tempo > 2200:
                self.fase = 1

        elif self.fase == 1 and tempo > 5000:
            # Reinicia o dia e volta o jogador para a casa
            self.gd.horario.reiniciar_dia()
            self.gd.dormiu_voluntario = False
            jogador = self.gd.jogador
            if jogador:
                jogador.x       = float(SPAWN_X)
                jogador.y       = float(SPAWN_Y)
                jogador.pescando = False
                jogador.direcao  = 'baixo'
            from src.farm_state import EstadoFazenda
            return EstadoFazenda(self.gd)

        return None

    def desenhar(self, tela: pygame.Surface):
        largura, altura = tela.get_size()
        tela.fill((0, 0, 0))

        if self.fase >= 1:
            fonte_g = FONTES.get('grande', pygame.font.SysFont('arial', 28, bold=True))
            fonte_n = FONTES.get('normal', pygame.font.SysFont('arial', 18))
            dormiu  = getattr(self.gd, 'dormiu_voluntario', False)

            if dormiu:
                linha1 = fonte_g.render('Descansando... 🛏️', True, (180, 220, 180))
                linha2 = fonte_n.render('Você acorda em casa renovado no dia seguinte.', True, (130, 175, 130))
            else:
                linha1 = fonte_g.render('Você desmaiou de cansaço...', True, (200, 170, 80))
                linha2 = fonte_n.render('Você acorda em casa no dia seguinte.', True, (140, 140, 140))

            tela.blit(linha1, (largura // 2 - linha1.get_width() // 2, altura // 2 - 30))
            tela.blit(linha2, (largura // 2 - linha2.get_width() // 2, altura // 2 + 20))

        if self.fase == 0:
            escuridao = pygame.Surface((largura, altura))
            escuridao.fill((0, 0, 0))
            escuridao.set_alpha(self.alfa)
            tela.blit(escuridao, (0, 0))
