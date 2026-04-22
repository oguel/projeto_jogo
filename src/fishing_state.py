"""
pesca_estado.py / fishing_state.py — Minigame de pesca estilo Guitar Hero.

Como funciona:
  • 4 pistas (A/S/W/D) com notas caindo de cima para baixo
  • Acertar uma nota enche a barra de captura
  • Errar ou deixar expirar diminui a barra
  • O padrão se repete em loop até: barra = 0% (escapou) ou 100% (capturado)
  • Contagem regressiva de 3 segundos antes de iniciar
"""
import pygame
import random
import math

from src.states    import EstadoBase, FONTES
from src.constants import ACOES_PESCA, LABELS_PESCA, CORES_PESCA

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Configurações do minigame
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Y_ZONA_ACERTO   = 490   # posição y da zona de acerto
MEIA_PISTA      = 28    # metade da largura de cada pista
RAIO_NOTA       = 22    # raio do círculo de cada nota
JANELA_PERFEITO = 90    # margem de ms para acerto perfeito
JANELA_BOM      = 180   # margem de ms para acerto bom
DECAIMENTO      = 4.0   # barra perde X% por segundo (passivo)
GANHO_PERFEITO  = +18.0
GANHO_BOM       = +10.0
PENALIDADE_ERRO = -10.0  # pressionou na hora errada
PENALIDADE_MISS = -15.0  # deixou a nota expirar


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Nota — representa um círculo caindo em uma pista
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class Nota:
    __slots__ = ('pista', 'tempo_acerto', 'tempo_spawn', 'estado', 'y')

    def __init__(self, pista: int, tempo_acerto: float, tempo_queda: float):
        self.pista       = pista
        self.tempo_acerto = tempo_acerto
        self.tempo_spawn  = tempo_acerto - tempo_queda
        self.estado       = 'pendente'  # pendente | perfeito | bom | expirou
        self.y            = -RAIO_NOTA


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EstadoPesca — estado principal do minigame de pesca
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class EstadoPesca(EstadoBase):
    def __init__(self, dados_jogo):
        self.gd  = dados_jogo
        self.cfg = dados_jogo.configuracao

        # Contagem regressiva de 3 segundos
        self.inicio_ms   = pygame.time.get_ticks() + 3000
        self.fase        = 'contagem'   # 'contagem' | 'jogando' | 'resultado'
        self.contagem    = 3

        # Escolhe um tipo de peixe aleatório
        tipos            = list(self.cfg.padroes_pesca.keys())
        self.tipo_peixe  = random.choice(tipos)
        self.dados_peixe = self.cfg.padroes_pesca[self.tipo_peixe]

        # Gera notas iniciais
        self.notas       = self._gerar_notas(0.0)

        # Barra de captura (0–100, começa em 50)
        self.barra       = 50.0
        self.ultima_att  = self.inicio_ms

        # Feedback visual flutuante [texto, x, y, timestamp, cor]
        self.feedback    = []

        # Resultado final
        self.resultado        = None   # None | 'capturado' | 'escapou'
        self.tempo_resultado  = 0

        # Posições x das pistas (calculadas no desenhar)
        self.x_pistas    = [200, 290, 380, 470]

    # ── Geração e reinício do padrão ─────────────────────────────
    def _gerar_notas(self, tempo_inicio: float) -> list:
        """Gera a lista de notas a partir do padrão do peixe atual."""
        bpm         = self.dados_peixe['bpm']
        ms_por_beat = 60_000 / bpm
        tempo_queda = float(self.dados_peixe['queda_ms'])
        return [
            Nota(pista, tempo_inicio + beat * ms_por_beat, tempo_queda)
            for (beat, pista) in self.dados_peixe['padrao']
        ]

    def _reiniciar_padrao(self, agora_ms: float):
        """Reinicia as notas. O jogo continua até a barra chegar a 0% ou 100%."""
        ms_por_beat = 60_000 / self.dados_peixe['bpm']
        queda       = float(self.dados_peixe['queda_ms'])
        inicio_prox = agora_ms + queda + 400
        self.notas  = [
            Nota(pista, inicio_prox + beat * ms_por_beat, queda)
            for (beat, pista) in self.dados_peixe['padrao']
        ]

    # ── Processar teclas ─────────────────────────────────────────
    def processar_eventos(self, eventos: list):
        if self.fase == 'resultado':
            for evento in eventos:
                if evento.type == pygame.KEYDOWN:
                    return self._finalizar()
            return self

        if self.fase != 'jogando':
            return self

        agora_ms = pygame.time.get_ticks() - self.inicio_ms
        teclas   = self.cfg.teclas

        for evento in eventos:
            if evento.type != pygame.KEYDOWN:
                continue
            pista = self._tecla_para_pista(evento.key, teclas)
            if pista is not None:
                self._tentar_acertar(pista, agora_ms)

        return self

    def _tecla_para_pista(self, tecla: int, mapa: dict) -> int | None:
        """Converte uma tecla pressionada para índice de pista (0–3)."""
        for i, acao in enumerate(ACOES_PESCA):
            if tecla == mapa.get(acao):
                return i
        return None

    def _tentar_acertar(self, pista: int, agora_ms: float):
        """Verifica se o jogador acertou uma nota na pista correta."""
        melhor = min(
            (n for n in self.notas if n.estado == 'pendente' and n.pista == pista),
            key=lambda n: abs(agora_ms - n.tempo_acerto),
            default=None
        )
        x_pista   = self.x_pistas[pista]
        diferenca = abs(agora_ms - melhor.tempo_acerto) if melhor else JANELA_BOM + 1

        if melhor and diferenca < JANELA_BOM:
            if diferenca < JANELA_PERFEITO:
                melhor.estado  = 'perfeito'
                self.barra    += GANHO_PERFEITO
                self._adicionar_feedback('PERFEITO!', x_pista, (100, 255, 100))
            else:
                melhor.estado  = 'bom'
                self.barra    += GANHO_BOM
                self._adicionar_feedback('BOM!', x_pista, (255, 230, 80))
        else:
            self.barra += PENALIDADE_ERRO
            self._adicionar_feedback('ERROU', x_pista, (255, 80, 80))

        self.barra = max(0.0, min(100.0, self.barra))

    def _adicionar_feedback(self, texto: str, x: int, cor: tuple):
        self.feedback.append([texto, x, Y_ZONA_ACERTO - 40, pygame.time.get_ticks(), cor])

    # ── Atualização por frame ─────────────────────────────────────
    def atualizar(self):
        agora_real = pygame.time.get_ticks()
        agora_ms   = agora_real - self.inicio_ms

        # Contagem regressiva
        if self.fase == 'contagem':
            self.contagem = max(1, math.ceil((self.inicio_ms - agora_real) / 1000))
            if agora_real >= self.inicio_ms:
                self.fase      = 'jogando'
                self.ultima_att = agora_real
            return None

        # Resultado: fecha automaticamente após 3.5s
        if self.fase == 'resultado':
            if agora_real - self.tempo_resultado > 3500:
                return self._finalizar()
            return None

        # Decaimento passivo da barra
        delta         = (agora_real - self.ultima_att) / 1000.0
        self.ultima_att = agora_real
        self.barra    = max(0.0, min(100.0, self.barra - DECAIMENTO * delta))

        # Move as notas para baixo
        queda = float(self.dados_peixe['queda_ms'])
        for nota in self.notas:
            if nota.estado != 'pendente':
                continue
            passado = agora_ms - nota.tempo_spawn
            if passado < 0:
                nota.y = -RAIO_NOTA
                continue
            nota.y = -RAIO_NOTA + (passado / queda) * (Y_ZONA_ACERTO + RAIO_NOTA)
            if agora_ms > nota.tempo_acerto + JANELA_BOM:
                nota.estado   = 'expirou'
                self.barra   += PENALIDADE_MISS
                self.barra    = max(0.0, self.barra)

        # Remove feedback velho (> 800ms)
        self.feedback = [f for f in self.feedback
                         if agora_real - f[3] < 800]

        # Verifica fim
        todas_prontas = all(n.estado != 'pendente' for n in self.notas)
        if self.barra <= 0:
            self._definir_resultado('escapou')
        elif self.barra >= 100:
            self._definir_resultado('capturado')
        elif todas_prontas:
            self._reiniciar_padrao(agora_ms)

        return None

    def _definir_resultado(self, resultado: str):
        if self.resultado is None:
            self.resultado       = resultado
            self.fase            = 'resultado'
            self.tempo_resultado = pygame.time.get_ticks()

    def _finalizar(self):
        """Fecha o minigame e volta ao mapa."""
        if self.resultado == 'capturado':
            id_item  = self.dados_peixe.get('item_recompensa', 'peixe_comum')
            qtd      = self.dados_peixe.get('qtd_recompensa', 1)
            self.gd.inventario.adicionar(id_item, qtd)
        self.gd.ultimo_resultado = self.resultado

        if self.gd.ultimo_mapa == 'fazenda':
            from src.farm_state import EstadoFazenda
            return EstadoFazenda(self.gd)
        from src.town_state import EstadoCidade
        return EstadoCidade(self.gd)

    # ── Desenho ──────────────────────────────────────────────────
    def desenhar(self, tela: pygame.Surface):
        largura, altura = tela.get_size()

        # Calcula posições x das 4 pistas
        total_larg    = 4 * 80
        inicio_pistas = largura // 2 - total_larg // 2 + 40
        self.x_pistas = [inicio_pistas + i * 80 for i in range(4)]

        # Fundo gradiente azul-escuro
        for linha_y in range(altura):
            p = linha_y / altura
            pygame.draw.line(tela,
                (int(8 + p * 18), int(8 + p * 18), int(25 + p * 50)),
                (0, linha_y), (largura, linha_y))

        fonte_g = FONTES.get('grande', pygame.font.SysFont('arial', 28, bold=True))
        fonte_n = FONTES.get('normal', pygame.font.SysFont('arial', 18))
        fonte_p = FONTES.get('pequena', pygame.font.SysFont('arial', 14))

        # ── Contagem regressiva ──────────────────────────────────
        if self.fase == 'contagem':
            pulso   = 1.0 + 0.3 * math.sin(pygame.time.get_ticks() * 0.01)
            tam     = int(80 * pulso)
            fonte_c = pygame.font.SysFont('arial', tam, bold=True)
            num     = fonte_c.render(str(self.contagem), True, self.dados_peixe['cor'])
            tela.blit(num, (largura // 2 - num.get_width() // 2,
                             altura  // 2 - num.get_height() // 2))
            nome = fonte_g.render(f'🎣  {self.dados_peixe["nome"]}!', True, self.dados_peixe['cor'])
            tela.blit(nome, (largura // 2 - nome.get_width() // 2, 28))
            return

        # Nome do peixe
        nome = fonte_g.render(f'🎣  {self.dados_peixe["nome"]}', True, self.dados_peixe['cor'])
        tela.blit(nome, (largura // 2 - nome.get_width() // 2, 8))

        # Barra de captura
        self._desenhar_barra(tela, largura, fonte_p)

        # Pistas e zonas de acerto
        for i in range(4):
            x_pista = self.x_pistas[i]
            cor     = CORES_PESCA[i]

            # Faixa semitransparente
            faixa = pygame.Surface((MEIA_PISTA * 2, altura), pygame.SRCALPHA)
            faixa.fill((*cor, 18))
            tela.blit(faixa, (x_pista - MEIA_PISTA, 0))
            pygame.draw.line(tela, (*cor, 70),
                             (x_pista - MEIA_PISTA, 0), (x_pista - MEIA_PISTA, altura), 1)
            pygame.draw.line(tela, (*cor, 70),
                             (x_pista + MEIA_PISTA, 0), (x_pista + MEIA_PISTA, altura), 1)

            # Zona de acerto
            pygame.draw.circle(tela, (*cor, 60), (x_pista, Y_ZONA_ACERTO), RAIO_NOTA + 10)
            pygame.draw.circle(tela, cor,         (x_pista, Y_ZONA_ACERTO), RAIO_NOTA + 10, 3)

            # Tecla correspondente
            rotulo = fonte_p.render(LABELS_PESCA[i], True, cor)
            tela.blit(rotulo, (x_pista - rotulo.get_width() // 2, Y_ZONA_ACERTO + RAIO_NOTA + 14))

        # Notas descendo
        for nota in self.notas:
            if nota.estado == 'pendente' and -RAIO_NOTA <= nota.y <= Y_ZONA_ACERTO + 60:
                x_pista = self.x_pistas[nota.pista]
                cor     = CORES_PESCA[nota.pista]
                pygame.draw.circle(tela, (0,0,0,60), (x_pista+3, int(nota.y)+3), RAIO_NOTA)
                pygame.draw.circle(tela, cor,         (x_pista,   int(nota.y)),   RAIO_NOTA)
                pygame.draw.circle(tela, (255,255,255),(x_pista,   int(nota.y)),   RAIO_NOTA, 2)
            elif nota.estado in ('perfeito', 'bom'):
                x_pista    = self.x_pistas[nota.pista]
                cor_acerto = (100, 255, 100) if nota.estado == 'perfeito' else (255, 230, 80)
                pygame.draw.circle(tela, cor_acerto, (x_pista, Y_ZONA_ACERTO), RAIO_NOTA + 12, 3)

        # Feedback visual flutuante
        for (texto, fx, fy, nasceu, cor) in self.feedback:
            idade  = pygame.time.get_ticks() - nasceu
            alfa   = max(0, 255 - int(idade / 800 * 255))
            subida = int(idade / 800 * 28)
            surf   = fonte_g.render(texto, True, cor)
            surf.set_alpha(alfa)
            tela.blit(surf, (fx - surf.get_width() // 2, fy - subida))

        # Dica de meta
        dica = fonte_p.render('Encha a barra para capturar o peixe!', True, (180, 180, 255))
        tela.blit(dica, (largura - dica.get_width() - 10, 60))

        # Tela de resultado
        if self.fase == 'resultado':
            capturou = self.resultado == 'capturado'
            cor_res  = (80, 255, 120) if capturou else (255, 80, 80)
            msg_res  = '🐟 PEIXE CAPTURADO!' if capturou else '💨 O peixe escapou...'
            surf_res = pygame.font.SysFont('arial', 42, bold=True).render(msg_res, True, cor_res)
            brilho   = pygame.Surface((surf_res.get_width() + 40, surf_res.get_height() + 20), pygame.SRCALPHA)
            brilho.fill((*cor_res, 35))
            tela.blit(brilho,  (largura // 2 - brilho.get_width()   // 2, altura // 2 - brilho.get_height()   // 2))
            tela.blit(surf_res,(largura // 2 - surf_res.get_width() // 2, altura // 2 - surf_res.get_height() // 2))
            confirmar = fonte_n.render('Pressione qualquer tecla para continuar', True, (180, 180, 180))
            tela.blit(confirmar, (largura // 2 - confirmar.get_width() // 2, altura // 2 + 54))

    def _desenhar_barra(self, tela: pygame.Surface, largura: int, fonte):
        """Desenha a barra de captura no topo da tela."""
        larg_barra, alt_barra = 400, 24
        x_barra = largura // 2 - larg_barra // 2
        y_barra = 56

        # Fundo
        pygame.draw.rect(tela, (55, 55, 80), (x_barra-2, y_barra-2, larg_barra+4, alt_barra+4), border_radius=6)
        pygame.draw.rect(tela, (25, 25, 48), (x_barra,   y_barra,   larg_barra,   alt_barra),   border_radius=5)

        # Preenchimento
        preench = int(larg_barra * self.barra / 100)
        if preench > 0:
            if self.barra > 60:    cor_barra = (80, 210, 80)
            elif self.barra > 30:  cor_barra = (255, 200, 50)
            else:                   cor_barra = (255, 80, 80)
            pygame.draw.rect(tela, cor_barra, (x_barra, y_barra, preench, alt_barra), border_radius=5)

        # Texto
        texto_barra = fonte.render(f'Força: {int(self.barra)}%', True, (230, 230, 230))
        tela.blit(texto_barra, (x_barra + larg_barra // 2 - texto_barra.get_width() // 2, y_barra + 3))

        # Marcador de 50%
        pygame.draw.line(tela, (255, 255, 255, 80),
                         (x_barra + larg_barra // 2, y_barra),
                         (x_barra + larg_barra // 2, y_barra + alt_barra), 1)
