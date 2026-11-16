import numpy as np
from PIL import Image

photo = Image.open("photo.png").convert("RGB")
colour = np.asarray(photo)
grey = np.asarray(photo.convert("L"))

print("photo size (width, height):", photo.size)
print("colour array shape:", colour.shape)
print("grey array shape:", grey.shape)
print("top-left pixel in colour:", colour[0, 0])
print("top-left pixel in grey:", grey[0, 0])
print("darkest and lightest grey:", grey.min(), grey.max())
