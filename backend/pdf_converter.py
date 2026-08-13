import subprocess
import os
import shutil
from typing import Optional

def find_soffice_binary() -> Optional[str]:
    # Check PATH
    soffice_path = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice_path:
        return soffice_path
    
    # Check standard Windows installation paths
    candidate_paths = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\LibreOffice\program\soffice.exe"),
    ]
    
    for path in candidate_paths:
        if os.path.exists(path):
            return path
            
    return None

def convert_pptx_to_pdf(pptx_path: str, output_pdf_path: str) -> str:
    if not os.path.exists(pptx_path):
        raise FileNotFoundError(f"PPTX file not found: {pptx_path}")
        
    soffice_bin = find_soffice_binary()
    if not soffice_bin:
        raise RuntimeError("LibreOffice executable ('soffice') not found. Please install LibreOffice or add it to PATH.")
        
    out_dir = os.path.dirname(os.path.abspath(output_pdf_path))
    os.makedirs(out_dir, exist_ok=True)
    
    cmd = [
        soffice_bin,
        "--headless",
        "--convert-to", "pdf",
        pptx_path,
        "--outdir", out_dir
    ]
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"LibreOffice PDF conversion failed: {result.stderr}")
        
    # LibreOffice output filename matches pptx stem + .pdf
    base_name = os.path.splitext(os.path.basename(pptx_path))[0] + ".pdf"
    generated_pdf = os.path.join(out_dir, base_name)
    
    if os.path.exists(generated_pdf) and generated_pdf != output_pdf_path:
        if os.path.exists(output_pdf_path):
            os.remove(output_pdf_path)
        os.rename(generated_pdf, output_pdf_path)
        
    return output_pdf_path
