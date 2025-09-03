[TR](README_tr.md) - [EN](README.md)

# Auto Image Labeler - User Guide

Auto Image Labeler is an application that performs object detection on images, simplifies labeling processes, and helps create datasets in YOLO format.

## Table of Contents

- [Installation](#installation)
- [Main Screen](#main-screen)
- [Image Loading and Navigation](#image-loading-and-navigation)
- [Manual Labeling](#manual-labeling)
- [Automatic Labeling](#automatic-labeling)
- [Saving Annotations](#saving-annotations)
- [Dataset Splitting](#dataset-splitting)

## Installation

1. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Launch the application:
   ```bash
   python main.py
   ```

## Main Screen

The application consists of the following sections:

- **Image Area**: Main area used for viewing and labeling images.
- **Control Panel**: Control buttons and settings located on the right side.
  - Navigation Buttons (Previous/Next)
  - Open Folder
  - Save Annotations
  - Clear Annotations
  - Class Management
  - Model Management
  - Dataset Management
  - Format Selection

## Image Loading and Navigation

1. **Open Folder**: Click the "Open Folder" button to select a folder containing image files.
2. **Navigate Between Images**: 
   - Use "Next" and "Previous" buttons to navigate between images.
   - Alternatively, use right/left arrow keys.

## Manual Labeling

1. **Drawing Rectangles**: 
   - Click and drag with the mouse on the image to draw a new rectangle.
   - Must be at least 5x5 pixels in size.

2. **Editing Rectangles**:
   - Click on an existing rectangle to select it.
   - Drag the selected rectangle with the mouse to move it.
   - Resize by dragging from edges and corners.
   - Delete the selected rectangle with the DELETE key.

3. **Class Management**:
   - Select an existing class from the "Classes" section.
   - Add new classes with the "Add Class" button.
   - Change the class of the selected rectangle with the "Set Class to Selected" button.

## Automatic Labeling

1. **Loading Model**:
   - Click "Open folder" button in the "Model Management" section to select a YOLOv8 model (.pt).
   - Adjust the confidence threshold (default: 0.5).

2. **Labeling**:
   - **Single Image**: Click "Auto label current image" button to perform automatic object detection on the displayed image.
   - **Batch Processing**: Use "Simple Auto label all image" button to automatically label all images in the folder.

## Saving Annotations

1. **Format Selection**:
   - Select your desired format from the "Output Format" section:
     - YOLO Format (class_id, x_center, y_center, width, height) - normalized
     - Standard Format (x, y, width, height, class_id) - pixel values

2. **Saving**:
   - Click "Save Annotations" button to save the annotations.
   - Annotations are saved to a subfolder named "annotations" in the folder containing the images.
   - Class information is stored in "classes.json" file.

## Dataset Splitting

You can split your dataset into train, validation, and test sets for YOLO training:

1. **Setting Ratios**:
   - Set percentage ratios for train, validation, and test from the "Data splitter" section.
   - The sum of ratios must equal 100.

2. **Splitting**:
   - Click the "Split dataset" button.
   - Select the output folder.
   - When the process is complete, it automatically:
     - Creates train, validation, and test subfolders.
     - Creates data.yaml file.
     - Packages the entire dataset as a zip file.

## Shortcuts

- **Right/Left Arrow**: Navigate to next/previous image
- **DELETE**: Delete selected