import asyncio
import sys
import time
import os
import shutil
from bleak import BleakScanner, BleakClient
from PIL import Image

# For PDF support (optional if pymupdf is installed)
try:
    import fitz
except ImportError:
    fitz = None

# UUIDs discovered
WRITE_CHARACTERISTIC_UUID = "0000ff02-0000-1000-8000-00805f9b34fb"
NOTIFY_CHARACTERISTIC_UUID = "0000ff03-0000-1000-8000-00805f9b34fb"

# Printer Width (Dots)
PRINTER_WIDTH = 384

# Directions
WATCH_DIR = "print_queue"
PROCESSED_DIR = os.path.join(WATCH_DIR, "processed")

def process_image(img_input):
    """
    Takes a path or a PIL Image object and prepares it for the Phomemo T02.
    """
    if isinstance(img_input, str):
        img = Image.open(img_input)
    else:
        img = img_input
        
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
        
        # Header for this chunk: GS v 0 0 xL xH yL yH
        xL = WIDTH_BYTES & 0xFF
        xH = (WIDTH_BYTES >> 8) & 0xFF
        yL = h & 0xFF
        yH = (h >> 8) & 0xFF
        
        cmd = b'\x1d\x76\x30\x00' + bytes([xL, xH, yL, yH]) + chunk_data
        commands.append(cmd)
        
    # Feed lines (footer)
    commands.append(b'\x1b\x64\x03')
    return commands

async def find_printer():
    """
    Robust printer discovery with user selection.
    """
    print("Buscando dispositivos Bluetooth (10s)...")
    scanned = await BleakScanner.discover(return_adv=True, timeout=10.0)
    found_devices = list(scanned.values())
    
    if not found_devices:
        return None

    # Filter likely candidates first
    candidates = []
    for d, a in found_devices:
        name = d.name or "Unknown"
        if "T02" in name or "Phomemo" in name:
            candidates.append(d)
    
    # If exactly one Phomemo found, return it
    if len(candidates) == 1:
        return candidates[0]
    
    # If none found by name or multiple, show list
    print("\n--- Dispositivos Bluetooth ---")
    for i, (device, adv) in enumerate(found_devices):
        name = device.name or "Unknown"
        marker = " [PROVÁVEL]" if device in candidates else ""
        print(f"{i}: {name}{marker} ({device.address}) | RSSI: {adv.rssi}")

    print("\nDigite o NÚMERO da impressora:")
    choice = input("Número >> ").strip()
    if choice.isdigit():
        idx = int(choice)
        if 0 <= idx < len(found_devices):
            return found_devices[idx][0]
    return None

class PhomemoPrinter:
    def __init__(self, device_or_address):
        self.target = device_or_address
        self.client = None
        self._lock = asyncio.Lock()

    async def connect(self):
        if self.client and self.client.is_connected:
            return True
        
        print(f"Tentando conectar a {self.target}...")
        try:
            self.client = BleakClient(self.target)
            await self.client.connect()
            print(f"\u2705 Conectado com sucesso.")
            return True
        except Exception as e:
            print(f"\u274c Erro ao conectar: {e}")
            self.client = None
            return False

    async def ensure_connected(self):
        if not self.client or not self.client.is_connected:
            return await self.connect()
        return True

    async def check_status(self):
        """
        Attempts to read status from the printer. 
        Returns (is_ready, message)
        """
        if not await self.ensure_connected():
            return False, "Desconectado"

        status_event = asyncio.Event()
        status_result = {"ready": True, "msg": "Pronta"}

        def handler(sender, data):
            if len(data) >= 3 and data[0] == 0x1a:
                lid_open = bool(data[2] & 0x01)
                paper_present = bool(data[2] & 0x10)
                
                if lid_open:
                    status_result["msg"] = "\u26a0\ufe0f Tampa aberta!"
                    status_result["ready"] = False
                elif not paper_present:
                    status_result["msg"] = "\u26a0\ufe0f Sem papel!"
                    status_result["ready"] = False
                else:
                    status_result["msg"] = "Pronta"
                    status_result["ready"] = True
                status_event.set()

        try:
            await self.client.start_notify(NOTIFY_CHARACTERISTIC_UUID, handler)
            await self.client.write_gatt_char(WRITE_CHARACTERISTIC_UUID, b'\x1d\x67\x6e', response=False)
            try:
                await asyncio.wait_for(status_event.wait(), timeout=2.0)
            except asyncio.TimeoutError:
                pass 
            await self.client.stop_notify(NOTIFY_CHARACTERISTIC_UUID)
        except Exception as e:
            return True, f"Aviso: Status indisponível ({e})"

        return status_result["ready"], status_result["msg"]

    async def print_image(self, image_src):
        """
        Main printing function. image_src can be path or PIL Image.
        """
        async with self._lock:
            if not await self.ensure_connected():
                return False

            print(f"Processando e enviando...")
            try:
                img = process_image(image_src)
            except Exception as e:
                print(f"Erro no processamento da imagem: {e}")
                return False

            commands = image_to_escpos(img)
            
            # 1. Check Status
            ready, msg = await self.check_status()
            if not ready:
                print(f"\n\u274c CANCELADO: {msg}")
                return False
            
            # 2. Print
            print(f"Status: {msg}. Enviando dados...")
            for i, cmd in enumerate(commands):
                await self.client.write_gatt_char(WRITE_CHARACTERISTIC_UUID, cmd, response=False)
                await asyncio.sleep(0.04)
                if i % 10 == 0:
                    sys.stdout.write(f"\rProgresso: {int((i/len(commands))*100)}%")
                    sys.stdout.flush()
            
            print(f"\rProgresso: 100% - \u2705 Sucesso.")
            return True

    async def disconnect(self):
        if self.client:
            await self.client.disconnect()
            self.client = None

