# CloudWatch Logs Workload

This workload runs a data corpora on both CloudWatch Logs and OpenSearch.


### Test Procedures

#### OpenSearch DSL (Default)
```
opensearch-benchmark run --target-host="https://search-opensearch-219-test-7gp4rtoigdlt5qxtqgdehyxboe.us-east-1.es.amazonaws.com" --client-options="basic_auth_user:'hoangia',basic_auth_password:'Hoangia@123'" --workload-path=/home/ec2-user/cloud-watch-logs-benchmark/cloudwatch-logs-comparison --test-mode
```

#### OpenSearch PPL
```
opensearch-benchmark run --target-host="https://search-opensearch-219-test-7gp4rtoigdlt5qxtqgdehyxboe.us-east-1.es.amazonaws.com" --client-options="basic_auth_user:'hoangia',basic_auth_password:'Hoangia@123'" --workload-path=/home/ec2-user/cloud-watch-logs-benchmark/cloudwatch-logs-comparison --test-procedure=ppl --test-mode
```

#### OpenSearch SQL
```
opensearch-benchmark run --target-host="https://search-opensearch-219-test-7gp4rtoigdlt5qxtqgdehyxboe.us-east-1.es.amazonaws.com" --client-options="basic_auth_user:'hoangia',basic_auth_password:'Hoangia@123'" --workload-path=/home/ec2-user/cloud-watch-logs-benchmark/cloudwatch-logs-comparison --test-procedure=sql --test-mode
```