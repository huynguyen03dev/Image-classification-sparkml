from minio import Minio
import os

client = Minio(endpoint="localhost:9000",
               access_key="minioadmin",
               secret_key="minioadmin",
               secure=False)

bucket_name = "dev"
image_dir = "data/animal_images"

# Ensure the bucket exists
if not client.bucket_exists(bucket_name):
    client.make_bucket(bucket_name)

# Upload images
for root, dirs, files in os.walk(image_dir):
    for file in files:
        if file.endswith(('.jpg', '.jpeg', '.png')):
            folder_name = os.path.basename(root)
            file_path = os.path.join(root, file)
            object_name = f"{folder_name}/{file}"
            client.fput_object(bucket_name, object_name, file_path)
            print(f"Uploaded {file_path} as {object_name} to bucket {bucket_name}")