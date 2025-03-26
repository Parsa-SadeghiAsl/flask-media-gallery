# Media Gallery

A simple web gallery application that displays and allows downloading of media files from a local directory.

## Features

- View media files in a responsive grid layout
- Download media files
- Support for common image formats (PNG, JPG, JPEG, GIF) and video formats (MP4, WEBM, MOV)
- Modern and responsive UI

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `data` folder in the project root and add your media files:
```bash
mkdir data
# Copy your media files into the Data folder
```

4. Run the application:
```bash
python app.py
```

5. Open your web browser and navigate to `http://localhost:5000`

## Usage

1. Place your media files in the `data` folder
2. View your media files in the grid layout
3. Download files by clicking the "Download" button on any media item

## Directory Structure

- `data/` - Directory containing your media files
- `templates/` - Contains the HTML templates

## Supported File Types

- Images: PNG, JPG, JPEG, GIF
- Videos: MP4, WEBM, MOV