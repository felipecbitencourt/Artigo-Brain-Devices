"""
Script para dividir o artigo revisado em seções separadas.

Uso:
    python split_article_sections.py
"""

import json
import os
import re
from pathlib import Path


def split_article_into_sections(json_path: str, output_dir: str) -> dict:
    """
    Divide o artigo em seções baseado nos títulos identificados.
    
    Args:
        json_path: Caminho para o arquivo JSON do artigo
        output_dir: Diretório para salvar os arquivos TXT
        
    Returns:
        Dicionário com as seções extraídas
    """
    # Carregar o JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    texto_completo = data.get('texto_completo', '')
    
    # Definir os padrões de seção (títulos em ordem de aparição)
    section_patterns = [
        (r'^Abstract\s*$', 'Abstract'),
        (r'^Keywords\s*$', 'Keywords'),
        (r'^Introduction\s*$', 'Introduction'),
        (r'^Background\s*$', 'Background'),
        (r'^Method\s*$', 'Method'),
        (r'^Results\s*$', 'Results'),
        (r'^Table Description\s*$', 'Table_Description'),
        (r'^Discussion of Results\s*$', 'Discussion'),
        (r'^Limitations of Technologies Evaluated\s*$', 'Limitations'),
        (r'^Conclusion\s*$', 'Conclusion'),
        (r'^Acknowledgment\s*$', 'Acknowledgment'),
        (r'^Bibliography\s*$', 'Bibliography'),
    ]
    
    # Encontrar as posições de cada seção
    section_positions = []
    
    for pattern, name in section_patterns:
        match = re.search(pattern, texto_completo, re.MULTILINE | re.IGNORECASE)
        if match:
            section_positions.append({
                'name': name,
                'start': match.start(),
                'end': match.end()
            })
    
    # Ordenar por posição
    section_positions.sort(key=lambda x: x['start'])
    
    # Extrair o título (antes do Abstract)
    title_end = section_positions[0]['start'] if section_positions else len(texto_completo)
    title_text = texto_completo[:title_end].strip()
    
    # Criar diretório de saída
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    sections = {}
    
    # Salvar o título
    sections['00_Title'] = title_text
    with open(output_path / '00_Title.txt', 'w', encoding='utf-8') as f:
        f.write(title_text)
    
    # Extrair conteúdo de cada seção
    for i, section in enumerate(section_positions):
        # Determinar o fim da seção (início da próxima ou fim do texto)
        if i + 1 < len(section_positions):
            section_end = section_positions[i + 1]['start']
        else:
            section_end = len(texto_completo)
        
        # Extrair o texto da seção (incluindo o título)
        section_text = texto_completo[section['start']:section_end].strip()
        
        # Remover o título da seção do conteúdo (primeira linha)
        lines = section_text.split('\n')
        if len(lines) > 1:
            section_content = '\n'.join(lines[1:]).strip()
        else:
            section_content = section_text
        
        # Numerar para manter ordem
        order = str(i + 1).zfill(2)
        filename = f"{order}_{section['name']}.txt"
        
        sections[filename] = section_content
        
        with open(output_path / filename, 'w', encoding='utf-8') as f:
            f.write(section_content)
        
        print(f"✅ Criado: {filename} ({len(section_content):,} caracteres)")
    
    return sections


def main():
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    
    json_path = project_dir / "textos_json" / "Artigo-Revisado.json"
    output_dir = project_dir / "Artigo-Partes"
    
    print("=" * 60)
    print("📄 DIVISOR DE SEÇÕES DO ARTIGO")
    print("=" * 60)
    print(f"\n📥 Entrada: {json_path}")
    print(f"📤 Saída:   {output_dir}\n")
    print("-" * 60 + "\n")
    
    sections = split_article_into_sections(str(json_path), str(output_dir))
    
    print("\n" + "-" * 60)
    print(f"\n✨ Total: {len(sections)} seções criadas!")


if __name__ == "__main__":
    main()
