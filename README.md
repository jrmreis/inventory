# Electronic Components Inventory System

A Telegram bot-based inventory management system for electronic components (resistors, capacitors, Arduinos, connectors, etc.) with AI-powered image recognition.

## Features

- **Telegram Bot Interface**: Easy-to-use conversational interface
- **Image Recognition**: Take photos of components for automatic identification
- **OCR + AI**: Reads component labels, resistor color codes, and part numbers
- **Inventory Tracking**: Track quantities, locations, and specifications
- **Search & Reports**: Find components quickly, view inventory status
- **AWS Deployment**: Production-ready infrastructure with Terraform

## Architecture

```
Telegram Bot → Image Processing (OCR) → AI Extraction → Database (Supabase)
                                                       ↓
                                                    Reports
```

## Quick Start

### Prerequisites

- Python 3.11+
- Telegram Bot Token (from @BotFather)
- Supabase account (free tier)
- Groq API key (free tier)
- AWS account (for deployment)

### Local Development

1. **Clone and setup**:
```bash
cd /home/joel/repos/github/Dev/Inventory
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. **Setup database**:
```bash
# Run migrations in Supabase SQL editor
cat migrations/*.sql
```

4. **Run the bot**:
```bash
python main.py
```

### Production Deployment

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for complete AWS deployment instructions.

## Bot Commands

- `/start` - Welcome message and instructions
- `/help` - Show all available commands
- `/add` - Add new component (with photo or manual entry)
- `/search` - Search for components
- `/list` - List all components
- `/status` - Inventory status and statistics
- `/low_stock` - Show components with low quantity
- `/location` - Find components by storage location
- `/myid` - Get your Telegram user ID (for whitelist)
- `/cancel` - Cancel current operation

## Component Types Supported

- Resistors (with color code recognition)
- Capacitors
- Microcontrollers (Arduino, ESP32, STM32, etc.)
- Connectors (headers, JST, USB, etc.)
- ICs (integrated circuits)
- LEDs and displays
- Sensors
- Power supplies and modules
- Custom components

## Project Structure

```
Inventory/
├── app/
│   ├── __init__.py
│   ├── bot.py                 # Main bot logic
│   ├── image_processor.py     # OCR and image processing
│   ├── data_extractor.py      # AI-powered data extraction
│   └── component_classifier.py # Component type detection
├── migrations/
│   ├── 001_create_components_table.sql
│   └── 002_create_views.sql
├── terraform/
│   ├── main.tf               # Provider configuration
│   ├── ecs.tf                # ECS cluster and service
│   ├── secrets.tf            # AWS Secrets Manager
│   ├── cloudwatch.tf         # Logging
│   └── github-oidc.tf        # CI/CD authentication
├── .github/
│   └── workflows/
│       └── deploy.yml        # CI/CD pipeline
├── main.py                   # Application entry point
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

## Technology Stack

- **Backend**: Python 3.11
- **Bot Framework**: python-telegram-bot
- **Database**: Supabase (PostgreSQL)
- **Image Recognition**: Tesseract OCR + OpenCV
- **AI**: Groq (Llama 3.3 70B)
- **Infrastructure**: AWS ECS Fargate
- **IaC**: Terraform
- **CI/CD**: GitHub Actions

## Security

- User whitelist authentication
- AWS Secrets Manager for credentials
- OIDC authentication for CI/CD (no long-term keys)
- Encrypted database connections

## License

MIT License - See LICENSE file

## Support

For issues and questions, please open an issue on GitHub.
