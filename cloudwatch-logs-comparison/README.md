## CloudWatch Logs Comparison OSB Workload

This repository contains the **CloudWatch Logs Comparison** workload for benchmarking AWS CloudWatch Logs against OpenSearch using OpenSearch Benchmark. This workload uses real-world client ingestion log query patterns from production AWS services to provide meaningful performance comparisons across different query languages and target platforms.

This workload enables direct performance comparison between:
- **OpenSearch** (using DSL, PPL, or SQL)
- **AWS CloudWatch Logs** (with automatic or manual query translation)

### Query Categories

The workload includes 20 production queries across 6 essential categories:

1. **Count Queries**: Simple and filtered document counting operations
   - Total document counts
   - Filtered counts by host or service

2. **Aggregations**: Statistical operations on byte transfer metrics
   - Sum aggregations (bytes transferred, request/response sizes)
   - Max aggregations (peak transfer sizes)
   - Cardinality aggregations (distinct IP addresses, request IDs)

3. **Host/Hostname Filtering**: Pattern matching and term queries
   - Wildcard patterns (e.g., `*-cell-1-*`, `aws-logs-frontend-prod-*`)
   - Exact hostname matching
   - Combined filtering (host + hostname patterns)

4. **Group-By Operations**: Multi-field aggregation queries
   - Grouping by hostname and marketplace
   - Nested aggregations with counts

5. **Timestamp Operations**: Time-based sorting and pagination
   - Ascending/descending timestamp sorting
   - Time-filtered queries with sorting

6. **Distinct Value Queries**: Unique value identification
   - Distinct remote IP addresses
   - Unique request identifiers
   - Distinct hostnames

### Prerequisites

Before using this workload, ensure you have the following:

