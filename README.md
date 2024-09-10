# EXIF Metadata Extractor

EXIF Metadata Extractor is a Python application that can view and analyze EXIF metadata information of image files. It also makes place name prediction using GPS data from images and analyzes the tags of images with artificial intelligence.

## Features

- View EXIF metadata information (camera information, shooting date, GPS data, etc.).
- Small preview and large preview of images.
- Estimating place names using GPS data from images.
- Analyze tags of images with artificial intelligence.
- Save metadata information to a file.

## Requirements

- Python 3.6 or higher
- Pillow
- piexif
- torch
- torchvision
- requests
- json

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/KuGuVeGaa/MetaData_View.git
    cd MetaData_View
    ```

2. Install the necessary Python packages:
    ```bash
    pip install pillowxif torch torchvision requests
    ```

3. Take your Google Maps Geocoding API key and add it to the `self.google_maps_api_key` variable in the `ImageMetadataExtractor` class:
    ```python
    self.google_maps_api_key = 'api_key'
    ```

## Usage

1. Run the application:
    ```bash
    python metadata.py
    ```

2. When the application opens, select an image file by clicking on the “Select Image File” button.

3. The selected image file's EXIF metadata information, small and large previews, AI analysis results will be displayed in the GUI.

4. You can save the metadata information to a file by clicking on the “Save Metadata” button.


