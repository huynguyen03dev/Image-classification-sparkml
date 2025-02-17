# Dự án Phân loại Ảnh Các Loài Động Vật

## Mô tả
Dự án này nhằm xây dựng một hệ thống phân loại ảnh các loài động vật sử dụng SparkML.  
- Dataset: Ảnh các loài động vật được tải từ Kaggle, lưu trữ trong HDFS theo cấu trúc thư mục (mỗi folder tên là tên loài).  
- Kiến trúc cluster:  
  - Node 1: Hadoop NameNode & DataNode, Spark Master, Zeppelin  
  - Node 2: Hadoop DataNode, Spark Worker  
  - Node 3: Hadoop DataNode, Spark Worker  
- Công nghệ: Docker, Docker Compose, Hadoop, Spark, Apache Zeppelin, SparkML (MLlib).

## Cách chạy dự án

1. Cài đặt Docker và Docker Compose.

2. Copy file `docker-compose.yml` vào thư mục dự án.

3. Chạy lệnh sau để build và khởi động cluster: