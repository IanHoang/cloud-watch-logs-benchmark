# CloudWatch Logs Benchmark Extension

Benchmark CloudWatch Logs alongside OpenSearch using OpenSearch Benchmark.

## Prerequisites

- Python 3.8+
- OpenSearch Benchmark installed (`pip install opensearch-benchmark`)
- AWS credentials configured
- CloudWatch Logs permissions: `StartQuery`, `GetQueryResults`, `CreateLogGroup`, `CreateLogStream`, `PutLogEvents`

## Setup

1. **Install dependencies**
   ```bash
   pip install aioboto3 boto3 tqdm
   ```

2. **Configure AWS credentials**
   ```bash
   aws configure
   # OR export AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
   ```

3. **Ingest test data to CloudWatch**
   ```bash
   python ingest_data.py your-data.json --log-group /benchmark/test
   ```

## Usage

### Ingest Data
```bash
# Basic ingestion
python ingest_data.py data.jsonl --log-group /benchmark/big5

# With custom stream and region
python ingest_data.py data.json \
  --log-group /benchmark/test \
  --log-stream my-stream \
  --region us-west-2
```

### Run Benchmark
```bash
# Benchmark CloudWatch Logs
opensearch-benchmark execute-test \
  --workload-path ./workloads/cloudwatch_logs_workload.py \
  --test-procedure cloudwatch-logs-benchmark \
  --target-hosts localhost:9200

# Compare with OpenSearch
opensearch-benchmark execute-test \
  --workload big5 \
  --target-hosts localhost:9200
```

### Supported File Formats
- **JSON**: Single object or array
- **JSONL/NDJSON**: One JSON object per line

### Example Workload Configuration
```python
{
    "name": "search-errors",
    "operation-type": "cloudwatch-logs-search",
    "query": {"match": {"level": "ERROR"}},
    "log_group": "/aws/lambda/my-function",
    "region": "us-east-1",
    "time_range_hours": 24
}
```

## Performance Notes

- CloudWatch Logs has 15-minute query timeout
- Queries are charged per GB scanned
- Use specific time ranges and filters to reduce costs
- Consider API rate limits for high-concurrency benchmarks