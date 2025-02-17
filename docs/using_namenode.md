# Using the NameNode Container

1. List files in HDFS:
   ```
   hadoop fs -ls /
   ```
2. Create a directory in HDFS:
   ```
   hadoop fs -mkdir /data/animal_images
   ```
3. Upload data to HDFS:
   ```
   hadoop fs -put /data/animal_images/* /data/animal_images/
   ```
4. Verify the files:
   ```
   hadoop fs -ls /data/animal_images/
   ```
