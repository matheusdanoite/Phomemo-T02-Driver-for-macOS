import asyncio
import sys
from bleak import BleakScanner, BleakClient
from PIL import Image

# UUIDs discovered
WRITE_CHARACTERISTIC_UUID = "0000ff02-0000-1000-8000-00805f9b34fb"

# Printer Width (Dots)
PRINTER_WIDTH = 384

def process_image(image_path):
    img = Image.open(image_path)
    
    # Resize keeping aspect ratio
    w_percent = (PRINTER_WIDTH / float(img.size[0]))
    h_size = int((float(img.size[1]) * float(w_percent)))
    img = img.resize((PRINTER_WIDTH, h_size), Image.Resampling.LANCZOS)
    
    # Convert to 1-bit
    img = img.convert("1")
    
    return img

def image_to_escpos(img):
    """
    Convert 1-bit PIL image to ESC/POS 'GS v 0' raster format.
    """
    WIDTH_BYTES = PRINTER_WIDTH // 8
    
    from PIL import ImageOps
    # Invert so white=0 (no burn), black=1 (burn)
    img = ImageOps.invert(img.convert("L")).convert("1")
    
    data = img.tobytes()
    
    commands = []
    
    # Init printer
    commands.append(b'\x1b\x40') 
    
    # Send image in chunks
    chunk_height = 100
    total_height = img.height
    
    for y in range(0, total_height, chunk_height):
        h = min(chunk_height, total_height - y)
        
        start = y * WIDTH_BYTES
        end = (y + h) * WIDTH_BYTES
        chunk_data = data[start:end]
        
        # Header for this chunk
        xL = WIDTH_BYTES & 0xFF
        xH = (WIDTH_BYTES >> 8) & 0xFF
        
        yL = h & 0xFF
        yH = (h >> 8) & 0xFF
        
        cmd = b'\x1d\x76\x30\x00' + bytes([xL, xH, yL, yH]) + chunk_data
        commands.append(cmd)
        
    # Feed lines (footer)
    commands.append(b'\x1b\x64\x03')
    
    return commands

async def print_image(address, image_path):
    print(f"Processando imagem: {image_path}")
    try:
        img = process_image(image_path)
    except Exception as e:
        print(f"Erro ao abrir imagem: {e}")
        return

    commands = image_to_escpos(img)
    
    print(f"Tentando conectar a {address} ...")
    connected = False
    client = None
    
    # Retries for connection
    for attempt in range(3):
        try:
            # Re-find device to get fresh handle
            device = await BleakScanner.find_device_by_address(address, timeout=10.0)
            if not device:
                print(f"  Tentativa {attempt+1}: Dispositivo não encontrado. Verifique se está ligado.")
                continue
                
            client = BleakClient(device)
            await client.connect()
            connected = True
            break
        except Exception as e:
            print(f"  Tentativa {attempt+1} falhou: {e}")
            if attempt < 2:
                await asyncio.sleep(2)

    if not connected:
        print("Falha ao conectar após 3 tentativas.")
        return

    try:
        print("Conectado! Enviando dados...")
        for i, cmd in enumerate(commands):
            await client.write_gatt_char(WRITE_CHARACTERISTIC_UUID, cmd, response=False)
            await asyncio.sleep(0.05)
            if i % 10 == 0:
                 sys.stdout.write(f"\rEnviando... {int((i/len(commands))*100)}%")
                 sys.stdout.flush()
        
        print("\nEnvio concluído.")
    except Exception as e:
        print(f"Erro durante envio: {e}")
    finally:
        await client.disconnect()

async def main():
    if len(sys.argv) < 2:
        print("Uso: python print_phomemo.py <arquivo_imagem>")
        return

    img_path = sys.argv[1]
    
    print("Procurando impressora T02 (10s)...")
    
    # Use robust method to find device
    scanned = await BleakScanner.discover(return_adv=True, timeout=10.0)
    target = None
    
    for device, adv in scanned.values():
        name = device.name or "Unknown"
        # Check Name or Manufacturer Data (Phomemo often has specific ones, but simple name check first)
        if name == "T02" or "Phomemo" in name:
            target = device
            break
            
    # Fallback to T02 UUID if we found it before
    if not target:
        # Check against the UUID used in previous successful scan if possible, 
        # but addresses change on macOS (UUID randomization), so name is best.
        # Let's try to look for the one with Manufacturer ID 0 if name fails?
        pass

    if not target:
        print("\n\u274c Impressora não encontrada automaticamente pelo nome.")
        print("Dicas:")
        print("1. Desligue e ligue a impressora novamente.")
        print("2. Certifique-se de que o Bluetooth do Mac está ligado.")
        print("3. Tente rodar 'scan_phomemo.py' novamente se o nome mudou.")
        return
        
    print(f"\n\u2705 Encontrado: {target.name} ({target.address})")
    await print_image(target.address, img_path)

if __name__ == "__main__":
    asyncio.run(main())
