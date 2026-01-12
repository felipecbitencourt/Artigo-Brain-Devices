"""
Script para extrair texto de arquivos PDF e salvar em formato JSON.

Dependências:
    pip install PyMuPDF

Uso:
    python extract_pdf_to_json.py
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime

try:
    import fitz  # PyMuPDF
except ImportError:
    print("❌ PyMuPDF não está instalado.")
    print("   Execute: pip install PyMuPDF")
    sys.exit(1)


def extract_text_from_pdf(pdf_path: str) -> dict:
    """
    Extrai texto de um arquivo PDF.
    
    Args:
        pdf_path: Caminho para o arquivo PDF
        
    Returns:
        Dicionário com metadados e texto extraído por página
    """
    doc = fitz.open(pdf_path)
    
    result = {
        "arquivo": os.path.basename(pdf_path),
        "caminho_original": str(pdf_path),
        "data_extracao": datetime.now().isoformat(),
        "total_paginas": len(doc),
        "metadados": doc.metadata,
        "paginas": []
    }
    
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text")
        result["paginas"].append({
            "numero": page_num,
            "texto": text.strip(),
            "caracteres": len(text)
        })
    
    # Texto completo concatenado
    result["texto_completo"] = "\n\n".join(
        [p["texto"] for p in result["paginas"]]
    )
    result["total_caracteres"] = len(result["texto_completo"])
    
    doc.close()
    return result


def process_all_pdfs(input_dir: str, output_dir: str) -> list:
    """
    Processa todos os PDFs em um diretório.
    
    Args:
        input_dir: Diretório com os PDFs
        output_dir: Diretório para salvar os JSONs
        
    Returns:
        Lista de arquivos processados
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    processed = []
    pdf_files = list(input_path.glob("*.pdf"))
    
    if not pdf_files:
        print(f"⚠️  Nenhum arquivo PDF encontrado em: {input_dir}")
        return processed
    
    print(f"📂 Encontrados {len(pdf_files)} arquivo(s) PDF\n")
    
    for pdf_file in pdf_files:
        print(f"📄 Processando: {pdf_file.name}")
        
        try:
            data = extract_text_from_pdf(str(pdf_file))
            
            # Nome do arquivo JSON (mesmo nome, extensão diferente)
            json_filename = pdf_file.stem + ".json"
            json_path = output_path / json_filename
            
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"   ✅ Salvo: {json_filename}")
            print(f"   📊 {data['total_paginas']} páginas, {data['total_caracteres']:,} caracteres\n")
            
            processed.append({
                "pdf": pdf_file.name,
                "json": json_filename,
                "paginas": data["total_paginas"],
                "caracteres": data["total_caracteres"]
            })
            
        except Exception as e:
            print(f"   ❌ Erro: {e}\n")
    
    return processed


def main():
    # Diretórios padrão (relativos ao script)
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    
    input_dir = project_dir  # PDFs estão na raiz do projeto
    output_dir = project_dir / "textos_json"
    
    print("=" * 60)
    print("🔄 EXTRATOR DE PDF PARA JSON")
    print("=" * 60)
    print(f"\n📥 Entrada: {input_dir}")
    print(f"📤 Saída:   {output_dir}\n")
    print("-" * 60 + "\n")
    
    processed = process_all_pdfs(str(input_dir), str(output_dir))
    
    print("-" * 60)
    print(f"\n✨ Processamento concluído!")
    print(f"   Total: {len(processed)} arquivo(s) convertido(s)")
    
    # Salvar resumo
    if processed:
        summary_path = output_dir / "_resumo_extracao.json"
        summary = {
            "data_processamento": datetime.now().isoformat(),
            "total_arquivos": len(processed),
            "arquivos": processed
        }
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"   Resumo salvo em: {summary_path.name}")


if __name__ == "__main__":
    main()
