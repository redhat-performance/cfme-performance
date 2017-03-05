### Indexing data in ElasticSearch

1. (Optional) cleanup old data:
   ```
   curl -XDELETE http://admin:admin@10.12.23.122:9201/cfme-*
   ```

2. (Optional) cleanup old templates:

   ```
   curl -XDELETE http://admin:admin@10.12.23.122:9201/_template/cfme*
   ```

3. Create new templates:

   ```
   ./es-create-cfme-templates
   ```

4. Index data as follows:

   ```
   ./postprocess/cfme_csv2elastic.py ../results/20170105161527-workload-cap-and-util-5.7.0.1/
   ```
