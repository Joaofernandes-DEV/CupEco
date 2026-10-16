"""Relógio de passo fixo (D8): converte o tempo real em passos iguais de simulação.

A tela desenha no ritmo que o computador conseguir, mas a simulação avança sempre em passos
de 1/60 s. Assim uma luta é determinística e pode ser reproduzida a partir dos comandos.
A conta é feita com inteiros para não acumular erro de arredondamento.
"""

PASSOS_POR_SEGUNDO = 60

# Se o computador travar por um instante, o jogo desacelera em vez de simular de uma vez
# todo o tempo perdido (o que faria a Dara "teleportar" e poderia travar de novo).
MAX_PASSOS_POR_QUADRO = 5


class PassoFixo:
    """Acumula o tempo dos quadros (em milissegundos) e diz quantos passos simular."""

    def __init__(
        self,
        passos_por_segundo: int = PASSOS_POR_SEGUNDO,
        max_passos: int = MAX_PASSOS_POR_QUADRO,
    ) -> None:
        self.passos_por_segundo = passos_por_segundo
        self.max_passos = max_passos
        # Tempo acumulado em "milissegundos × passos por segundo": 1000 unidades = 1 passo.
        self._acumulado = 0

    def avancar(self, milissegundos: int) -> int:
        """Soma o tempo de um quadro e devolve quantos passos de simulação rodar agora."""
        self._acumulado += max(milissegundos, 0) * self.passos_por_segundo
        passos, self._acumulado = divmod(self._acumulado, 1000)
        if passos > self.max_passos:
            self._acumulado = 0
            return self.max_passos
        return passos
