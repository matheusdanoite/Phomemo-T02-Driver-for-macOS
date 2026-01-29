import asyncio
import sys
import fitz  # PyMuPDF
from PIL import Image
import io

# Import the image printing logic from our existing script
# We'll just define the connection/printing logic here again to keep it standalone or import if cleaner.
# Let's import to reuse code.
try:
    from print_phomemo import print_image, WRITE_CHARACTERISTIC_UUID, PRINTER_WIDTH
    import print_phomemo
except ImportError:
    # If standard import fails (e.g. running from different dir), try modifying path or copying logic.
    # For now, let's assume it's in the same directory.
    print("Erro: Não foi possível importar 'print_phomemo.py'. Certifique-se de que estão na mesma pasta.")
    sys.exit(1)


async def main():
    if len(sys.argv) < 2:
        print("Uso: python pdf_to_phomemo.py <arquivo.pdf>")
        return

    # PDF Service usually passes the file path as an argument
    # Sometimes multiple files. We'll handle arguments as file paths.
    
    file_paths = sys.argv[1:]
    
    # 1. Find Printer First (Reuse main logic or explicit scan)
    print("Procurando impressora T02...")
    from bleak import BleakScanner
    scanned = await BleakScanner.discover(return_adv=True, timeout=5.0)
    target = None
    for device, adv in scanned.values():
        name = device.name or "Unknown"
        if name == "T02" or "Phomemo" in name:
            target = device
            break

    if not target:
        print("Impressora não encontrada. Verique se está ligada.")
        return
        
    print(f"Alvo: {target.name} ({target.address})")

    for pdf_path in file_paths:
        print(f"Processando arquivo: {pdf_path}")
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            print(f"Erro ao abrir PDF {pdf_path}: {e}")
            continue

        for i, page in enumerate(doc):
            print(f"  Imprimindo página {i+1}...")
            
            # Render page to Pixmap (Image)
            # Zoom matrix to get better resolution? 
            # Printer width is 384 dots.
            # A standard A4 is ~600pts wide.
            # Let's render at reasonable dpi.
            
            pix = page.get_pixmap(dpi=203) # 203 DPI is standard for these printers
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Save temp or process directly
            # Our print_phomemo.process_image handles resizing to 384 width.
            # But process_image takes a path. Let's make a temp file or modify print_phomemo to take image object.
            
            # Easier: Save to temp buffer/file to use existing function unmodified
            temp_img_path = f"/tmp/phomemo_page_{i}.png"
            img.save(temp_img_path)
            
            # Print
            await print_phomemo.print_image(target.address, temp_img_path)
            
            # Optional: Sleep slightly between pages
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
