#!/usr/bin/env python
"""
Ví dụ Spark job sử dụng SparkML để phân loại ảnh các loài động vật
Giả định dataset đã được copy vào HDFS tại đường dẫn /data/animal_images
với cấu trúc thư mục:
  /data/animal_images/
      con_meo/
      con_chien/
      con_voi/
      ...
Mỗi thư mục tên theo loài, chứa các file ảnh.
"""
from pyspark.sql import SparkSession
from pyspark.ml import Pipeline
from pyspark.ml.classification import LogisticRegression  # ví dụ dùng mô hình logistic regression
from pyspark.sql.functions import udf, col
from pyspark.sql.types import StringType
import os

def extract_label(file_path):
    # Giả sử file_path có cấu trúc /data/animal_images/ten_loai/ten_file.jpg
    parts = file_path.split(os.sep)
    # Lấy phần tên folder chứa ảnh
    try:
        # Giả sử folder ảnh nằm ngay sau thư mục animal_images
        label = parts[parts.index("animal_images") + 1]
    except Exception as e:
        label = "unknown"
    return label

# Khởi tạo SparkSession
spark = SparkSession.builder.appName("AnimalImageClassification").getOrCreate()
spark.sparkContext.setLogLevel("WARN")

# Đọc ảnh từ HDFS (Spark hỗ trợ đọc định dạng ảnh nếu cài đặt package spark-image)
# Nếu không có package, bạn có thể load danh sách file và xử lý bằng UDF
df_images = spark.read.format("image").load("hdfs://namenode:9000/data/animal_images/")

# Tạo cột label từ file path
extract_label_udf = udf(extract_label, StringType())
df_images = df_images.withColumn("label", extract_label_udf(col("image.origin")))

df_images.show(5, truncate=50)

# Ở đây bạn sẽ cần chuyển đổi dữ liệu ảnh thành vector đặc trưng (feature vector)
# Ví dụ: tính histogram màu, hay dùng một model pre-trained để trích xuất feature.
# Đơn giản ta giả định đã có cột "features" (vector) sau quá trình xử lý.
# Sau đó tạo pipeline SparkML, ví dụ với Logistic Regression:
from pyspark.ml.feature import StringIndexer, VectorAssembler
from pyspark.ml.evaluation import MulticlassClassificationEvaluator

# Giả sử có cột "features" đã tồn tại, ví dụ ta dùng một VectorAssembler giả lập
assembler = VectorAssembler(inputCols=["dummy_feature"], outputCol="features")
# Tạo cột dummy_feature từ chiều cao ảnh (vd chỉ để minh họa)
from pyspark.sql.functions import lit
df_images = df_images.withColumn("dummy_feature", lit(1.0))

# Chuyển label thành số
indexer = StringIndexer(inputCol="label", outputCol="labelIndex")

# Mô hình phân loại
lr = LogisticRegression(featuresCol="features", labelCol="labelIndex", maxIter=10)

# Xây dựng pipeline
pipeline = Pipeline(stages=[assembler, indexer, lr])

# Huấn luyện mô hình
model = pipeline.fit(df_images)
predictions = model.transform(df_images)

# Đánh giá
evaluator = MulticlassClassificationEvaluator(labelCol="labelIndex", predictionCol="prediction", metricName="accuracy")
accuracy = evaluator.evaluate(predictions)
print(f"Accuracy = {accuracy}")

spark.stop()