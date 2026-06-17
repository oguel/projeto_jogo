import pygame
import math

from src.states    import EstadoBase, FONTES
from src.constants import ACOES_PESCA, LABELS_PESCA, CORES_PESCA
from src import assets as RECURSOS

# Configuracoes
Y_ZONA_ACERTO   = 490
MEIA_PISTA      = 28
RAIO_NOTA       = 22
JANELA_PERFEITO = 60    
JANELA_BOM      = 120   
GANHO_PERFEITO  = +8.0  
GANHO_BOM       = +4.0
PENALIDADE_ERRO = -14.0  
PENALIDADE_MISS = -22.0 
MAX_LOOPS       = 3


# Nota
class Nota:
    __slots__ = ('pista', 'tempo_acerto', 'tempo_spawn', 'estado', 'y')

    def __init__(self, pista: int, tempo_acerto: float, tempo_queda: float):
        self.pista        = pista
        self.tempo_acerto = tempo_acerto
        self.tempo_spawn  = tempo_acerto - tempo_queda
        self.estado       = 'pendente'   # pendente | perfeito | bom | expirou
        self.y            = -RAIO_NOTA


# -------------------------------------------------------------
# EstadoPesca
# -------------------------------------------------------------
class EstadoPesca(EstadoBase):
    def __init__(self, dados_jogo):
        self.gd  = dados_jogo
        self.cfg = dados_jogo.configuracao

        # Contagem regressiva de 3 s
        self.inicio_ms  = pygame.time.get_ticks() + 3000
        self.fase       = 'contagem'   # contagem | jogando | resultado
        self.contagem   = 3

        # Escolhe peixe
        import random
        tipos            = list(self.cfg.padroes_pesca.keys())
        self.tipo_peixe  = random.choice(tipos)
        self.dados_peixe = self.cfg.padroes_pesca[self.tipo_peixe]

        # Notas e barra
        self.notas      = self._gerar_notas(0.0)
        self.barra      = 20.0      # começa em 20%
        self._loops     = 0
        self._combo     = 0
        self._tick      = 0

        # Feedback flutuante: [texto, x, y, timestamp, cor]
        self.feedback: list = []

        # Resultado
        self.resultado       = None
        self.tempo_resultado = 0

        # Posicoes x das pistas (definidas no desenhar)
        self.x_pistas = [200, 290, 380, 470]

    # -- Geracao de notas -----------------------------------------
    def _gerar_notas(self, tempo_inicio: float) -> list:
        bpm         = self.dados_peixe['bpm']
        ms_por_beat = 60_000 / bpm
        queda       = float(self.dados_peixe['queda_ms'])
        offset      = queda   # primeira nota começa a cair ao iniciar
        return [
            Nota(pista, tempo_inicio + offset + beat * ms_por_beat, queda)
            for (beat, pista) in self.dados_peixe['padrao']
        ]

    def _reiniciar_padrao(self, agora_ms: float):
        self._loops += 1
        if self._loops >= MAX_LOOPS:
            self._definir_resultado('escapou')
            return
        queda       = float(self.dados_peixe['queda_ms'])
        ms_por_beat = 60_000 / self.dados_peixe['bpm']
        inicio_prox = agora_ms + queda + 400
        self.notas  = [
            Nota(pista, inicio_prox + beat * ms_por_beat, queda)
            for (beat, pista) in self.dados_peixe['padrao']
        ]

    # -- Eventos --------------------------------------------------
    def processar_eventos(self, eventos: list):
        if self.fase == 'resultado':
            for evento in eventos:
                if evento.type == pygame.KEYDOWN:
                    RECURSOS.tocar_som('tecla', self.cfg.volumes)
                    return self._finalizar()
            return self

        if self.fase != 'jogando':
            return self

        agora_ms = pygame.time.get_ticks() - self.inicio_ms
        for evento in eventos:
            if evento.type != pygame.KEYDOWN:
                continue
            pista = self._tecla_para_pista(evento.key, self.cfg.teclas)
            if pista is not None:
                RECURSOS.tocar_som('tecla', self.cfg.volumes)
                self._tentar_acertar(pista, agora_ms)
        return self

    def _tecla_para_pista(self, tecla: int, mapa: dict) -> int | None:
        for i, acao in enumerate(ACOES_PESCA):
            if tecla == mapa.get(acao):
                return i
        return None

    def _tentar_acertar(self, pista: int, agora_ms: float):
        melhor = min(
            (n for n in self.notas if n.estado == 'pendente' and n.pista == pista),
            key=lambda n: abs(agora_ms - n.tempo_acerto),
            default=None,
        )
        diferenca = abs(agora_ms - melhor.tempo_acerto) if melhor else JANELA_BOM + 1
        x_pista   = self.x_pistas[pista]

        if melhor and diferenca < JANELA_BOM:
            if diferenca < JANELA_PERFEITO:
                self._combo  += 1
                multi         = min(3.0, 1.0 + (self._combo - 1) * 0.5)
                self.barra   += GANHO_PERFEITO * multi
                melhor.estado = 'perfeito'
                label = f'PERFEITO! x{multi:.1f}' if multi > 1 else 'PERFEITO!'
                self._fb(label, x_pista, (100, 255, 100))
            else:
                self._combo   = 0
                self.barra   += GANHO_BOM
                melhor.estado = 'bom'
                self._fb('BOM!', x_pista, (255, 230, 80))
        else:
            # Erro: apertou na hora errada ou pista errada
            self._combo  = 0
            self.barra  += PENALIDADE_ERRO
            self._fb('ERROU!', x_pista, (255, 60, 60))

        self.barra = max(0.0, min(100.0, self.barra))

    def _fb(self, texto: str, x: int, cor: tuple):
        self.feedback.append([texto, x, Y_ZONA_ACERTO - 50, pygame.time.get_ticks(), cor])

    # -- Atualizacao ----------------------------------------------
    def atualizar(self):
        agora_real = pygame.time.get_ticks()
        agora_ms   = agora_real - self.inicio_ms

        # Contagem regressiva
        if self.fase == 'contagem':
            self.contagem = max(1, math.ceil((self.inicio_ms - agora_real) / 1000))
            if agora_real >= self.inicio_ms:
                self.fase = 'jogando'
            return None

        # Aguarda tecla no resultado
        if self.fase == 'resultado':
            if agora_real - self.tempo_resultado > 3500:
                return self._finalizar()
            return None

        # -- Move notas --
        queda = float(self.dados_peixe['queda_ms'])
        for nota in self.notas:
            if nota.estado != 'pendente':
                continue
            passado = agora_ms - nota.tempo_spawn
            if passado < 0:
                nota.y = -RAIO_NOTA
                continue
            nota.y = -RAIO_NOTA + (passado / queda) * (Y_ZONA_ACERTO + RAIO_NOTA)

            # Miss: nota passou da zona de acerto sem ser pressionada
            if agora_ms > nota.tempo_acerto + JANELA_BOM:
                nota.estado  = 'expirou'
                self._combo  = 0
                self.barra  += PENALIDADE_MISS
                self.barra   = max(0.0, self.barra)

        # -- Remove feedback velho --
        self._tick += 1
        self.feedback = [f for f in self.feedback
                         if agora_real - f[3] < 900]

        # -- Verifica condicoes de fim --
        if self.barra >= 100:
            self._definir_resultado('capturado')
        elif self.barra <= 0:
            self._definir_resultado('escapou')
        elif all(n.estado != 'pendente' for n in self.notas):
            self._reiniciar_padrao(agora_ms)

        return None

    def _definir_resultado(self, resultado: str):
        if self.resultado is None:
            self.resultado       = resultado
            self.fase            = 'resultado'
            self.tempo_resultado = pygame.time.get_ticks()

    def _finalizar(self):
        if self.resultado == 'capturado':
            id_item = self.dados_peixe.get('item_recompensa', 'peixe_comum')
            qtd     = self.dados_peixe.get('qtd_recompensa', 1)
            self.gd.inventario.adicionar(id_item, qtd)
        self.gd.ultimo_resultado = self.resultado
        if self.gd.ultimo_mapa == 'fazenda':
            from src.farm_state import EstadoFazenda
            return EstadoFazenda(self.gd)
        from src.town_state import EstadoCidade
        return EstadoCidade(self.gd)

    # -- Desenho --------------------------------------------------
    def desenhar(self, tela: pygame.Surface):
        largura, altura = tela.get_size()

        # Posicoes x das pistas
        total_larg    = 4 * 80
        inicio_pistas = largura // 2 - total_larg // 2 + 40
        self.x_pistas = [inicio_pistas + i * 80 for i in range(4)]

        # Fundo gradiente escuro
        for y in range(altura):
            p = y / altura
            b = int(22 + p * 55)
            pygame.draw.line(tela, (6, 6, b), (0, y), (largura, y))

        fonte_g = FONTES.get('grande', pygame.font.SysFont('arial', 28, bold=True))
        fonte_n = FONTES.get('normal', pygame.font.SysFont('arial', 18))
        fonte_p = FONTES.get('pequena', pygame.font.SysFont('arial', 14))

        # -- Contagem regressiva ----------------------------------
        if self.fase == 'contagem':
            pulso   = 1.0 + 0.3 * math.sin(pygame.time.get_ticks() * 0.01)
            tam     = int(80 * pulso)
            fonte_c = pygame.font.SysFont('arial', tam, bold=True)
            num     = fonte_c.render(str(self.contagem), True, self.dados_peixe['cor'])
            tela.blit(num, (largura // 2 - num.get_width() // 2,
                             altura  // 2 - num.get_height() // 2))
            nome = fonte_g.render(f'{self.dados_peixe["nome"]}!', True, self.dados_peixe['cor'])
            tela.blit(nome, (largura // 2 - nome.get_width() // 2, 28))
            return

        # Nome do peixe
        nome = fonte_g.render(self.dados_peixe['nome'], True, self.dados_peixe['cor'])
        tela.blit(nome, (largura // 2 - nome.get_width() // 2, 8))

        # Barra de captura
        self._desenhar_barra(tela, largura, fonte_p)

        # Combo
        if self._combo >= 2:
            cor_c = (255, 255, 80) if self._combo < 4 else (255, 140, 30)
            multi = min(3.0, 1.0 + (self._combo - 1) * 0.5)
            tc    = fonte_n.render(f'COMBO x{self._combo}  ({multi:.1f}x)', True, cor_c)
            tela.blit(tc, (largura - tc.get_width() - 10, 10))

        # -- Pistas ----------------------------------------------
        for i in range(4):
            x_pista = self.x_pistas[i]
            cor     = CORES_PESCA[i]

            # Faixa semi-transparente
            faixa = pygame.Surface((MEIA_PISTA * 2, altura), pygame.SRCALPHA)
            faixa.fill((*cor, 14))
            tela.blit(faixa, (x_pista - MEIA_PISTA, 0))

            # Bordas
            cor_dim = tuple(max(0, c // 3) for c in cor)
            pygame.draw.line(tela, cor_dim,
                             (x_pista - MEIA_PISTA, 0), (x_pista - MEIA_PISTA, altura))
            pygame.draw.line(tela, cor_dim,
                             (x_pista + MEIA_PISTA, 0), (x_pista + MEIA_PISTA, altura))

            # Zona de acerto (circulo pulsante)
            pulso_z = 1.0 + 0.06 * math.sin(self._tick * 0.2 + i)
            raio_z  = int((RAIO_NOTA + 10) * pulso_z)
            pygame.draw.circle(tela, cor, (x_pista, Y_ZONA_ACERTO), raio_z, 3)
            pygame.draw.circle(tela, (200, 200, 200), (x_pista, Y_ZONA_ACERTO), raio_z, 1)

            # Tecla
            rotulo = fonte_n.render(LABELS_PESCA[i], True, cor)
            ty     = Y_ZONA_ACERTO + RAIO_NOTA + 16
            tela.blit(rotulo, (x_pista - rotulo.get_width() // 2, ty))

        # -- Notas ------------------------------------------------
        for nota in self.notas:
            x_pista = self.x_pistas[nota.pista]
            cor     = CORES_PESCA[nota.pista]
            if nota.estado == 'pendente' and -RAIO_NOTA <= nota.y <= Y_ZONA_ACERTO + 60:
                ny = int(nota.y)
                pygame.draw.circle(tela, (0, 0, 0),   (x_pista + 2, ny + 2), RAIO_NOTA)
                pygame.draw.circle(tela, cor,          (x_pista,     ny),     RAIO_NOTA)
                pygame.draw.circle(tela, (255,255,255),(x_pista,     ny),     RAIO_NOTA, 2)
            elif nota.estado in ('perfeito', 'bom'):
                cor_a = (100, 255, 100) if nota.estado == 'perfeito' else (255, 230, 80)
                pygame.draw.circle(tela, cor_a, (x_pista, Y_ZONA_ACERTO), RAIO_NOTA + 14, 3)

        # -- Feedback flutuante -----------------------------------
        agora_real = pygame.time.get_ticks()
        for (texto, fx, fy, nasceu, cor) in self.feedback:
            idade  = agora_real - nasceu
            alfa   = max(0, 255 - int(idade / 900 * 255))
            subida = int(idade / 900 * 38)
            surf   = fonte_g.render(texto, True, cor)
            surf.set_alpha(alfa)
            tela.blit(surf, (fx - surf.get_width() // 2, fy - subida))

        # Tentativas restantes
        loops_rest = MAX_LOOPS - self._loops
        if loops_rest <= 1:
            pisca     = int(255 * abs(math.sin(self._tick * 0.15)))
            cor_alert = (pisca, 40, 40)
        else:
            cor_alert = (160, 160, 220)
        dica = fonte_p.render(
            f'Tentativas: {loops_rest}/{MAX_LOOPS}  |  Encha a barra!', True, cor_alert)
        tela.blit(dica, (largura - dica.get_width() - 10, 60))

        # Dica sobre a regra da barra
        dica2 = fonte_p.render('Barra so diminui ao errar!', True, (100, 180, 255))
        tela.blit(dica2, (10, 60))

        # -- Tela de resultado ------------------------------------
        if self.fase == 'resultado':
            capturou = self.resultado == 'capturado'
            cor_res  = (80, 255, 120) if capturou else (255, 80, 80)
            msg_res  = 'PEIXE CAPTURADO!' if capturou else 'O peixe escapou...'
            surf_res = pygame.font.SysFont('arial', 42, bold=True).render(msg_res, True, cor_res)
            # Caixa de fundo
            caixa = pygame.Surface((surf_res.get_width() + 40, surf_res.get_height() + 20),
                                   pygame.SRCALPHA)
            caixa.fill((0, 0, 0, 160))
            tela.blit(caixa, (largura // 2 - caixa.get_width() // 2,
                               altura  // 2 - caixa.get_height() // 2))
            tela.blit(surf_res, (largura // 2 - surf_res.get_width() // 2,
                                  altura  // 2 - surf_res.get_height() // 2))
            confirmar = fonte_n.render('Pressione qualquer tecla para continuar', True, (180, 180, 180))
            tela.blit(confirmar, (largura // 2 - confirmar.get_width() // 2,
                                   altura  // 2 + 54))

    def _desenhar_barra(self, tela: pygame.Surface, largura: int, fonte):
        larg_barra, alt_barra = 440, 28
        x_barra = largura // 2 - larg_barra // 2
        y_barra = 52

        # Pulso quando proxima de capturar
        if self.barra > 70:
            pulso = int(3 * abs(math.sin(self._tick * 0.18)))
            pygame.draw.rect(tela, (60, 180, 80),
                             (x_barra - pulso - 4, y_barra - pulso - 4,
                              larg_barra + (pulso + 4) * 2, alt_barra + (pulso + 4) * 2),
                             border_radius=8)

        # Fundo
        pygame.draw.rect(tela, (45, 45, 70),
                         (x_barra - 3, y_barra - 3, larg_barra + 6, alt_barra + 6),
                         border_radius=8)
        pygame.draw.rect(tela, (18, 18, 38),
                         (x_barra, y_barra, larg_barra, alt_barra), border_radius=6)

        # Preenchimento
        preench = int(larg_barra * min(self.barra, 100) / 100)
        if preench > 0:
            if self.barra > 60:
                cor_fill = (60, 200, 60)
            elif self.barra > 30:
                cor_fill = (220, 170, 30)
            else:
                cor_fill = (200, 40, 40)
            pygame.draw.rect(tela, cor_fill,
                             (x_barra, y_barra, preench, alt_barra), border_radius=6)

        # Marcadores 25 / 50 / 75%
        for pct in (25, 50, 75):
            mx = x_barra + int(larg_barra * pct / 100)
            pygame.draw.line(tela, (120, 120, 160),
                             (mx, y_barra), (mx, y_barra + alt_barra))

        # Borda
        pygame.draw.rect(tela, (80, 80, 120),
                         (x_barra, y_barra, larg_barra, alt_barra), 2, border_radius=6)

        # Texto
        label   = f'{int(self.barra)}%'
        cor_t   = (255, 100, 80) if self.barra <= 30 else (230, 230, 230)
        txt_b   = fonte.render(label, True, cor_t)
        tela.blit(txt_b, (x_barra + larg_barra // 2 - txt_b.get_width() // 2,
                           y_barra + alt_barra // 2 - txt_b.get_height() // 2))
