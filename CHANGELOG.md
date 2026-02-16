# Changelog

## [1.0.0] - 2026-02-16
### Added
- Initial release of the Phomemo T02 macOS Driver.
- **Native Integration**: "Print to Phomemo" option added to the macOS Print Dialog (PDF Services).
- **Command Line Interface**: Support for printing PNG and JPG images directly from the terminal.
- **Folder Monitor**: Automatic printing of files dropped into the `print_queue/` directory.
- **Smart Resizing**: Automatic scaling of images and PDFs to fit the 48mm print width.
- **Bluetooth Connectivity**: Persistent BLE connection using `bleak` for fast printing and auto-recovery.
- Image processing pipeline using `Pillow` for dithering and `PyMuPDF` for PDF rendering.
