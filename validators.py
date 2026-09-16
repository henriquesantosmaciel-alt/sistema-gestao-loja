"""
validators.py - Funcoes de validacao reutilizadas pelos modulos de negocio
e pela camada web. Centraliza regras para manter consistencia.
"""
import re

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ValidationError(Exception):
    """Erro de validacao de dados de entrada."""


def validar_texto_obrigatorio(valor, campo, tamanho_maximo=200):
    if not valor or not str(valor).strip():
        raise ValidationError(f"O campo '{campo}' e obrigatorio.")
    if len(str(valor)) > tamanho_maximo:
        raise ValidationError(f"O campo '{campo}' deve ter no maximo {tamanho_maximo} caracteres.")
    return str(valor).strip()


def validar_numero_positivo(valor, campo, permitir_zero=True):
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        raise ValidationError(f"O campo '{campo}' deve ser numerico.")
    if permitir_zero and numero < 0:
        raise ValidationError(f"O campo '{campo}' nao pode ser negativo.")
    if not permitir_zero and numero <= 0:
        raise ValidationError(f"O campo '{campo}' deve ser maior que zero.")
    return numero


def validar_inteiro_positivo(valor, campo, permitir_zero=True):
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        raise ValidationError(f"O campo '{campo}' deve ser um numero inteiro.")
    if permitir_zero and numero < 0:
        raise ValidationError(f"O campo '{campo}' nao pode ser negativo.")
    if not permitir_zero and numero <= 0:
        raise ValidationError(f"O campo '{campo}' deve ser maior que zero.")
    return numero


def validar_email(valor, campo="email", obrigatorio=False):
    if not valor:
        if obrigatorio:
            raise ValidationError(f"O campo '{campo}' e obrigatorio.")
        return None
    if not EMAIL_REGEX.match(valor.strip()):
        raise ValidationError(f"O campo '{campo}' possui um formato invalido.")
    return valor.strip().lower()


def validar_senha_forte(senha, tamanho_minimo=6):
    if not senha or len(senha) < tamanho_minimo:
        raise ValidationError(f"A senha deve ter pelo menos {tamanho_minimo} caracteres.")
    return senha
