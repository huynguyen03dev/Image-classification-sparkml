# ...existing content...

## Uploading Data to HDFS via Docker
1. List Docker containers:
   ```
   docker ps
   ```
2. Identify the container running the NameNode (e.g. "my-namenode").
3. Access the container:
   ```
   docker exec -it my-namenode bash
   ```
4. Upload data to HDFS:
   ```
   hadoop fs -mkdir -p /data/animal_images
   hadoop fs -put /local/path/to/images/* /data/animal_images/
   ```
5. Verify the files in HDFS:
   ```
   hadoop fs -ls /data/animal_images/
   ```
