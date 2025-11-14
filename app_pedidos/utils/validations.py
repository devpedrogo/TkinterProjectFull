# utils/validations.py
import re


def validar_nome(nome):
    """Nome obrigatório e não vazio."""
    return nome and nome.strip() != ""


def validar_email(email):
    """Validação de formato de e-mail simples (ex: nome@dominio.com)."""
    if not email:
        return True  # Permite vazio se não for obrigatório
    # Regex simples para garantir formato básico
    padrao = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.fullmatch(padrao, email.strip()) is not None


def validar_telefone(telefone):
    """Valida telefone com 8 a 15 dígitos (aceita espaços, hífens, parênteses, mas só conta dígitos)."""
    if not telefone:
        return True  # Permite vazio se não for obrigatório

    # Remove caracteres não numéricos
    digitos = re.sub(r'\D', '', telefone)

    # Verifica se o número de dígitos está entre 8 e 15
    return 8 <= len(digitos) <= 15