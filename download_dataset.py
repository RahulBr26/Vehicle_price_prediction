import kagglehub
import shutil
import os


# Download dataset
path = kagglehub.dataset_download(
    "bhavikjikadara/car-price-prediction-dataset"
)

print("Downloaded path:")
print(path)


# Source CSV
source = os.path.join(
    path,
    "car_prediction_data.csv"
)


# Destination folder
os.makedirs("dataset", exist_ok=True)


destination = "dataset/car_prediction_data.csv"


# Copy CSV into project
shutil.copy(source, destination)


print("CSV copied successfully!")
print(destination)