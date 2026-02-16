# Phomemo T02 macOS Driver (Python)

[Português Brasileiro](README.pt-br.md)

A simple, native-feeling driver for the Phomemo T02 Thermal Printer on macOS. 

This project allows you to print to your Phomemo T02 directly from macOS without using the official mobile app. It includes a Python script for command-line printing and a **Mac PDF Service** integration, adding an "Print to Phomemo" option to the native CMD+P dialog in any application (Chrome, Pages, Preview, etc.).

## Features
- **Native Integration**: Add "Print to Phomemo" to the system Print Dialog (PDF Menu).
- **Command Line Interface**: Print images (PNG/JPG) directly from the terminal.
- **Native Integration**: Add "Print to Phomemo" to the system Print Dialog (PDF Menu).
- **Auto-Printing (Folder Monitor)**: Automatically print any image or PDF dropped into a specific folder.
- **Persistent Connection**: Maintains a constant Bluetooth connection for faster printing and automatic recovery.
- **Smart Resizing**: Automatically resizes images and PDFs to fit the 48mm (384 dots) print width.

## Prerequisites
- **Hardware**: Phomemo T02 Printer.
- **OS**: macOS (tested on Sonoma/Sequoia via `bleak`).
- **Software**: Python 3.10+.

## Installation
1. **Clone or Download this repository**:
   ```bash
   git clone https://github.com/matheusdanoite/Phomemo-T02-Driver-for-macOS.git
   cd Phomemo-T02-Driver-for-macOS
   ```

2. **Set up Python Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Install Native Menu Integration** (Optional):
   This creates an alias in your user's PDF Services folder, making the option appear in the print menu.
   ```bash
   # Make sure the wrapper is executable
   chmod +x print_to_phomemo.command
   # Create the link (Replace /path/to/project with the actual path if moved)
   mkdir -p ~/Library/PDF\ Services
   ln -s "$(pwd)/print_to_phomemo.command" ~/Library/PDF\ Services/Imprimir\ na\ Phomemo
   ```

## Usage
### Method 1: Automatic Printing (Recommended)
Run the script without arguments to start the **Monitor Mode**:
```bash
./venv/bin/python print_phomemo.py
```
- **Folder**: Drop files (`.png`, `.jpg`, `.pdf`) into the `print_queue/` folder.
- **History**: Printed files are moved to `print_queue/processed/`.
- **Stay Connected**: The script stays connected to the printer, ensuring near-instant printing of new items.

### Method 2: Native Print (System Dialog)
1. Open any document in any Mac app.
2. Press **CMD + P** to open the Print Dialog.
3. Click the **PDF** button -> Select **"Imprimir na Phomemo"**.

### Method 3: Command Line (One-off)
Print an existing image or PDF file directly:
```bash
./venv/bin/python print_phomemo.py image.png
```
Scan for devices/UUIDs:
```bash
./venv/bin/python scan_phomemo.py
```

## Technical Details
- **Protocol**: The driver uses ESC/POS-like raster bit image commands (`GS v 0`) sent over BLE.
- **UUIDs**:
  - Service: `ff00`
  - Write Characteristic: `ff02`
- **Conversion**: Uses `PyMuPDF` to render PDF pages and `Pillow` to convert them to 1-bit dithered monochrome images suitable for the thermal head.

## Status Codes (Dev Notes)
The printer sends 3-byte notification packets (Prefix `1a`) to UUID `ff03`.
Byte 2 (Index 2) contains the status bits:
- **Bit 0**: `1` = Lid Open, `0` = Lid Closed.
- **Bit 4**: `1` = Paper Present, `0` = Paper Out.

**Examples:**
- `1a 05 99` -> Lid Open (153 = `1001 1001`)
- `1a 05 98` -> Lid Closed + Paper OK (152 = `1001 1000`)
- `1a 06 88` -> Lid Closed + Paper Out (136 = `1000 1000`)

Brought to your family by matheusdanoite.
