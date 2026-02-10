import asyncio
import time
from bleak import BleakScanner, BleakClient

# UUIDs discovered
NOTIFY_UUID = "0000ff03-0000-1000-8000-00805f9b34fb"
READ_UUID   = "0000ff01-0000-1000-8000-00805f9b34fb"
WRITE_UUID  = "0000ff02-0000-1000-8000-00805f9b34fb"

def notification_handler(sender, data):
    timestamp = time.strftime("%H:%M:%S")
    hex_data = data.hex(" ")
    
    if len(data) < 3 or data[0] != 0x1a:
        print(f"[{timestamp}] Notificação ignorada (não é status): {hex_data}")
        return

    # LOGIC DISCOVERED:
    # Byte 2 (Index 2):
    #   Bit 0: 1 = LID OPEN, 0 = LID CLOSED
    #   Bit 4: 1 = PAPER PRESENT, 0 = PAPER OUT
    
    lid_open = bool(data[2] & 0x01)
    paper_present = bool(data[2] & 0x10)
    
    status_str = "TAMPA: " + ("ABERTA" if lid_open else "FECHADA")
    status_str += " | PAPEL: " + ("OK" if paper_present else "AUSENTE")
    
    print(f"[{timestamp}] Status: {status_str} ({hex_data})")

async def check_status():
    print("Iniciando busca por impressoras (10 segundos)...")
    
    # Use return_adv=True to get more details on macOS
    devices = await BleakScanner.discover(timeout=10.0, return_adv=True)
    
    found_devices = list(devices.values())
    
    if not found_devices:
        print("Nenhum dispositivo Bluetooth encontrado.")
        return

    print("\n--- Dispositivos Encontrados ---")
    for i, (device, adv) in enumerate(found_devices):
        name = device.name or "Unknown"
        print(f"{i}: {name} ({device.address}) | RSSI: {adv.rssi}")

    print("\nDigite o NÚMERO da impressora (Provavelmente 'T02' ou um 'Unknown' com sinal forte):")
    choice = input("Número >> ").strip()
    
    target_device = None
    if choice.isdigit():
        idx = int(choice)
        if 0 <= idx < len(found_devices):
            target_device = found_devices[idx][0]
    else:
        # Fallback to manual UUID if they typed it
        for d, a in found_devices:
            if d.address.upper() == choice.upper():
                target_device = d
                break

    if not target_device:
        print("Abortando: Nenhuma impressora selecionada.")
        return

    print(f"\nConectando a {target_device.name or 'Unknown'} ({target_device.address})...")
    # Use the device object directly
    async with BleakClient(target_device) as client:
        print(f"Conectado: {client.is_connected}")
        
        # Subscribe to notifications
        print(f"Assinando notificações em {NOTIFY_UUID}...")
        await client.start_notify(NOTIFY_UUID, notification_handler)
        
        print("\n*** MONITORAMENTO ATIVO ***")
        print("Instruções:")
        print("1. Abra a tampa da impressora.")
        print("2. Remova o papel.")
        print("3. Feche a tampa.")
        print("4. Aguarde e observe os logs abaixo.")
        print("Pressione Ctrl+C para parar.\n")
        
        # Periodic Status Query (Attempting common ESC/POS / Phomemo status commands)
        # Commands to try: 
        # \x10\x04\x01 (Real-time status)
        # \x1d\x67\x6e (Check paper)
        # \x1b\x76 (Status request in some clones)
        query_commands = [b'\x10\x04\x01', b'\x1d\x67\x6e', b'\x1b\x76']
        
        try:
            while True:
                for cmd in query_commands:
                    # Try writing to the WRITE characteristic to provoke a response
                    try:
                        # await client.write_gatt_char(WRITE_UUID, cmd, response=False)
                        pass # Disabled by default to avoid interference with printing, 
                             # enable if notifications are not automatic
                    except:
                        pass
                await asyncio.sleep(2)
        except asyncio.CancelledError:
            pass
        except KeyboardInterrupt:
            print("\nEncerrando...")
        finally:
            await client.stop_notify(NOTIFY_UUID)

if __name__ == "__main__":
    try:
        asyncio.run(check_status())
    except KeyboardInterrupt:
        pass
