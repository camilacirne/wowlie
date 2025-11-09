import re
from typing import List, Tuple

COMMON = {
    "password", "123456", "qwerty", "letmein", "admin", "welcome",
    "abc123", "iloveyou", "wowlie"
}

def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
    """
    Regras simples e eficientes:
      - >= 12 chars
      - tem minúscula, maiúscula, dígito, símbolo
      - não estar em lista comum
      - evitar repetições longas do mesmo caractere
    Retorna (ok, erros)
    """
    errors: List[str] = []
    if not password or len(password) < 8:
        errors.append("Mínimo de 8 caracteres.")

    if password.lower() in COMMON:
        errors.append("Senha muito comum.")

    if not re.search(r"[a-z]", password):
        errors.append("Inclua letra minúscula.")
    if not re.search(r"[A-Z]", password):
        errors.append("Inclua letra maiúscula.")
    if not re.search(r"\d", password):
        errors.append("Inclua dígito.")
    if not re.search(r"[^\w\s]", password): 
        errors.append("Inclua símbolo (ex: !@#$%).")
    if re.search(r"(.)\1\1\1", password):
        errors.append("Evite repetições longas do mesmo caractere.")

    return (len(errors) == 0, errors)
