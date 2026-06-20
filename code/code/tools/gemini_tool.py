import os
import time
import logging
from PIL import Image
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass
import google.generativeai as genai
from config import Config
from tools.validators import VLMAnalysis

# Setup logging
logger = logging.getLogger(__name__)

class GeminiTool:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or Config.get_api_key()
        genai.configure(api_key=self.api_key)
        
    def resize_image(self, img: Image.Image, max_size: int = 1024) -> Image.Image:
        """
        Resizes the image if its width or height exceeds max_size, maintaining aspect ratio.
        """
        w, h = img.size
        if w > max_size or h > max_size:
            if w > h:
                new_w = max_size
                new_h = int(h * (max_size / w))
            else:
                new_h = max_size
                new_w = int(w * (max_size / h))
            logger.info(f"Resizing image from {w}x{h} to {new_w}x{new_h}")
            return img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        return img

    def load_and_preprocess_images(self, image_paths: list, dataset_root: str = "dataset") -> list:
        """
        Loads images from the given paths, converts them to RGB, and resizes them.
        Handles missing or corrupted images by raising an exception.
        """
        images = []
        for path_str in image_paths:
            path_str = path_str.strip()
            if not path_str:
                continue
            
            if path_str.startswith("dataset/"):
                full_path = os.path.abspath(path_str)
            else:
                full_path = os.path.abspath(os.path.join(dataset_root, path_str))
                
            if not os.path.exists(full_path):
                raise FileNotFoundError(f"Image file not found: {full_path}")
                
            try:
                img = Image.open(full_path)
                img.load()  # Force load image data to catch corruption early
                img_rgb = img.convert("RGB")
                img_resized = self.resize_image(img_rgb)
                images.append(img_resized)
            except Exception as e:
                raise IOError(f"Failed to load or parse image {full_path}: {e}")
                
        return images

    def call_gemini_vision(
        self,
        prompt: str, 
        images: list, 
        model_name: str = Config.DEFAULT_MODEL
    ) -> VLMAnalysis:
        """
        Sends the prompt and images to the Gemini VLM and requests a structured JSON output.
        Implements retry logic with exponential backoff on failure.
        """
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=VLMAnalysis,
                temperature=Config.TEMPERATURE
            )
        )
        
        contents = [prompt]
        contents.extend(images)
        
        max_retries = Config.MAX_RETRIES
        for attempt in range(max_retries):
            try:
                logger.info(f"Calling VLM model {model_name} (Attempt {attempt+1}/{max_retries})...")
                response = model.generate_content(contents)
                response_text = response.text
                logger.info("VLM call completed successfully.")
                analysis = VLMAnalysis.model_validate_json(response_text)
                return analysis
            except Exception as e:
                logger.error(f"Error on attempt {attempt+1} calling VLM: {e}")
                if attempt < max_retries - 1:
                    sleep_time = 2 ** (attempt + 1)
                    logger.info(f"Sleeping for {sleep_time} seconds before retrying...")
                    time.sleep(sleep_time)
                else:
                    raise e