- [OpenSearch](https://opensearch.org) (v2.11 or later)
- [OpenSearch Benchmark](https://opensearch.org/docs/latest/benchmark) (v1.2 or later)
- [OpenSearch SQL Plugin](https://opensearch.org/docs/latest/search-plugins/sql/index/) (required for PPL and SQL test procedures)
- AWS credentials configured (for CloudWatch test procedures)
- Python 3.8+ with `aioboto3` and `boto3` packages (for CloudWatch operations)

### Query Language Support

This workload supports **six test procedures** across three query languages:

#### OpenSearch Test Procedures

1. **DSL (Default)**: Elasticsearch Query DSL syntax
   - Uses standard OpenSearch search API
   - Full support for all query types

2. **PPL**: Piped Processing Language
   - Requires SQL plugin installation
   - Uses `/_plugins/_ppl` endpoint
   - Pipe-based query syntax (e.g., `source = index | where field = value`)

3. **SQL**: Standard SQL syntax
   - Requires SQL plugin installation
   - Uses `/_plugins/_sql` endpoint
   - Familiar SQL SELECT statements

#### CloudWatch Test Procedures

4. **CloudWatch DSL**: Automatically translated from DSL
   - Translates OpenSearch DSL to CloudWatch Insights query language
   - Fully functional, no manual intervention required
   - Uses `AsyncCloudWatchLogsRunner` for translation

5. **CloudWatch PPL**: Manual translation required
   - Placeholder operations provided
   - Requires manual conversion of PPL to CloudWatch Insights syntax
   - Reference PPL queries included in `_comment` fields

6. **CloudWatch SQL**: Manual translation required
   - Placeholder operations provided
   - Requires manual conversion of SQL to CloudWatch Insights syntax
   - Reference SQL queries included in `_comment` fields

### Running the Workload

#### OpenSearch Test Procedures

Run DSL queries against OpenSearch (default):
```bash
opensearch-benchmark execute-test \
  --workload-path=./cloudwatch-logs-comparison \
  --test-procedure=dsl \
  --target-hosts=localhost:9200 \
  --workload-params='{"index_name":"opensearch-client-ingest-data-new"}'
```

Run PPL queries against OpenSearch:
```bash
opensearch-benchmark execute-test \
  --workload-path=./cloudwatch-logs-comparison \
  --test-procedure=ppl \
  --target-hosts=localhost:9200
```

Run SQL queries against OpenSearch:
```bash
opensearch-benchmark execute-test \
  --workload-path=./cloudwatch-logs-comparison \
  --test-procedure=sql \
  --target-hosts=localhost:9200
```

#### CloudWatch Test Procedures

Run DSL queries against CloudWatch Logs (automatic translation):
```bash
opensearch-benchmark execute-test \
  --workload-path=./cloudwatch-logs-comparison \
  --test-procedure=cloudwatch-dsl \
  --workload-params='{"cw_log_group":"your-log-group-name","cw_region":"us-east-1"}'
```

Run PPL queries against CloudWatch Logs (requires manual translation):
```bash
opensearch-benchmark execute-test \
  --workload-path=./cloudwatch-logs-comparison \
  --test-procedure=cloudwatch-ppl \
  --workload-params='{"cw_log_group":"your-log-group-name","cw_region":"us-east-1"}'
```

Run SQL queries against CloudWatch Logs (requires manual translation):
```bash
opensearch-benchmark execute-test \
  --workload-path=./cloudwatch-logs-comparison \
  --test-procedure=cloudwatch-sql \
  --workload-params='{"cw_log_group":"your-log-group-name","cw_region":"us-east-1"}'
```

### Parameters

This workload allows the following parameters to be specified using `--workload-params`:

#### OpenSearch Parameters
* `index_name` (default: `opensearch-client-ingest-data-new`): The name of the OpenSearch index to query.
* `search_clients` (default: 1): Number of clients that issue search requests.

#### CloudWatch Parameters
* `cw_log_group` (required for CloudWatch test procedures): The CloudWatch Logs log group name to query.
* `cw_region` (default: `us-east-1`): AWS region where the log group is located.
* `time_range_hours` (default: 24): Time range in hours for CloudWatch queries to scan.

#### Benchmark Configuration
* `warmup_iterations` (default: 100): Number of warmup query iterations prior to actual measurements.
* `test_iterations` (default: 50): Number of test iterations per query that will have their latency and throughput measured.
* `target_throughput` (default: 1): Target throughput for each query operation in requests per second (use 0 or "" for no throttling).

### AWS Configuration

#### Required IAM Permissions

For CloudWatch test procedures, ensure your AWS credentials have the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:StartQuery",
        "logs:GetQueryResults"
      ],
      "Resource": "*"
    }
  ]
}
```

#### Configuring AWS Credentials

Configure your AWS credentials using one of these methods:

```bash
# Method 1: AWS CLI
aws configure

# Method 2: Environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

#### Cost Considerations

- CloudWatch Logs queries are charged per GB of data scanned
- Use specific time ranges (`time_range_hours` parameter) to limit scanned data
- Apply filters to reduce the amount of data scanned
- Default time range is 24 hours

### Data Schema

The queries in this workload expect log documents with the following schema:

| Field | Type | Description |
|-------|------|-------------|
| `host` | keyword | Service host identifier (e.g., `service.internal`) |
| `Hostname` | keyword/text | Full hostname (e.g., `aws-logs-frontend-prod-iad12-cell-1-31.iad12.amazon.com`) |
| `Marketplace` | keyword | Marketplace identifier |
| `REMOTE_ADDR` | keyword | Remote IP address |
| `requestId` | keyword | Unique request identifier |
| `bytesReqHdrBe` | long | Bytes in request header (backend) |
| `bytesReqHdrFe` | long | Bytes in request header (frontend) |
| `bytesReqBodyBe` | long | Bytes in request body (backend) |
| `bytesReqBodyFe` | long | Bytes in request body (frontend) |
| `bytesRespHdrBe` | long | Bytes in response header (backend) |
| `bytesRespHdrFe` | long | Bytes in response header (frontend) |
| `bytesRespBodyFe` | long | Bytes in response body (frontend) |
| `reqContentLength` | long | Request content length |
| `putBufferedBytes` | long | Buffered bytes for PUT operations |
| `@timestamp` | date | Event timestamp |

### Query List

