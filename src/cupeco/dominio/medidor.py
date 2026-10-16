"""Medidor de Reciclagem (J4, D25): 5 fardos de 100 pontos inteiros.

Enche com o dano causado e com as triagens. Um fardo paga um tiro EX; com os 5 cheios, o
mesmo botão solta o Super (a Prensa), que gasta tudo.
"""

PONTOS_POR_FARDO = 100
FARDOS = 5
PONTOS_MAXIMOS = PONTOS_POR_FARDO * FARDOS


class Medidor:
    def __init__(self, pontos: int = 0) -> None:
        self.pontos = 0
        self.ganhar(pontos)

    @property
    def fardos(self) -> int:
        """Fardos completos (o que aparece cheio no HUD)."""
        return self.pontos // PONTOS_POR_FARDO

    @property
    def cheio(self) -> bool:
        return self.pontos == PONTOS_MAXIMOS

    @property
    def pode_ex(self) -> bool:
        return self.pontos >= PONTOS_POR_FARDO

    def ganhar(self, pontos: int) -> None:
        if pontos < 0:
            raise ValueError(
                "o Medidor só ganha pontos; para gastar, use gastar_ex ou gastar_super"
            )
        self.pontos = min(PONTOS_MAXIMOS, self.pontos + pontos)

    def gastar_ex(self) -> bool:
        """Gasta um fardo, se houver. Devolve se o EX foi pago."""
        if not self.pode_ex:
            return False
        self.pontos -= PONTOS_POR_FARDO
        return True

    def gastar_super(self) -> bool:
        """Gasta o Medidor inteiro, se estiver cheio. Devolve se o Super foi pago."""
        if not self.cheio:
            return False
        self.pontos = 0
        return True
