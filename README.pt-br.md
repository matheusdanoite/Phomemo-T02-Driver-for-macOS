# Driver Phomemo T02 para macOS (Python)

[English](README.md)

Um driver simples com o intuito de integrar a impressora térmica Phomemo T02 no macOS.

Este projeto permite que você imprima na sua Phomemo T02 diretamente do macOS sem usar o aplicativo móvel oficial. Ele inclui um script Python para impressão via linha de comando e uma integração de **Serviço de PDF para Mac**, adicionando uma opção "Imprimir na Phomemo" ao diálogo nativo CMD+P em qualquer aplicativo (Chrome, Pages, Preview, etc.).

## Funcionalidades
- **Integração Nativa**: Adiciona "Imprimir na Phomemo" ao Diálogo de Impressão do sistema (Menu PDF).
- **Interface de Linha de Comando**: Imprima imagens (PNG/JPG) diretamente do terminal.
- **Impressão Automática (Monitor de Pasta)**: Imprime automaticamente qualquer imagem ou PDF solto em uma pasta específica.
- **Conexão Persistente**: Mantém uma conexão constante Bluetooth para impressão mais rápida e recuperação automática.
- **Redimensionamento Inteligente**: Redimensiona automaticamente imagens e PDFs para caber na largura de impressão de 48mm (384 pontos).

## Pré-requisitos
- **Hardware**: Impressora Phomemo T02.
- **SO**: macOS (testado em Sonoma/Sequoia via `bleak`).
- **Software**: Python 3.10+.

## Instalação
1. **Clone ou Baixe este repositório**:
   ```bash
   git clone https://github.com/matheusdanoite/Phomemo-T02-Driver-for-macOS.git
   cd Phomemo-T02-Driver-for-macOS
   ```
2. **Configure o Ambiente Python**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Instale a Integração do Menu Nativo** (Opcional):
   Isso cria um alias na pasta de Serviços de PDF do seu usuário, fazendo com que a opção apareça no menu de impressão.
   ```bash
   # Certifique-se de que o wrapper seja executável
   chmod +x print_to_phomemo.command
   
   # Crie o link (Substitua /path/to/project pelo caminho real se movido)
   mkdir -p ~/Library/PDF\ Services
   ln -s "$(pwd)/print_to_phomemo.command" ~/Library/PDF\ Services/Imprimir\ na\ Phomemo
   ```

## Uso
### Método 1: Impressão Automática (Recomendado)
Execute o script sem argumentos para iniciar o **Modo Monitor**:
```bash
./venv/bin/python print_phomemo.py
```
- **Pasta**: Solte arquivos (`.png`, `.jpg`, `.pdf`) na pasta `print_queue/`.
- **Histórico**: Arquivos impressos são movidos para `print_queue/processed/`.
- **Fique Conectado**: O script permanece conectado à impressora, garantindo impressão quase instantânea de novos itens.

### Método 2: Impressão Nativa (Diálogo do Sistema)
1. Abra qualquer documento em qualquer aplicativo Mac.
2. Pressione **CMD + P** para abrir o Diálogo de Impressão.
3. Clique no botão **PDF** -> Selecione **"Imprimir na Phomemo"**.

### Método 3: Linha de Comando (Uso único)
Imprima uma imagem ou arquivo PDF existente diretamente:
```bash
./venv/bin/python print_phomemo.py image.png
```
Escaneie por dispositivos/UUIDs:
```bash
./venv/bin/python scan_phomemo.py
```

## Detalhes Técnicos
- **Protocolo**: O driver usa comandos de imagem raster estilo ESC/POS (`GS v 0`) enviados via BLE.
- **UUIDs**:
  - Serviço: `ff00`
  - Característica de Escrita: `ff02`
- **Conversão**: Usa `PyMuPDF` para renderizar páginas PDF e `Pillow` para convertê-las em imagens monocromáticas pontilhadas de 1 bit adequadas para a cabeça térmica.

## Códigos de Status (Notas de Dev)
A impressora envia pacotes de notificação de 3 bytes (Prefixo `1a`) para o UUID `ff03`.
O Byte 2 (Índice 2) contém os bits de status:
- **Bit 0**: `1` = Tampa Aberta, `0` = Tampa Fechada.
- **Bit 4**: `1` = Papel Presente, `0` = Papel Ausente.

**Exemplos:**
- `1a 05 99` -> Tampa Aberta (153 = `1001 1001`)
- `1a 05 98` -> Tampa Fechada + Papel OK (152 = `1001 1000`)
- `1a 06 88` -> Tampa Fechada + Papel Ausente (136 = `1000 1000`)

Mais uma coisa feita por matheusdanoite.
