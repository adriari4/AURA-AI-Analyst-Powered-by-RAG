import os
import fitz  # PyMuPDF
import base64
import io
from openai import OpenAI
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

def analyze_page(image_bytes: bytes, page_num: int) -> Dict[str, Any]:
    """
    Sends page image to GPT-4o to extract text and graphics.
    """
    base64_image = encode_image(image_bytes)
    
    prompt = """
    You are an expert technical document analyzer. Your task is to process this page from a technical thesis (likely a screenshot).
    
    1. **OCR Text**: Extract all readable text from the page. 
       - Fix line breaks to form coherent paragraphs.
       - Remove repeated headers, footers, or page numbers.
       - If the page is unreadable, state "Page unreadable".
       
    2. **Extract Graphics**: Identify any Figures, Charts, Tables, or Diagrams.
       - For each graphic, provide a short **Caption** describing what it shows.
       - Extract any text/numbers inside the graphic.
       - If a graphic is unreadable, state "Graphic unreadable".
       
    Output your response in the following JSON format ONLY:
    {
        "page_number": <int>,
        "is_readable": <bool>,
        "main_text": "<cleaned text string>",
        "graphics": [
            {
                "type": "<Figure/Chart/Table/Diagram>",
                "caption": "<description>",
                "content": "<extracted text/data from graphic>"
            }
        ]
    }
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        import json
        return json.loads(content)
        
    except Exception as e:
        return {
            "page_number": page_num,
            "is_readable": False,
            "main_text": f"Error processing page: {str(e)}",
            "graphics": []
        }

def process_pdf(pdf_path: str) -> str:
    """
    Processes a PDF file and returns the formatted output.
    """
    if not os.path.exists(pdf_path):
        return f"Error: File not found at {pdf_path}"

    doc = fitz.open(pdf_path)
    results = []
    
    print(f"Processing {pdf_path} ({len(doc)} pages)...")
    
    for i, page in enumerate(doc):
        print(f"Analyzing page {i+1}/{len(doc)}...")
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # 2x zoom for better OCR
        img_bytes = pix.tobytes("png")
        
        page_data = analyze_page(img_bytes, i+1)
        results.append(page_data)
        
    doc.close()
    
    # Format Output
    output = []
    
    # 1. OCR Text
    output.append("## OCR Text")
    all_text = []
    for res in results:
        if res.get("is_readable", True):
            text = res.get("main_text", "")
            if text:
                all_text.append(text)
        else:
            all_text.append(f"[Page {res['page_number']} unreadable]")
            
    output.append("\n\n".join(all_text))
    output.append("\n")
    
    # 2. Extracted Graphics
    output.append("## Extracted Graphics")
    for res in results:
        graphics = res.get("graphics", [])
        if graphics:
            for g in graphics:
                output.append(f"- Page {res['page_number']}: [{g['type']}] {g['caption']}")
                if g.get('content'):
                    output.append(f"  Content: {g['content']}")
    output.append("\n")
    
    # 3. Summary
    # Generate summary from the extracted text
    full_text_for_summary = "\n".join(all_text)
    summary = generate_summary(full_text_for_summary)
    
    output.append("## Summary")
    output.append(summary)
    
    return "\n".join(output)

def process_pdf_to_json(pdf_path: str, output_path: str):
    """
    Processes a PDF and saves the raw analysis to a JSON file.
    """
    if not os.path.exists(pdf_path):
        print(f"Error: File not found at {pdf_path}")
        return

    doc = fitz.open(pdf_path)
    results = []
    
    print(f"Processing {pdf_path} ({len(doc)} pages)...")
    
    for i, page in enumerate(doc):
        print(f"Analyzing page {i+1}/{len(doc)}...")
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_bytes = pix.tobytes("png")
        
        page_data = analyze_page(img_bytes, i+1)
        results.append(page_data)
        
    doc.close()
    
    # Generate Summary
    all_text = []
    for res in results:
        if res.get("is_readable", True):
            text = res.get("main_text", "")
            if text:
                all_text.append(text)
    
    full_text = "\n".join(all_text)
    summary = generate_summary(full_text)
    
    final_data = {
        "filename": os.path.basename(pdf_path),
        "summary": summary,
        "pages": results
    }
    
    import json
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=2)
    
    print(f"Saved analysis to {output_path}")

def generate_summary(text: str) -> str:
    """Generates a summary of the thesis."""
    if not text or len(text) < 100:
        return "Not enough text to summarize."
        
    prompt = f"""
    Summarize the following technical thesis text.
    Focus on:
    1. The Problem/Context
    2. The Method/Approach
    3. The Results/Key Findings
    
    Keep it concise.
    
    Text:
    {text[:15000]} 
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating summary: {str(e)}"

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2 and sys.argv[1] == "--json":
        # Usage: python pdf_ocr_tool.py --json <pdf_path> <output_json_path>
        process_pdf_to_json(sys.argv[2], sys.argv[3])
    elif len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        print(process_pdf(pdf_path))
    else:
        print("Usage: python pdf_ocr_tool.py <path_to_pdf>")
        print("Usage: python pdf_ocr_tool.py --json <path_to_pdf> <output_json_path>")
