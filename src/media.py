from dotenv import load_dotenv
from imagekitio import ImageKit
import os


load_dotenv()

imagekit: ImageKit = ImageKit(private_key=os.getenv("IMAGEKIT_PRIVATE_KEY"))

# eosc