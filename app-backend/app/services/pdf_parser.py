import re
import subprocess
import tempfile
import os
import unicodedata
from typing import List, Optional
from sqlalchemy.orm import Session
from .. import models

class PDFParser:
    ALIASES = {
        "tecnicasdeconstrucaodeprogramas": "INF01120",
        "introducaoaarquiteturadecomputadores": "INF01112",
        "arquiteturaeorganizacaodecomputadoresi": "INF01075",
        "organizacaodecomputadoresb": "INF01113",
        "teoriadacomputacaon": "INF05035",
        "introducaoaengenhariadecomputacao": "ECP99002",
    }

    def __init__(self, db: Optional[Session] = None, aliases: Optional[dict] = None):
        """
        Inicializa o parseador de PDF.

        Parâmetros de entrada:
            db (Optional[Session]): Sessão do banco de dados do SQLAlchemy (opcional).
            aliases (Optional[dict]): Dicionário de aliases de disciplinas mapeando nomes normalizados para códigos (opcional).

        Parâmetros de saída:
            Nenhum.
        """
        self.db = db
        self.aliases = aliases if aliases is not None else self.ALIASES

    def normalize_name(self, name: str) -> str:
        """
        Normaliza o nome de uma disciplina para comparação segura. Remove acentos, caracteres especiais,
        converte para minúsculas e remove sufixos de turmas/departamentos comuns (ex: '- A', '- CIC').

        Parâmetros de entrada:
            name (str): O nome original da disciplina.

        Parâmetros de saída:
            str: O nome normalizado contendo apenas caracteres alfanuméricos minúsculos.
        """
        if not name:
            return ""
        n = unicodedata.normalize('NFD', name)
        n = "".join([c for c in n if unicodedata.category(c) != 'Mn'])
        n = n.lower()
        # Strip trailing - A, - B, - C, - CIC (up to 3 chars)
        n = re.sub(r'\s*-\s*[a-z0-9]{1,3}$', '', n)
        # Strip trailing single letters like A, B, C, D, N
        n = re.sub(r'\b(a|b|c|d|cic|n)\b$', '', n)
        n = re.sub(r'[^a-z0-9]', '', n).strip()
        return n

    def parse_pdf_completed_courses(self, pdf_bytes: bytes, expected_course: Optional[str] = None, db_courses: Optional[List] = None) -> List[str]:
        """
        Faz o parse de um PDF de histórico escolar da UFRGS, extraindo e retornando a lista de códigos
        das disciplinas concluídas com aprovação ou dispensa.

        Parâmetros de entrada:
            pdf_bytes (bytes): Os bytes do arquivo PDF do histórico escolar.
            expected_course (Optional[str]): Nome do curso esperado para validação com o histórico (opcional).
            db_courses (Optional[List]): Lista de objetos de disciplinas do banco de dados (opcional).

        Parâmetros de saída:
            List[str]: Lista de códigos das disciplinas concluídas/aprovadas encontradas no histórico.
        """
        # Write pdf_bytes to a named temporary file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_pdf:
            temp_pdf.write(pdf_bytes)
            temp_pdf_path = temp_pdf.name
            
        try:
            # Run pdftotext to extract text
            result = subprocess.run(
                ["pdftotext", temp_pdf_path, "-"],
                capture_output=True,
                text=True,
                check=True
            )
            text_content = result.stdout
        finally:
            # Clean up the temporary PDF file
            try:
                os.unlink(temp_pdf_path)
            except OSError:
                pass

        if expected_course:
            # Search for the course name in the PDF (e.g. "Curso: CIÊNCIA DA COMPUTAÇÃO")
            course_match = re.search(r"Curso:\s*(.*)", text_content, re.IGNORECASE)
            if not course_match:
                raise ValueError("Não foi possível identificar o nome do curso no histórico escolar enviado.")
            
            pdf_course = course_match.group(1).strip()
            
            # Function to normalize strings (removes accents, extra spaces, lowercases, and ignores de/da/do)
            def normalize(name):
                """
                Função auxiliar interna para normalizar strings de nomes de cursos,
                removendo acentos, espaços extras, convertendo para minúsculas e
                removendo preposições comuns como 'da', 'de', 'do'.

                Parâmetros de entrada:
                    name (str): Nome do curso a ser normalizado.

                Parâmetros de saída:
                    str: Nome normalizado contendo apenas caracteres alfanuméricos minúsculos.
                """
                n = unicodedata.normalize('NFD', name)
                n = "".join([c for c in n if unicodedata.category(c) != 'Mn'])
                n = n.lower()
                n = re.sub(r'\b(da|de|do)\b', '', n)
                return re.sub(r'[^a-z0-9]', '', n)
                
            if normalize(pdf_course) != normalize(expected_course):
                raise ValueError(
                    f"O histórico enviado é do curso '{pdf_course.upper()}', "
                    f"mas o seu vínculo atual é no curso '{expected_course.upper()}'. "
                    f"Por favor, envie o histórico correto."
                )

        # Parse the text content line-by-line
        lines = [line.strip() for line in text_content.splitlines() if line.strip()]
        completed_codes = set()
        completed_names = set()
        
        i = 0
        n = len(lines)
        
        while i < n:
            line = lines[i]
            
            # Check if line matches a semester header (e.g., 2025/2)
            if re.match(r"^\d{4}/\d$", line):
                s_idx = -1
                # Scan ahead to find the situation (usually within next 8 lines)
                for offset in range(1, 8):
                    if i + offset >= n:
                        break
                    curr = lines[i + offset]
                    # If we hit another semester header or a page footer, stop scanning this block
                    if re.match(r"^\d{4}/\d$", curr) or "of" in curr or "https://" in curr:
                        break
                    
                    is_sit = curr.lower() in [
                        "aprovado", "aprovada",
                        "liberação com crédito", "liberação com credito",
                        "liberação sem crédito", "liberação sem credito",
                        "dispensa", "aproveitamento",
                        "matriculado", "matriculada",
                        "reprovado", "reprovada", "cancelado",
                        "cancelado com justificativa"
                    ]
                    if is_sit:
                        s_idx = i + offset
                        break
                
                if s_idx != -1:
                    situation = lines[s_idx]
                    is_completed = situation.lower() in [
                        "aprovado", "aprovada",
                        "liberação com crédito", "liberação com credito",
                        "liberação sem crédito", "liberação sem credito",
                        "dispensa", "aproveitamento"
                    ]
                    
                    # Reconstruct course name
                    name_start = i + 1
                    name_end = max(name_start + 1, s_idx - 2)
                    course_text = " ".join(lines[name_start:name_end]).strip()
                    
                    # Extract code if present (like "[INF01127] ENGENHARIA DE SOFTWARE")
                    code_match = re.search(r"[\[\(]([A-Z0-9]{3,10})[\]\)]", course_text)
                    if code_match:
                        code = code_match.group(1)
                        name = course_text.replace(code_match.group(0), "").strip()
                    else:
                        code = None
                        name = course_text
                    
                    if is_completed:
                        if code:
                            completed_codes.add(code)
                        if name:
                            completed_names.add(name)
                    
                    i = s_idx + 1
                    continue
            
            # Scan for any standalone parenthesized or bracketed code in non-semester lines
            code_match = re.search(r"[\[\(]([A-Z0-9]{3,10})[\]\)]", line)
            if code_match:
                code = code_match.group(1)
                name = line.replace(code_match.group(0), "").strip()
                # If it is a completed list or we're just extracting general info:
                completed_codes.add(code)
                if name:
                    completed_names.add(name)
                    
            i += 1

        # Fallback to query database if self.db is set and db_courses is not provided
        if db_courses is None and self.db is not None:
            db_courses = self.db.query(models.Course).all()

        # Map the extracted codes and names to the actual database courses
        db_by_code = {}
        db_by_name = {}
        if db_courses:
            for course in db_courses:
                db_by_code[course.code.lower().strip()] = course.code
                db_by_name[self.normalize_name(course.name)] = course.code

        final_codes = set()
        
        # 1. Map from extracted codes
        for code in completed_codes:
            code_lower = code.lower().strip()
            if code_lower in db_by_code:
                final_codes.add(db_by_code[code_lower])
                
        # 2. Map from extracted names (using normalization and ALIASES)
        for name in completed_names:
            norm_name = self.normalize_name(name)
            if not norm_name:
                continue
            if norm_name in self.aliases:
                alias_code = self.aliases[norm_name]
                if alias_code.lower() in db_by_code:
                    final_codes.add(db_by_code[alias_code.lower()])
            elif norm_name in db_by_name:
                final_codes.add(db_by_name[norm_name])

        # If no db_courses provided (e.g. testing or backwards compatibility),
        # return the found codes directly
        if not db_courses:
            return list({c for c in completed_codes if not c.startswith("VAERE")})

        # Filter out empty/invalid codes and VAERE
        return list({c for c in final_codes if c and not c.startswith("VAERE")})

