# Phomemo T02 macOS Driver (Python)

A simple, native-feeling driver for the Phomemo T02 Thermal Printer on macOS. 

This project allows you to print to your Phomemo T02 directly from macOS without using the official mobile app. It includes a Python script for command-line printing and a **Mac PDF Service** integration, adding an "Print to Phomemo" option to the native CMD+P dialog in any application (Chrome, Pages, Preview, etc.).

## Features

- **Native Integration**: Add "Print to Phomemo" to the system Print Dialog (PDF Menu).
- **Command Line Interface**: Print images (PNG/JPG) directly from the terminal.
- **Auto-Discovery**: Automatically finds the T02 printer via Bluetooth Low Energy (BLE).
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

### Method 1: Native Print (Recommended)

1. Open any document (PDF, Webpage, Text) in any Mac app.
2. Press **CMD + P** to open the Print Dialog.
3. Click the **PDF** button (usually at the bottom or in a dropdown).
4. Select **"Imprimir na Phomemo"**.
5. The script will convert the document to an image and send it to the printer via Bluetooth.

### Method 2: Command Line

Print an existing image file:

```bash
./venv/bin/python print_phomemo.py image.png
```

Scan for devices/UUIDs (for debugging):

```bash
./venv/bin/python scan_phomemo.py
```

## Technical Details

- **Protocol**: The driver uses ESC/POS-like raster bit image commands (`GS v 0`) sent over BLE.
- **UUIDs**:
  - Service: `ff00`
  - Write Characteristic: `ff02`
- **Conversion**: Uses `PyMuPDF` to render PDF pages and `Pillow` to convert them to 1-bit dithered monochrome images suitable for the thermal head.

## Troubleshooting

- **Printer not found**: The T02 goes to sleep quickly. Turn it OFF and ON again immediately before printing if it fails.
- **Permission Denied**: Ensure `print_to_phomemo.command` has execute permissions (`chmod +x`).

## Status Codes (Dev Notes)

Work in progress for "Paper Out" detection:
- `1a 06 ...` -> Cover Open.
- `1a 05 98 ...` -> No Paper (Cover Closed).

## License

MIT License. Feel free to modify and adapt.