| # | Query Name | Category | Description |
|---|------------|----------|-------------|
| 0 | count-query | Count | Total document count with track_total_hits |
| 1 | sum-bytes-query | Aggregation | Sum of bytesReqHdrBe field |
| 2 | host-count-query | Count | Count documents where host = service.internal |
| 3 | host-filter-query | Filtering | Combined host and hostname wildcard filter (10k docs) |
| 4 | hostname-filter-query | Filtering | Match specific hostname (10k docs) |
| 5 | frontend-host-query | Filtering | Wildcard match for frontend hosts (10k docs) |
| 6 | iad12-host-query | Filtering | Wildcard match for iad12 region hosts (10k docs) |
| 7 | cell1-host-query | Filtering | Wildcard match for cell-1 hosts (10k docs) |
| 8 | host-group-query | Group-By | Group by hostname and marketplace with counts |
| 9 | timestamp-query | Timestamp | Sort by timestamp ascending (10k docs) |
| 10 | host-timestamp-query | Timestamp | Filter by host + sort by timestamp (10k docs) |
| 11 | limit-query | Basic | Simple pagination (10k docs) |
| 12 | sum-bytes-by-host-query | Aggregation | Sum bytes grouped by hostname |
| 13 | max-bytes-by-host-query | Aggregation | Max bytesReqHdrBe for specific hostname |
| 14 | distinct-remote-addr-query | Distinct | Cardinality aggregation on REMOTE_ADDR |
| 15 | distinct-requestid-query | Distinct | Cardinality aggregation on requestId |
| 16 | distinct-hostname-query | Distinct | Terms aggregation for unique hostnames (10k terms) |
| 17 | sum-req-content-query | Aggregation | Sum reqContentLength filtered by host |
| 18 | distinct-remote-addr-host-query | Distinct | Cardinality on REMOTE_ADDR filtered by host |
| 19 | max-bytes-query | Aggregation | Multiple max aggregations on 9 byte fields |

### Sample Run Output

#### DSL Test Procedure (OpenSearch)

```bash
opensearch-benchmark execute-test --workload-path=./cloudwatch-logs-comparison --test-procedure=dsl
```

```
   ____                  _____                      __       ____                  __                         __
  / __ \____  ___  ____ / ___/___  ____ ___________/ /_     / __ )___  ____  _____/ /_  ____ ___  ____ ______/ /__
 / / / / __ \/ _ \/ __ \\__ \/ _ \/ __ `/ ___/ ___/ __ \   / __  / _ \/ __ \/ ___/ __ \/ __ `__ \/ __ `/ ___/ //_/
/ /_/ / /_/ /  __/ / / /__/ /  __/ /_/ / /  / /__/ / / /  / /_/ /  __/ / / / /__/ / / / / / / / / /_/ / /  / ,<
\____/ .___/\___/_/ /_/____/\___/\__,_/_/   \___/_/ /_/  /_____/\___/_/ /_/\___/_/ /_/_/ /_/ /_/\__,_/_/  /_/|_|
    /_/

[INFO] Executing test with workload [cloudwatch-logs-comparison], test_procedure [dsl]

Running 0-count-query                                                          [100% done]
Running 1-sum-bytes-query                                                      [100% done]
Running 2-host-count-query                                                     [100% done]
Running 3-host-filter-query                                                    [100% done]
Running 4-hostname-filter-query                                                [100% done]
Running 5-frontend-host-query                                                  [100% done]
Running 6-iad12-host-query                                                     [100% done]
Running 7-cell1-host-query                                                     [100% done]
Running 8-host-group-query                                                     [100% done]
Running 9-timestamp-query                                                      [100% done]
Running 10-host-timestamp-query                                                [100% done]
Running 11-limit-query                                                         [100% done]
Running 12-sum-bytes-by-host-query                                             [100% done]
Running 13-max-bytes-by-host-query                                             [100% done]
Running 14-distinct-remote-addr-query                                          [100% done]
Running 15-distinct-requestid-query                                            [100% done]
Running 16-distinct-hostname-query                                             [100% done]
Running 17-sum-req-content-query                                               [100% done]
Running 18-distinct-remote-addr-host-query                                     [100% done]
Running 19-max-bytes-query                                                     [100% done]

