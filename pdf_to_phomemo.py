import asyncio
import sys
import fitz  # PyMuPDF
from PIL import Image
import print_phomemo

async def main():
    if len(sys.argv) < 2:
        print("Uso: python pdf_to_phomemo.py <arquivo.pdf>")
        return

    file_paths = sys.argv[1:]
    
    # 1. Find Printer First (Reuse robust find_printer from print_phomemo)
    target = await print_phomemo.find_printer()

    if not target:
        print("\n\u274c Operação cancelada: Impressora não selecionada.")
        return
        
    print(f"\n\u2705 Alvo: {target.name or 'Unknown'} ({target.address})")

    for pdf_path in file_paths:
        print(f"\nProcessando arquivo: {pdf_path}")
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            print(f"Erro ao abrir PDF {pdf_path}: {e}")
            continue

        total_pages = len(doc)
        for i, page in enumerate(doc):
            print(f"  --- Imprimindo página {i+1} de {total_pages} ---")
            
            # Render page to Pixmap (Image) at printer's density
            # Phomemo T02 is ~203 DPI
            pix = page.get_pixmap(dpi=203)
            
            # Convert to PIL Image directly in memory
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Print (Wait for completion of this page before starting next)
            success = await print_phomemo.print_image(target, img)
            
            if not success:
                print(f"  \u274c Falha na página {i+1}. Interrompendo.")
                break
                
            # Optional: Short sleep between pages to let printer catch up/cool down
            if i < total_pages - 1:
                print("  Aguardando 2s para próxima página...")
                await asyncio.sleep(2)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrompido.")
    except Exception as e:
        print(f"\nErro fatal: {e}")
