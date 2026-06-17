import hashlib
import os

def hash_password(password: str) -> str:
    """
    Gera um hash seguro de senha utilizando PBKDF2 com SHA256 e um salt aleatório.
    Se a senha já estiver no formato de hash (separada por '$' com salt de 32 caracteres e hash de 64),
    retorna a senha original para evitar duplo hashing.

    Parâmetros de entrada:
        password (str): A senha em texto puro ou já com hash.

    Parâmetros de saída:
        str: A senha criptografada no formato "salt$hash_hex".
    """
    # If the password is already hashed, return it as is (prevents double hashing)
    if password.count('$') == 1:
        parts = password.split('$')
        if len(parts[0]) == 32 and len(parts[1]) == 64:
            return password
            
    salt = os.urandom(16).hex()
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"{salt}${dk.hex()}"

def verify_password(password: str, hashed: str) -> bool:
    """
    Verifica se uma senha em texto puro corresponde ao hash armazenado.
    Suporta um fallback para senhas legadas sem hash (compara em texto plano).

    Parâmetros de entrada:
        password (str): A senha em texto puro informada pelo usuário.
        hashed (str): O hash de senha armazenado no banco de dados.

    Parâmetros de saída:
        bool: True se a senha estiver correta, False caso contrário.
    """
    # Fallback for legacy unhashed passwords
    if '$' not in hashed:
        return password == hashed
        
    try:
        salt, key_hex = hashed.split('$')
        dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return dk.hex() == key_hex
    except Exception:
        return False
