import pygame
import math

from src.constants import SPAWN_X, SPAWN_Y

# Dicionario global de fontes - inicializado em jogo.py
FONTES: dict = {}


def inicializar_fontes():
    global FONTES
    FONTES = {
        'titulo':  pygame.font.SysFont('arial', 56, bold=True),
        'grande':  pygame.font.SysFont('arial', 32, bold=True),
        'normal':  pygame.font.SysFont('arial', 20),
        'pequena': pygame.font.SysFont('arial', 14),
    }


class EstadoBase:
    def processar_eventos(self, eventos: list) -> 'EstadoBase':
        return self

    def atualizar(self) -> 'EstadoBase | None':
        return None

    def desenhar(self, tela: pygame.Surface):
        pass


class EstadoTitulo(EstadoBase):
    def __init__(self, dados_jogo):
        self.gd      = dados_jogo

    def processar_eventos(self, eventos):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                    from src.assets import tocar_som
                    tocar_som('tecla', self.gd.configuracao.volumes)
                    return EstadoIntro(self.gd)
                elif evento.key == pygame.K_ESCAPE:
                    from src.assets import tocar_som
                    tocar_som('tecla', self.gd.configuracao.volumes)
                    from src.settings_state import EstadoConfiguracoes
                    return EstadoConfiguracoes(self.gd, self)
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                from src.assets import tocar_som
                tocar_som('tecla', self.gd.configuracao.volumes)
                return EstadoIntro(self.gd)
        return self

    def desenhar(self, tela: pygame.Surface):
        largura, altura = tela.get_size()

        from src.assets import obter_imagem
        img = obter_imagem('titlescreen', (largura, altura))
        tela.blit(img, (0, 0))

        fonte_p = FONTES.get('pequena', pygame.font.SysFont('arial', 14))
        versao  = fonte_p.render('v0.4  |  ESC = Configuracoes', True, (220, 220, 220))
        tela.blit(versao, (8, altura - 22))


class EstadoIntro(EstadoBase):
    SLIDES = [
        'Uma antiga fazenda esta sendo leiloada...',
        'Voce decide participar do leilao...',
        'Voce venceu o leilao!',
        'A fazenda agora e sua!',
        'Boa sorte, fazendeiro!',
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
                    return self._iniciar_jogo()
        return self

    def _iniciar_jogo(self):
        from src.entities import Jogador
        jogador   = Jogador()
        jogador.x = float(SPAWN_X)
        jogador.y = float(SPAWN_Y)
        self.gd.jogador = jogador
        from src.farm_state import EstadoFazenda
        return EstadoFazenda(self.gd)

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


# EstadoDesmaio - tela de desmaio (meia-noite) ou dormir

class EstadoDesmaio(EstadoBase):
    def __init__(self, dados_jogo):
        self.gd    = dados_jogo
        self.timer = pygame.time.get_ticks()
        self.fase  = 0   # 0 = fade para preto, 1 = mostrando mensagem
        self.alfa  = 0

    def atualizar(self):
        tempo = pygame.time.get_ticks() - self.timer

        if self.fase == 0:
            self.alfa = min(255, tempo // 8)
            if tempo > 2200:
                self.fase = 1

        elif self.fase == 1 and tempo > 5000:
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
                linha1 = fonte_g.render('Descansando...', True, (180, 220, 180))
                linha2 = fonte_n.render('Voce acorda em casa renovado no dia seguinte.', True, (130, 175, 130))
            else:
                linha1 = fonte_g.render('Voce desmaiou de cansaco...', True, (200, 170, 80))
                linha2 = fonte_n.render('Voce acorda em casa no dia seguinte.', True, (140, 140, 140))

            tela.blit(linha1, (largura // 2 - linha1.get_width() // 2, altura // 2 - 30))
            tela.blit(linha2, (largura // 2 - linha2.get_width() // 2, altura // 2 + 20))

        if self.fase == 0:
            escuridao = pygame.Surface((largura, altura))
            escuridao.fill((0, 0, 0))
            escuridao.set_alpha(self.alfa)
            tela.blit(escuridao, (0, 0))
