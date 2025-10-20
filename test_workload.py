import aioboto3
import asyncio
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


class AsyncCloudWatchLogsRunner:
    def __init__(self, params: Dict[str, Any]):
        self.region = params.get('region', 'us-east-1')
        self.log_group = params['log_group']
        self.query_params = params.get('query_params', {})
        self.session = aioboto3.Session()

    async def search(self, query: Any, **kwargs) -> Dict[str, Any]:
        """Execute search against CloudWatch Logs"""
        cw_query = self._translate_query(query)

        start_time = time.time()

        async with self.session.client('logs', region_name=self.region) as client:
            try:
                # Start the query
                response = await client.start_query(
                    logGroupName=self.log_group,
                    startTime=int((datetime.now() - timedelta(
                        hours=kwargs.get('time_range_hours', 24)
                    )).timestamp()),
                    endTime=int(datetime.now().timestamp()),
                    queryString=cw_query,
                    limit=kwargs.get('limit', 1000)
                )

                query_id = response['queryId']

                # Poll for completion with exponential backoff
                poll_interval = 0.1
                max_poll_interval = 2.0
                timeout = kwargs.get('timeout', 300)  # 5 minutes default

                while (time.time() - start_time) < timeout:
                    result = await client.get_query_results(queryId=query_id)

                    if result['status'] == 'Complete':
                        end_time = time.time()
                        return self._format_response(result, start_time, end_time)

                    elif result['status'] == 'Failed':
                        raise Exception(f"Query failed: {result}")

                    elif result['status'] in ['Cancelled', 'Timeout']:
                        raise Exception(f"Query {result['status'].lower()}")

                    # Exponential backoff for polling
                    await asyncio.sleep(poll_interval)
                    poll_interval = min(poll_interval * 1.5, max_poll_interval)

                # Timeout reached
                raise TimeoutError(f"Query timed out after {timeout} seconds")

            except Exception as e:
                end_time = time.time()
                return self._format_error_response(e, start_time, end_time)

    def _format_response(self, result: Dict, start_time: float, end_time: float) -> Dict[str, Any]:
        """Format CloudWatch response to match OpenSearch format"""
        results = result.get('results', [])

        # Convert CloudWatch results to ES-like format
        hits = []
        for row in results:
            hit = {'_source': {}}
            for field in row:
                if field.get('field') == '@timestamp':
                    hit['_source']['@timestamp'] = field.get('value')
                elif field.get('field') == '@message':
                    # Try to parse JSON message
                    try:
                        message_data = json.loads(field.get('value', ''))
                        hit['_source'].update(message_data)
                    except json.JSONDecodeError:
                        hit['_source']['message'] = field.get('value')
                else:
                    hit['_source'][field.get('field', 'unknown')] = field.get('value')
            hits.append(hit)

        return {
            'took': int((end_time - start_time) * 1000),  # milliseconds
            'timed_out': False,
            'hits': {
                'total': {'value': len(hits), 'relation': 'eq'},
                'max_score': None,
                'hits': hits
            },
            '_shards': {'total': 1, 'successful': 1, 'skipped': 0, 'failed': 0},
            'statistics': result.get('statistics', {})
        }

    def _format_error_response(self, error: Exception, start_time: float, end_time: float) -> Dict[str, Any]:
        """Format error response"""
        return {
            'took': int((end_time - start_time) * 1000),
            'timed_out': isinstance(error, TimeoutError),
            'error': {
                'type': type(error).__name__,
                'reason': str(error)
            },
            'hits': {'total': {'value': 0}, 'hits': []}
        }

    def _translate_query(self, es_query: Any) -> str:
        """Enhanced query translation"""
        if isinstance(es_query, dict):
            return self._translate_dict_query(es_query)
        elif isinstance(es_query, str):
            return self._translate_string_query(es_query)
        else:
            return str(es_query)

    def _translate_dict_query(self, query: Dict[str, Any]) -> str:
        """Translate dictionary queries"""
        if 'bool' in query:
            return self._translate_bool_query(query['bool'])

        elif 'match' in query:
            field, value = next(iter(query['match'].items()))
            if isinstance(value, dict) and 'query' in value:
                value = value['query']
            return f'fields @timestamp, {field} | filter {field} like /{value}/'

        elif 'match_all' in query:
            return 'fields @timestamp, @message | limit 1000'

        elif 'term' in query:
            field, value = next(iter(query['term'].items()))
            if isinstance(value, dict) and 'value' in value:
                value = value['value']
            return f'fields @timestamp, {field} | filter {field} = "{value}"'

        elif 'terms' in query:
            field, values = next(iter(query['terms'].items()))
            value_list = ', '.join([f'"{v}"' for v in values])
            return f'fields @timestamp, {field} | filter {field} in [{value_list}]'

        elif 'range' in query:
            field, conditions = next(iter(query['range'].items()))
            filters = []

            if 'gte' in conditions:
                filters.append(f'{field} >= {conditions["gte"]}')
            if 'gt' in conditions:
                filters.append(f'{field} > {conditions["gt"]}')
            if 'lte' in conditions:
                filters.append(f'{field} <= {conditions["lte"]}')
            if 'lt' in conditions:
                filters.append(f'{field} < {conditions["lt"]}')

            filter_clause = ' and '.join(filters) if filters else 'true'
            return f'fields @timestamp, {field} | filter {filter_clause}'

        elif 'wildcard' in query:
            field, pattern = next(iter(query['wildcard'].items()))
            if isinstance(pattern, dict) and 'value' in pattern:
                pattern = pattern['value']
            # Convert ES wildcard to CloudWatch regex
            cw_pattern = pattern.replace('*', '.*').replace('?', '.')
            return f'fields @timestamp, {field} | filter {field} like /{cw_pattern}/'

        else:
            # Fallback for unsupported queries
            return 'fields @timestamp, @message | limit 1000'

    def _translate_bool_query(self, bool_query: Dict[str, Any]) -> str:
        """Translate boolean queries"""
        conditions = []

        # Handle 'must' clauses (AND)
        if 'must' in bool_query:
            must_conditions = []
            for clause in bool_query['must']:
                sub_query = self._translate_dict_query(clause)
                # Extract filter part if possible
                if '| filter ' in sub_query:
                    filter_part = sub_query.split('| filter ')[1]
                    must_conditions.append(filter_part)
            if must_conditions:
                conditions.append(f"({' and '.join(must_conditions)})")

        # Handle 'should' clauses (OR)
        if 'should' in bool_query:
            should_conditions = []
            for clause in bool_query['should']:
                sub_query = self._translate_dict_query(clause)
                if '| filter ' in sub_query:
                    filter_part = sub_query.split('| filter ')[1]
                    should_conditions.append(filter_part)
            if should_conditions:
                conditions.append(f"({' or '.join(should_conditions)})")

        # Handle 'must_not' clauses (NOT)
        if 'must_not' in bool_query:
            must_not_conditions = []
            for clause in bool_query['must_not']:
                sub_query = self._translate_dict_query(clause)
                if '| filter ' in sub_query:
                    filter_part = sub_query.split('| filter ')[1]
                    must_not_conditions.append(f"not ({filter_part})")
            if must_not_conditions:
                conditions.extend(must_not_conditions)

        if conditions:
            final_condition = ' and '.join(conditions)
            return f'fields @timestamp, @message | filter {final_condition}'
        else:
            return 'fields @timestamp, @message | limit 1000'

    def _translate_string_query(self, query: str) -> str:
        """Translate simple string queries"""
        # Simple keyword search
        return f'fields @timestamp, @message | filter @message like /{query}/ | limit 1000'


# Register with OpenSearch Benchmark
def register(registry):
    registry.register_runner("cloudwatch-logs-search", cloudwatch_logs_search)


async def cloudwatch_logs_search(es, params):
    """Main runner function for OpenSearch Benchmark"""
    runner = AsyncCloudWatchLogsRunner(params)

    # Extract query - handle different parameter formats
    query = None
    if 'body' in params:
        query = params['body'].get('query', params['body'])
    elif 'query' in params:
        query = params['query']
    else:
        query = {'match_all': {}}

    # Execute the search
    response = await runner.search(query, **params)

    return response

def create_workload():
    return {
        "version": 2,
        "description": "CloudWatch Logs Test",
        "operations": [
            {
                "name": "simple-search",
                "operation-type": "cloudwatch-logs-search",
                "query": "ERROR",  
                "log_group": "/your/log/group/name", 
                "region": "us-east-1",  
                "time_range_hours": 1  
            }
        ],
        "test_procedures": [
            {
                "name": "quick-test",
                "schedule": [
                    {
                        "operation": "simple-search",
                        "clients": 1,
                        "iterations": 5  
                    }
                ]
            }
        ]
    }