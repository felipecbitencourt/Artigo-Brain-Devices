"""
Script para dividir o documento de alterações necessárias em seções por revisor e comentário.

Uso:
    python split_reviewer_comments.py
"""

import json
import os
import re
from pathlib import Path


def split_reviewer_comments(json_path: str, output_dir: str) -> dict:
    """
    Divide o documento de revisão em seções por revisor e comentário.
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    texto_completo = data.get('texto_completo', '')
    
    # Criar diretório de saída
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    sections = {}
    
    # Extrair o cabeçalho (Decision Letter)
    header_match = re.search(r'^(Decision Letter.*?)(?=Reviewer 1)', texto_completo, re.DOTALL)
    if header_match:
        header_text = header_match.group(1).strip()
        sections['00_Decision_Letter.txt'] = header_text
        with open(output_path / '00_Decision_Letter.txt', 'w', encoding='utf-8') as f:
            f.write(header_text)
        print(f"✅ Criado: 00_Decision_Letter.txt ({len(header_text):,} caracteres)")
    
    # Padrões para identificar seções de revisores
    reviewer_sections = [
        (r'(Reviewer 1\s*\n.*?)(?=Reviewer 2|$)', 'Reviewer_1'),
        (r'(Reviewer 2\s*\n.*?)(?=Reviewer 3|$)', 'Reviewer_2'),
        (r'(Reviewer 3\s*\n.*?)(?=FINAL STATEMENT|$)', 'Reviewer_3'),
        (r'(FINAL STATEMENT.*?)$', 'Final_Statement'),
    ]
    
    order = 1
    for pattern, name in reviewer_sections:
        match = re.search(pattern, texto_completo, re.DOTALL)
        if match:
            content = match.group(1).strip()
            filename = f"{str(order).zfill(2)}_{name}.txt"
            sections[filename] = content
            
            with open(output_path / filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Criado: {filename} ({len(content):,} caracteres)")
            order += 1
    
    # Também criar arquivos separados para cada comentário individual
    comments_dir = output_path / "Comentarios_Individuais"
    comments_dir.mkdir(parents=True, exist_ok=True)
    
    # Padrão para identificar comentários (R1C0, R1C1, R2C0, etc.)
    comment_pattern = r'(R[123]C\d+\.?\s*\n.*?)(?=R[123]C\d+\.|R[123]AQ\d+\.|Additional Questions|Reviewer \d|FINAL STATEMENT|$)'
    aq_pattern = r'(R[123]AQ\d+\.?\s*\n.*?)(?=R[123]C\d+\.|R[123]AQ\d+\.|Reviewer \d|FINAL STATEMENT|$)'
    
    # Encontrar todos os comentários
    comments = re.findall(comment_pattern, texto_completo, re.DOTALL)
    additional_questions = re.findall(aq_pattern, texto_completo, re.DOTALL)
    
    all_items = comments + additional_questions
    
    for item in all_items:
        item = item.strip()
        if not item:
            continue
            
        # Extrair o código do comentário
        code_match = re.match(r'(R[123](?:C|AQ)\d+)', item)
        if code_match:
            code = code_match.group(1)
            filename = f"{code}.txt"
            
            with open(comments_dir / filename, 'w', encoding='utf-8') as f:
                f.write(item)
            
            print(f"   📝 {filename}")
    
    return sections


def main():
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    
    json_path = project_dir / "textos_json" / "Altereções-necessárias.json"
    output_dir = project_dir / "Alterações"
    
    print("=" * 60)
    print("📋 DIVISOR DE COMENTÁRIOS DE REVISORES")
    print("=" * 60)
    print(f"\n📥 Entrada: {json_path}")
    print(f"📤 Saída:   {output_dir}\n")
    print("-" * 60 + "\n")
    
    sections = split_reviewer_comments(str(json_path), str(output_dir))
    
    print("\n" + "-" * 60)
    print(f"\n✨ Divisão concluída!")


if __name__ == "__main__":
    main()
