# MemeSmithy Bot

![License](https://img.shields.io/badge/license-AGPL--3.0-blue)
![Python](https://img.shields.io/badge/python-3.14+-blue)

An AI-powered Discord bot that generates memes on demand. Simply describe what you want, and the bot will create a custom meme using its collection of templates.

## Features

- **`/generate`** - Generate memes with AI-powered captions using any template
- **`/templates`** - Browse all available meme templates (paginated, 10 per page)
- **`/template`** - View a specific template with its description and preview
- **`/search`** - Search for templates by keyword in names and descriptions

## Prerequisites

- Python 3.14 or higher
- A Discord bot token ([how to create one](https://discord.com/developers/applications))
- An API key for AI caption generation
- [uv](https://github.com/astral-sh/uv) package manager (recommended) or pip

## Installation

### Option 1: Using uv (Recommended)

1. Install [uv](https://github.com/astral-sh/uv) if you haven't already:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Clone the repository:
   ```bash
   git clone <repository-url>
   cd memesmithy-bot
   ```

3. Install dependencies:
   ```bash
   uv sync
   ```

4. Download template images:
   ```bash
   uv run python main.py download_images
   ```

### Option 2: Using pip

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd memesmithy-bot
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .
   ```

3. Download template images:
   ```bash
   python main.py download_images
   ```

### Option 3: Docker

1. Build the Docker image:
   ```bash
   docker build -t memesmithy-bot .
   ```

2. Run the container:
   ```bash
   docker run -e DISCORD_TOKEN=your_token_here -e GROQ_API_KEY=your_api_key_here memesmithy-bot
   ```

   Or use a `.env` file:
   ```bash
   docker run --env-file .env memesmithy-bot
   ```

## Configuration

Create a `.env` file in the project root with the following variables:

```env
DISCORD_TOKEN=your_discord_bot_token_here
GROQ_API_KEY=your_api_key_here
```

**Required environment variables:**
- `DISCORD_TOKEN` or `BOT_TOKEN` - Your Discord bot token
- `GROQ_API_KEY` - Your API key for AI caption generation

The bot will automatically load these from the `.env` file when it starts.

## Usage

### Starting the Bot

Once configured, start the bot with:

```bash
# With uv
uv run python bot.py

# With pip/virtual environment
python bot.py
```

You should see a confirmation message when the bot connects to Discord successfully.

### Using Discord Commands

Once the bot is running in your Discord server:

- **Generate a meme**: `/generate prompt:"a cat complaining about Monday"`  
  Optionally specify a template: `/generate prompt:"funny situation" template_id:"template-id-here"`

- **Browse templates**: `/templates` or `/templates page:2` for pagination

- **View a template**: `/template template_id:"template-id-here"`

- **Search templates**: `/search keyword:"drake"`

## Project Structure

For contributors interested in the codebase structure:

```
memesmithy-bot/
├── bot.py              # Main bot entry point
├── main.py             # CLI tool for downloading template images
├── cogs/
│   └── memes.py        # Discord slash commands implementation
├── lib/
│   ├── generate.py    # AI caption generation
│   ├── img.py         # Image rendering and text overlay
│   └── templates.py   # Template loading and searching
├── images/             # Downloaded template images
├── fonts/              # Font files (arial.ttf, impact.ttf)
├── templates.csv       # Template database
└── pyproject.toml      # Project dependencies and configuration
```

## Contributing

Contributions are welcome! Here's how to get started:

### Development Setup

1. Fork the repository and clone your fork
2. Set up the development environment:
   ```bash
   uv sync --dev
   ```

3. Install pre-commit hooks (optional but recommended):
   ```bash
   uv run ruff check .
   ```

### Code Style

This project uses [ruff](https://github.com/astral-sh/ruff) for linting and formatting. Please ensure your code follows the project's style:

```bash
# Check for issues
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .
```

### Adding New Templates

Templates are stored in `templates.csv`. To add a new template:

1. Add a row to `templates.csv` with the following columns:
   - `id` - Unique identifier (UUID recommended)
   - `name` - Template name
   - `description` - Template description
   - `image_url` - URL to the template image
   - `prompt` - Instructions for how to use this template
   - `boxes` - JSON array defining text box positions: `[{"x": 10, "y": 10, "w": 200, "h": 50, "font": "impact", ...}]`
   - Other optional fields: `width`, `height`, `public`, etc.

2. Download the template image:
   ```bash
   python main.py download_images
   ```

### Pull Request Process

1. Create a feature branch from `main`
2. Make your changes and ensure code passes linting
3. Test your changes locally
4. Submit a pull request with a clear description of your changes

## Technical Details

### Architecture

The bot is built using:
- **nextcord** - Discord bot framework
- **Groq API** - For AI-powered caption generation
- **Pillow (PIL)** - Image manipulation and text rendering
- **Pydantic** - Data validation and template models
- **python-dotenv** - Environment variable management

### How Meme Generation Works

1. **User Input**: The user provides a prompt via the `/generate` command
2. **Template Selection**: Either a specific template ID is provided, or a random template is selected
3. **Caption Generation**: The bot uses the Groq API (with `openai/gpt-oss-20b` model) to generate appropriate captions based on:
   - The template's prompt instructions
   - The user's input
   - The template's text box configuration
4. **Image Rendering**: The generated captions are overlaid onto the template image using Pillow:
   - Text is automatically sized to fit within defined boxes
   - Supports multiple fonts (Arial, Impact) with automatic styling
   - Text is centered within each box
   - Optional watermark can be added
5. **Output**: The final meme image is sent to Discord

### Template Format

Templates are defined in `templates.csv` with the following structure:

- **Basic fields**: `id`, `name`, `description`, `image_url`
- **Boxes**: JSON array defining where text should be placed. Each box object contains:
  - `x`, `y`, `w`, `h` - Position and dimensions
  - `font` - Font name (`"arial"` or `"impact"`)
  - `fontsize` (optional) - Specific font size, or auto-sized if omitted
  - `color` (optional) - Text color (defaults based on font)
  - `border` (optional) - Stroke/border color for text

Example box definition:
```json
[{"x": 10, "y": 10, "w": 400, "h": 100, "font": "impact"}]
```

### Image Generation Pipeline

The image generation process in `lib/img.py`:

1. Loads the template image from the `images/` directory
2. Parses the boxes JSON configuration
3. For each text box:
   - Determines optimal font size (binary search algorithm)
   - Wraps text to fit within box dimensions
   - Centers text both horizontally and vertically
   - Applies font styling (color, stroke/border)
4. Optionally adds a watermark in the bottom-left corner
5. Returns the final PIL Image object

Font handling supports automatic sizing, text wrapping, and proper centering within defined text boxes.

## License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0). See the [LICENSE](LICENSE) file for details.

## Support & Troubleshooting

### Common Issues

**Bot doesn't start:**
- Ensure `DISCORD_TOKEN` or `BOT_TOKEN` is set in your `.env` file
- Check that `GROQ_API_KEY` is set
- Verify Python version is 3.14 or higher

**"No templates found" error:**
- Make sure `templates.csv` exists and has valid entries
- Run `python main.py download_images` to download template images

**Template images not showing:**
- Ensure the `images/` directory exists
- Run `python main.py download_images` to fetch images from URLs
- Check that template IDs match between CSV and image filenames

**Meme generation fails:**
- Verify your API key is valid and has sufficient credits/quota
- Check that the template has valid box definitions in the `boxes` field
- Ensure font files exist in the `fonts/` directory

For additional help, please open an issue on GitHub.