async def process_file(printer, file_path):
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext in ['.jpg', '.jpeg', '.png', '.bmp']:
        print(f"\nLido arquivo de imagem: {file_path}")
        return await printer.print_image(file_path)
    
    elif ext == '.pdf':
        if not fitz:
            print(f"Erro: PyMuPDF (fitz) não instalado. Não é possível imprimir PDF.")
            return False
            
        print(f"\nLido arquivo PDF: {file_path}")
        try:
            doc = fitz.open(file_path)
            for i, page in enumerate(doc):
                print(f"Pag {i+1}/{len(doc)}")
                pix = page.get_pixmap(dpi=203)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                success = await printer.print_image(img)
                if not success: return False
                if i < len(doc) - 1: await asyncio.sleep(2)
            return True
        except Exception as e:
            print(f"Erro processando PDF: {e}")
            return False
    
    return False

async def monitor_folder(printer):
    if not os.path.exists(WATCH_DIR): os.makedirs(WATCH_DIR)
    if not os.path.exists(PROCESSED_DIR): os.makedirs(PROCESSED_DIR)
    
    print(f"\n--- Iniciando Monitoramento (Polling) ---")
    print(f"Observando pasta: {os.path.abspath(WATCH_DIR)}")
    print(f"Pressione Ctrl+C para parar.\n")
    
    while True:
        try:
            await printer.ensure_connected()
            files = [f for f in os.listdir(WATCH_DIR) if os.path.isfile(os.path.join(WATCH_DIR, f))]
            
            for file_name in sorted(files):
                if file_name.startswith('.'): continue
                
                file_path = os.path.join(WATCH_DIR, file_name)
                success = await process_file(printer, file_path)
                
                if success:
                    dest = os.path.join(PROCESSED_DIR, file_name)
                    # Handle renaming if file exists in processed
                    if os.path.exists(dest):
                        base, ext = os.path.splitext(file_name)
                        dest = os.path.join(PROCESSED_DIR, f"{base}_{int(time.time())}{ext}")
                    shutil.move(file_path, dest)
                    print(f"Arquivo {file_name} movido para processed.")
                else:
                    print(f"Falha ao imprimir {file_name}. Tentará novamente no próximo ciclo.")
            
        except Exception as e:
            print(f"Erro no monitor: {e}")
            
        await asyncio.sleep(2)

async def main():
    target = await find_printer()
    if not target:
        print("\n\u274c Nenhuma impressora selecionada ou encontrada.")
        return
        
    printer = PhomemoPrinter(target)
    
    if len(sys.argv) > 1:
        # Modo de comando único
        img_path = sys.argv[1]
        await printer.print_image(img_path)
        await printer.disconnect()
    else:
        # Modo monitoramento
        await monitor_folder(printer)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuário.")
    except Exception as e:
        print(f"\nErro fatal: {e}")
