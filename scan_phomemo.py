import asyncio
from bleak import BleakScanner, BleakClient

async def scan():
    print("Iniciando escaneamento Bluetooth (10 segundos)...")
    
    # Use return_adv=True to get both device and advertisement data
    scanned_data = await BleakScanner.discover(return_adv=True, timeout=10.0)
    device_list = list(scanned_data.values())
    
    if not device_list:
        print("\nNenhum dispositivo encontrado.")
        return

    print("\n--- Dispositivos Encontrados ---")
    for i, (device, adv_data) in enumerate(device_list):
        name = device.name or "Unknown"
        address = device.address
        rssi = adv_data.rssi
        print(f"{i}: {name} ({address}) | RSSI: {rssi}")

    print("\n--------------------------------")
    print("Digite o NÚMERO da impressora para inspecionar os serviços.")
    
    choice = input("Número >> ").strip()
    if not choice.isdigit():
        print("Saindo.")
        return
        
    idx = int(choice)
    if idx < 0 or idx >= len(device_list):
        print("Opção inválida.")
        return
        
    target_device = device_list[idx][0]
    
    print(f"\nAlvo selecionado: {target_device.name or 'Unknown'} ({target_device.address})")
    print("Tentando conectar e explorar serviços...")
    
    try:
        async with BleakClient(target_device) as client:
            print(f"  Conectado: {client.is_connected}")
            print("\n--- DETALHES DOS SERVIÇOS ---")
            for service in client.services:
                print(f"\n[Service] {service.description} ({service.uuid})")
                for char in service.characteristics:
                    props = ", ".join(char.properties)
                    print(f"  \u2514\u2500 [Char] {char.description} ({char.uuid})")
                    print(f"     Props: {props}")
                    if "write" in props or "write-without-response" in props:
                        if "ff02" in char.uuid:
                            print("     *** CANAL DE ESCRITA DE DADOS ***")
                    if "notify" in props:
                        if "ff03" in char.uuid:
                            print("     *** CANAL DE NOTIFICAÇÃO (STATUS) ***")
            print("\n-----------------------------")
    except Exception as e:
        print(f"  Erro ao conectar: {e}")

if __name__ == "__main__":
    asyncio.run(scan())