------------------------------------------------------
```

#### CloudWatch-DSL Test Procedure

```bash
opensearch-benchmark execute-test --workload-path=./cloudwatch-logs-comparison --test-procedure=cloudwatch-dsl \
  --workload-params='{"cw_log_group":"opensearch-client-ingest-data-new","cw_region":"us-east-1"}'
```

```
[INFO] Executing test with workload [cloudwatch-logs-comparison], test_procedure [cloudwatch-dsl]

Running cw-0-count-query                                                       [100% done]
Running cw-1-sum-bytes-query                                                   [100% done]
Running cw-2-host-count-query                                                  [100% done]
Running cw-3-host-filter-query                                                 [100% done]
Running cw-4-hostname-filter-query                                             [100% done]
Running cw-5-frontend-host-query                                               [100% done]
Running cw-6-iad12-host-query                                                  [100% done]
Running cw-7-cell1-host-query                                                  [100% done]
Running cw-8-host-group-query                                                  [100% done]
Running cw-9-timestamp-query                                                   [100% done]
Running cw-10-host-timestamp-query                                             [100% done]
Running cw-11-limit-query                                                      [100% done]
Running cw-12-sum-bytes-by-host-query                                          [100% done]
Running cw-13-max-bytes-by-host-query                                          [100% done]
Running cw-14-distinct-remote-addr-query                                       [100% done]
Running cw-15-distinct-requestid-query                                         [100% done]
Running cw-16-distinct-hostname-query                                          [100% done]
Running cw-17-sum-req-content-query                                            [100% done]
Running cw-18-distinct-remote-addr-host-query                                  [100% done]
Running cw-19-max-bytes-query                                                  [100% done]

------------------------------------------------------
```

### Troubleshooting

#### SQL Plugin Not Installed

If you run the PPL or SQL test procedures without the SQL plugin installed, you'll see:

```
[ERROR] no handler found for uri [/_plugins/_ppl] and method [POST]
```

or

```
[ERROR] no handler found for uri [/_plugins/_sql] and method [POST]
```

**Solution**: Install the OpenSearch SQL Plugin on your cluster.

#### AWS Credentials Not Configured

For CloudWatch test procedures, if credentials are missing:

```
[ERROR] Unable to locate credentials
```

**Solution**: Configure AWS credentials using `aws configure` or environment variables.

#### CloudWatch Query Timeout

If CloudWatch queries timeout:

```
[ERROR] Query timed out after 300 seconds
```

**Solution**:
- Reduce the `time_range_hours` parameter
- Add more specific filters to reduce data scanned
- Ensure your log group has reasonable data volume

#### Manual Translation Required

For `cloudwatch-ppl` and `cloudwatch-sql` test procedures, operations contain placeholder queries:

```
"query": "TODO: Translate PPL query to CloudWatch Insights syntax"
```

**Solution**: Edit the operation files (`operations/cloudwatch-ppl.json` or `operations/cloudwatch-sql.json`) and manually translate queries to CloudWatch Insights syntax. Reference queries are provided in `_comment` fields.

### CloudWatch Query Translation

The `cloudwatch-dsl` test procedure uses `AsyncCloudWatchLogsRunner` to automatically translate OpenSearch DSL queries to CloudWatch Insights syntax:

| OpenSearch DSL | CloudWatch Insights |
|----------------|---------------------|
| `{"match": {"field": "value"}}` | `fields @timestamp, field \| filter field like /value/` |
| `{"term": {"field": "value"}}` | `fields @timestamp, field \| filter field = "value"` |
| `{"range": {"field": {"gte": 10}}}` | `fields @timestamp, field \| filter field >= 10` |
| `{"wildcard": {"field": "val*"}}` | `fields @timestamp, field \| filter field like /val.*/` |
| Bool queries (must, should, must_not) | Combined with `and`, `or`, `not` operators |

### License

This workload is provided under the Apache License 2.0. See LICENSE file for details.
