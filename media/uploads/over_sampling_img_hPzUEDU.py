import matplotlib.pyplot as plt
import pathlib
from google.colab import drive
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import os
import random

# Mount Google Drive
drive.mount('/content/drive')

#path to data
data_dir = pathlib.Path("/content/drive/MyDrive/data/Train")

# output directory to save augmented images
output_dir = pathlib.Path("/content/drive/MyDrive/data/newdata")
output_dir.mkdir(parents=True, exist_ok=True)

datagen = ImageDataGenerator(
    rotation_range=10,
    width_shift_range=0.1,
    height_shift_range=0.1,
    shear_range=0.1,
    zoom_range=0.1,
    horizontal_flip=True,
    fill_mode='nearest',
    rescale=1/255.0  # Rescale pixel values to [0, 1]
)

# Define classes to oversample
classes_to_oversample = [item.name for item in data_dir.glob('*') if item.is_dir()]

# Sample a fixed number of augmented images for each class
num_samples_per_class =  max(len(list((data_dir / cls).glob('*.jpg'))) for cls in classes_to_oversample)

# Loop through each class and oversample
for class_to_oversample in classes_to_oversample:
    # Create directory to save augmented images for current class
    class_output_dir = output_dir / class_to_oversample
    class_output_dir.mkdir(parents=True, exist_ok=True)

    # Loop through the selected class folder
    class_dir = data_dir / class_to_oversample
    images = list(class_dir.glob('*.jpg'))  # images are in jpg format, adjust if necessary

    # Randomly select images with replacement until we reach num_samples_per_class
    for i in range(num_samples_per_class):
        # Randomly select an image
        random_image_path = random.choice(images)
        image = plt.imread(str(random_image_path))  # Load image
        image = image.reshape((1,) + image.shape)  # Add batch dimension
        output_image_path = class_output_dir / f"augmented_{i}.jpg"  # Output path for augmented image

        # Generate and save augmented image
        for batch in datagen.flow(image, batch_size=1):
            augmented_image = batch[0]
            plt.imsave(output_image_path, augmented_image)
            break  # Exit loop after saving one augmented image