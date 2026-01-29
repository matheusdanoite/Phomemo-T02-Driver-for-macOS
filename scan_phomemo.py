import asyncio
from bleak import BleakScanner, BleakClient

async def scan():
    print("Iniciando escaneamento Bluetooth (10 segundos)...")
    
    # Use return_adv=True to get both device and advertisement data
    # This returns a dict: { "ADDRESS": (BLEDevice, AdvertisementData) }
    scanned_data = await BleakScanner.discover(return_adv=True, timeout=10.0)
    
    # Convert dict items to a list for indexing
    device_list = list(scanned_data.values())
    
    found_devices = []
    print("\n--- Dispositivos Encontrados ---")
    for i, (device, adv_data) in enumerate(device_list):
        name = device.name or "Unknown"
        address = device.address
        rssi = adv_data.rssi
        manufacturer_data = adv_data.manufacturer_data
        
        print(f"{i}: {name} ({address}) | RSSI: {rssi}")
        if manufacturer_data:
            # Show hex of manufacturer data
            for k, v in manufacturer_data.items():
                print(f"    Manufacturer {k}: {v.hex()}")
        
        found_devices.append(device)

    if not found_devices:
        print("\nNenhum dispositivo encontrado.")
        return

    print("\n--------------------------------")
    print("Digite o NÚMERO do dispositivo que você acha que é a impressora.")
    print("Se for 'Unknown', verifique o sinal (RSSI) ou Manufacturer Data.")
    
    choice = input("Número >> ")
    if not choice.strip().isdigit():
        print("Saindo.")
        return
        
    idx = int(choice)
    if idx < 0 or idx >= len(found_devices):
        print("Opção inválida.")
        return
        
    target_device = found_devices[idx]
    target_uuid = target_device.address
    
    print(f"\nAlvo selecionado: {target_device.name or 'Unknown'} ({target_uuid})")
    print("Tentando conectar (com retentativas)...")
    
    connected = False
    for attempt in range(3):
        print(f"Tentativa {attempt+1}/3...")
        try:
            # Re-find the device to ensure a fresh handle for connection
            device = await BleakScanner.find_device_by_address(target_uuid, timeout=10.0)
            if not device:
                print("  Dispositivo não encontrado no re-scan. Verifique se desligou.")
                continue
                
            async with BleakClient(device) as client:
                print(f"  Conectado: {client.is_connected}")
                print("\n--- DETALHES DOS SERVIÇOS ---")
                for service in client.services:
                    print(f"\n[Service] {service.description} ({service.uuid})")
                    for char in service.characteristics:
                        props = ", ".join(char.properties)
                        print(f"  \u2514\u2500 [Char] {char.description} ({char.uuid})")
                        print(f"     Props: {props}")
                        if "write" in props or "write-without-response" in props:
                            print("     *** PROVÁVEL CANAL DE ESCRITA ***")
                print("\n-----------------------------")
                print("SUCESSO! Copie os UUIDs acima.")
                connected = True
                break
        except Exception as e:
            print(f"  Erro na tentativa {attempt+1}: {e}")
            await asyncio.sleep(2)
            
    if not connected:
        print("\nFalha ao conectar após 3 tentativas.")

if __name__ == "__main__":
    asyncio.run(scan())
