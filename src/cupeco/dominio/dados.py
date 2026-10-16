"""Leitura dos dados de jogo em TOML com validação estrita (D26).

Os valores de jogo (materiais, física da Dara, armas, chefes) ficam em
`src/cupeco/conteudo/*.toml` e são convertidos para dataclasses. Qualquer chave desconhecida,
faltando ou com o tipo errado gera `DadosInvalidos` que diz onde está o problema, para um
erro de digitação nunca passar em silêncio.
"""

from __future__ import annotations

import dataclasses
import tomllib
import typing
from enum import Enum
from importlib import resources
from typing import Any, TypeVar

PACOTE_CONTEUDO = "cupeco.conteudo"

T = TypeVar("T")


class DadosInvalidos(ValueError):  # noqa: N818 - nomes em português, sem o sufixo "Error"
    """Dado de jogo inválido. A mensagem começa pelo caminho da chave (ex.: `papel.cor`)."""


def ler_toml(nome: str) -> dict[str, Any]:
    """Lê um arquivo TOML do pacote de conteúdo."""
    arquivo = resources.files(PACOTE_CONTEUDO).joinpath(nome)
    return tomllib.loads(arquivo.read_text(encoding="utf-8"))


def converter(valor: Any, tipo: type[T], onde: str) -> T:
    """Converte um valor lido do TOML para `tipo`, conferindo chaves e tipos.

    Suporta dataclasses (aninhadas), enumerações (pelo valor), `str`, `int`, `float` (aceita
    inteiro), `bool` e tuplas de tamanho fixo ou variável (`tuple[int, int]`,
    `tuple[int, ...]`).
    """
    if dataclasses.is_dataclass(tipo):
        return _converter_dataclass(valor, tipo, onde)
    if isinstance(tipo, type) and issubclass(tipo, Enum):
        validos = [membro.value for membro in tipo]
        if valor not in validos:
            raise DadosInvalidos(f"{onde}: {valor!r} não é um de {', '.join(map(str, validos))}")
        return tipo(valor)
    if typing.get_origin(tipo) is tuple:
        return _converter_tupla(valor, tipo, onde)  # type: ignore[return-value]
    if tipo is bool:
        if not isinstance(valor, bool):
            raise DadosInvalidos(f"{onde}: esperava verdadeiro ou falso, veio {valor!r}")
        return valor  # type: ignore[return-value]
    if tipo is int:
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise DadosInvalidos(f"{onde}: esperava um número inteiro, veio {valor!r}")
        return valor  # type: ignore[return-value]
    if tipo is float:
        if isinstance(valor, bool) or not isinstance(valor, int | float):
            raise DadosInvalidos(f"{onde}: esperava um número, veio {valor!r}")
        return float(valor)  # type: ignore[return-value]
    if tipo is str:
        if not isinstance(valor, str):
            raise DadosInvalidos(f"{onde}: esperava um texto, veio {valor!r}")
        return valor  # type: ignore[return-value]
    raise TypeError(f"tipo não suportado nos dados: {tipo!r}")


def _converter_dataclass(valor: Any, tipo: Any, onde: str) -> Any:
    if not isinstance(valor, dict):
        raise DadosInvalidos(f"{onde}: esperava uma tabela, veio {valor!r}")
    campos = {campo.name: campo for campo in dataclasses.fields(tipo)}
    dicas = typing.get_type_hints(tipo)
    desconhecidas = sorted(set(valor) - set(campos))
    if desconhecidas:
        raise DadosInvalidos(f"{onde}: chave desconhecida: {', '.join(desconhecidas)}")
    argumentos = {}
    for nome, campo in campos.items():
        if nome in valor:
            argumentos[nome] = converter(valor[nome], dicas[nome], f"{onde}.{nome}")
        elif campo.default is dataclasses.MISSING and campo.default_factory is dataclasses.MISSING:
            raise DadosInvalidos(f"{onde}: falta a chave {nome}")
    return tipo(**argumentos)


def _converter_tupla(valor: Any, tipo: Any, onde: str) -> tuple[Any, ...]:
    if not isinstance(valor, list):
        raise DadosInvalidos(f"{onde}: esperava uma lista, veio {valor!r}")
    argumentos = typing.get_args(tipo)
    if len(argumentos) == 2 and argumentos[1] is Ellipsis:
        tipos = [argumentos[0]] * len(valor)
    else:
        if len(valor) != len(argumentos):
            raise DadosInvalidos(f"{onde}: esperava {len(argumentos)} itens, vieram {len(valor)}")
        tipos = list(argumentos)
    return tuple(
        converter(item, tipo_item, f"{onde}[{indice}]")
        for indice, (item, tipo_item) in enumerate(zip(valor, tipos, strict=True))
    )
