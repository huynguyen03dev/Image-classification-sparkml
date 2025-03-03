%pyspark
import os
import boto3
from botocore.client import Config
from PIL import Image
import numpy as np
import tensorflow as tf
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf
from pyspark.sql.types import ArrayType, FloatType
import json

print("=== Starting MinIO Image Training Script (Default UDF Version) ===")

# Configuration for MinIO
print("Configuring MinIO client...")
minio_endpoint = 'http://minio:9000'
minio_access_key = 'minioadmin'
minio_secret_key = 'minioadmin'
bucket_name = 'dev'
local_image_dir = '/tmp/minio_images/'

# Initialize the MinIO client
print("Initializing MinIO client...")
s3 = boto3.client('s3',
                  endpoint_url=minio_endpoint,
                  aws_access_key_id=minio_access_key,
                  aws_secret_access_key=minio_secret_key,
                  config=Config(signature_version='s3v4'))

# Download images preserving folder structure
if not os.path.exists(local_image_dir):
    print("Creating local directory for images:", local_image_dir)
    os.makedirs(local_image_dir)
else:
    print("Local image directory exists:", local_image_dir)

print("Listing and downloading images from MinIO bucket...")
image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
downloaded_files = []  # list to store (local_file_path, label)

list_response = s3.list_objects_v2(Bucket=bucket_name)
if 'Contents' in list_response:
    for obj in list_response['Contents']:
        key = obj['Key']  # e.g., "antelope/27a5369441.jpg"
        if any(key.lower().endswith(ext) for ext in image_extensions):
            print("Downloading image:", key)
            # Construct local file path preserving folder structure
            local_file_path = os.path.join(local_image_dir, key)
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
            s3.download_file(bucket_name, key, local_file_path)
            # Extract label from key (everything before the first "/")
            label = key.split('/')[0] if "/" in key else "unknown"
            downloaded_files.append((local_file_path, label))
else:
    print("No objects found in bucket:", bucket_name)

total_downloaded = len(downloaded_files)
print("Finished downloading images. Total images downloaded:", total_downloaded)

print("Walking local image directory to list images...")
image_data_list = []
for root, dirs, files in os.walk(local_image_dir):
    for file in files:
        if any(file.lower().endswith(ext) for ext in image_extensions):
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, local_image_dir)
            label = rel_path.split(os.sep)[0]
            image_data_list.append((file_path, label))

print("Total image files found (by walking directory):", len(image_data_list))

print("Creating Spark session...")
spark = SparkSession.builder \
    .appName("MinIO Image Training DefaultUDF") \
    .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .getOrCreate()

print("Creating Spark DataFrame with image paths and labels...")
df = spark.createDataFrame(image_data_list, schema=["image_path", "label"]).persist()
df.show(5, truncate=False)

print("Defining image loading function...")
def load_image(file_path):
    try:
        img = Image.open(file_path)
        img = img.resize((128, 128))       # Resize to fixed size
        img = np.array(img)
        print("Loaded image as array with shape:", img.shape, "and dtype:", img.dtype)
        # Ensure image has 3 channels
        if img.ndim == 2: 
            img = np.stack((img,)*3, axis=-1)
        elif img.shape[-1] == 4:  
            img = img[:, :, :3]
        # Confirm shape is (128, 128, 3)
        if img.shape != (128, 128, 3):
            raise ValueError(f"Unexpected image shape: {img.shape}")
        return img.astype("float32") / 255.0   # Normalize
    except Exception as e:
        print(f"Error loading image {file_path}: {e}")
        return np.zeros((128, 128, 3), dtype=np.float32)

print("Defining standard UDF to preprocess images...")
def process_image_udf(path):
    # Load image and flatten the array into a list of floats
    img = load_image(path)
    return img.flatten().tolist()

# Create the UDF specifying that it returns an array of floats
standard_udf = udf(process_image_udf, ArrayType(FloatType()))

print("Applying standard UDF to DataFrame on a small subset...")
debug_df = df.limit(10)
debug_df = debug_df.withColumn("image_data", standard_udf("image_path"))
print("Debug UDF output:")
debug_df.show(truncate=False)