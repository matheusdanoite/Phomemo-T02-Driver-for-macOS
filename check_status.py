import asyncio
from bleak import BleakScanner, BleakClient

# Based on previous scan
NOTIFY_UUID = "0000ff03-0000-1000-8000-00805f9b34fb"
READ_UUID   = "0000ff01-0000-1000-8000-00805f9b34fb"

def notification_handler(sender, data):
    print(f"Notificação recebida de {sender}: {data.hex()} (Int: {int.from_bytes(data, 'little')})")

async def check_status():
    print("Procurando impressora...")
    device = await BleakScanner.find_device_by_filter(
        lambda d, ad: d.name and ("T02" in d.name or "Phomemo" in d.name)
    )
    
    if not device:
        print("Impressora não encontrada.")
        return

    print(f"Conectando a {device.name}...")
    async with BleakClient(device) as client:
        print(f"Conectado. Monitorando status por 20 segundos...")
        
        # Try reading initial status
        try:
            val = await client.read_gatt_char(READ_UUID)
            print(f"Leitura inicial (ff01): {val.hex()} (Int: {int.from_bytes(val, 'little')})")
        except Exception as e:
            print(f"Erro ao ler ff01: {e}")

        # Subscribe to notifications
        try:
            await client.start_notify(NOTIFY_UUID, notification_handler)
        except Exception as e:
            print(f"Erro ao assinar ff03: {e}")
            
        print("\n*** AÇÃO NECESSÁRIA ***")
        print("Por favor, abra a tampa da impressora, tire o papel, e feche novamente.")
        print("Observe se aparecem novos códigos no terminal.")
        
        await asyncio.sleep(20)
        await client.stop_notify(NOTIFY_UUID)

if __name__ == "__main__":
    asyncio.run(check_status())
