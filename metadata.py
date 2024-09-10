import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import piexif
import torch
from torchvision import models, transforms
import requests
import json

class ImageMetadataExtractor:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("EXIF Metadata Extractor")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        self.root.configure(bg='#f0f0f0')

        self.model = models.resnet18(pretrained=True)
        self.model.eval()

        self.preprocess = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        self.label_descriptions = self.load_label_descriptions()

        self.google_maps_api_key = 'api_key'

        self.create_widgets()

    def load_label_descriptions(self):
        url = 'https://raw.githubusercontent.com/anishathalye/imagenet-simple-labels/master/imagenet-simple-labels.json'
        response = requests.get(url)
        return json.loads(response.text)

    def create_widgets(self):
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.image_frame = tk.Frame(main_frame, bg='#ffffff', relief=tk.RAISED, borderwidth=2)
        self.image_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.metadata_frame = tk.Frame(main_frame, bg='#ffffff', relief=tk.RAISED, borderwidth=2)
        self.metadata_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.image_label = tk.Label(self.image_frame, text="Image Preview", font=("Arial", 16, 'bold'), bg='#ffffff')
        self.image_label.pack(pady=5)

        self.image_display = tk.Label(self.image_frame, bg="gray", width=60, height=40, relief=tk.SUNKEN)
        self.image_display.pack(fill=tk.BOTH, expand=True)
        self.image_display.bind("<Button-1>", self.show_large_image)

        self.text_output = scrolledtext.ScrolledText(self.metadata_frame, width=60, height=30, wrap=tk.WORD, font=("Arial", 12))
        self.text_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        button_frame = tk.Frame(self.metadata_frame, bg='#ffffff')
        button_frame.pack(pady=10)

        self.open_button = tk.Button(button_frame, text="Select Image File", font=("Arial", 12), width=20, bg='#4CAF50', fg='#ffffff', command=self.open_file_dialog)
        self.open_button.grid(row=0, column=0, padx=5, pady=5)

        self.save_button = tk.Button(button_frame, text="Save Metadata", font=("Arial", 12), width=20, bg='#2196F3', fg='#ffffff', command=self.save_metadata, state='disabled')
        self.save_button.grid(row=0, column=1, padx=5, pady=5)

        self.large_image_window = None
        self.large_image = None

    def open_file_dialog(self):
        file_path = filedialog.askopenfilename(
            title="Select an image file",
            filetypes=[("Image files", "*.jpg;*.jpeg;*.png;*.tiff;*.bmp")]
        )
        if file_path:
            self.display_image(file_path)
            metadata = self.get_image_metadata(file_path)
            interpreted_data = self.interpret_metadata(metadata)
            analysis = self.analyze_image(file_path)
            self.display_metadata(interpreted_data, analysis)

    def display_image(self, image_path):
        try:
            img = Image.open(image_path)
            img.thumbnail((800, 600))
            img_tk = ImageTk.PhotoImage(img)
            self.image_display.config(image=img_tk)
            self.image_display.image = img_tk
            self.large_image_path = image_path
        except Exception as e:
            messagebox.showerror("Error", f"Error loading image: {e}")

    def show_large_image(self, event):
        if self.large_image_window is None:
            self.large_image_window = tk.Toplevel(self.root)
            self.large_image_window.title("Large Image Preview")
            self.large_image_window.geometry("1200x900")

            try:
                img = Image.open(self.large_image_path)
                img_tk = ImageTk.PhotoImage(img)
                self.large_image = tk.Label(self.large_image_window, image=img_tk)
                self.large_image.pack(fill=tk.BOTH, expand=True)
                self.large_image.image = img_tk
            except Exception as e:
                messagebox.showerror("Error", f"Error loading large image: {e}")

    def get_image_metadata(self, image_path):
        try:
            img = Image.open(image_path)
            exif_data = img.info.get('exif')
            if exif_data:
                return piexif.load(exif_data)
        except (FileNotFoundError, OSError) as e:
            messagebox.showerror("Error", f"Error loading image file: {e}")
        return None

    def convert_gps_coordinates(self, gps_data):
        def to_degrees(value):
            degrees = value[0][0] / value[0][1]
            minutes = value[1][0] / value[1][1] / 60.0
            seconds = value[2][0] / value[2][1] / 3600.0
            return degrees + minutes + seconds

        lat = to_degrees(gps_data[piexif.GPSIFD.GPSLatitude])
        lat_ref = gps_data[piexif.GPSIFD.GPSLatitudeRef].decode('utf-8')
        lon = to_degrees(gps_data[piexif.GPSIFD.GPSLongitude])
        lon_ref = gps_data[piexif.GPSIFD.GPSLongitudeRef].decode('utf-8')

        if lat_ref != "N":
            lat = -lat
        if lon_ref != "E":
            lon = -lon

        return lat, lon

    def get_location_from_gps(self, lat, lon):
        try:
            url = f'https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&key={self.google_maps_api_key}'
            response = requests.get(url)
            data = response.json()
            if data['status'] == 'OK':
                results = data['results']
                if results:
                    address = results[0].get('formatted_address', 'Address not found')
                    return address
            return 'Location not found'
        except Exception as e:
            return f'Error occurred: {e}'

    def interpret_metadata(self, metadata):
        if not metadata:
            return {"Error": "No EXIF data found in this image."}

        interpreted_data = {}

        camera_make = metadata["0th"].get(piexif.ImageIFD.Make, b'').decode('utf-8', 'ignore')
        camera_model = metadata["0th"].get(piexif.ImageIFD.Model, b'').decode('utf-8', 'ignore')
        interpreted_data[
            'Camera'] = f"{camera_make} {camera_model}" if camera_make and camera_model else "Unknown camera"

        datetime = metadata["0th"].get(piexif.ImageIFD.DateTime, b'').decode('utf-8', 'ignore')
        interpreted_data['Date Taken'] = datetime if datetime else "Date taken unknown"

        gps_info = metadata.get('GPS', None)
        if gps_info:
            try:
                lat, lon = self.convert_gps_coordinates(gps_info)
                location = self.get_location_from_gps(lat, lon)
                interpreted_data['GPS Location'] = f"Latitude: {lat}, Longitude: {lon}\nLocation: {location}"
            except (KeyError, IndexError):
                interpreted_data['GPS Location'] = "GPS information not found"
        else:
            interpreted_data['GPS Location'] = "GPS information not found"

        return interpreted_data

    def analyze_image(self, image_path):
        try:
            img = Image.open(image_path)
            img = self.preprocess(img)
            img = img.unsqueeze(0)
            with torch.no_grad():
                outputs = self.model(img)
                topk_prob, topk_indices = torch.topk(outputs, 5)
                results = []
                for prob, idx in zip(topk_prob[0], topk_indices[0]):
                    label = str(idx.item())
                    description = self.label_descriptions[int(label)] if int(label) < len(self.label_descriptions) else label
                    results.append({'label': description, 'score': prob.item()})
                return results
        except Exception as e:
            messagebox.showerror("Error", f"Error occurred during image analysis: {e}")
        return None

    def display_metadata(self, metadata, analysis):
        self.text_output.delete(1.0, tk.END)
        self.text_output.insert(tk.END, "EXIF Metadata:\n")
        for key, value in metadata.items():
            self.text_output.insert(tk.END, f"{key}: {value}\n")

        self.text_output.insert(tk.END, "\nAI Analysis:\n")
        if analysis:
            for result in analysis:
                self.text_output.insert(tk.END, f"Label: {result['label']}, Confidence Score: {result['score']:.2f}\n")
        else:
            self.text_output.insert(tk.END, "No analysis results found.")

        self.save_button.config(state='normal')

    def save_metadata(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(self.text_output.get(1.0, tk.END))
                messagebox.showinfo("Success", "Metadata successfully saved.")
            except Exception as e:
                messagebox.showerror("Error", f"Error occurred while saving the file: {e}")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    extractor = ImageMetadataExtractor()
    extractor.run()
