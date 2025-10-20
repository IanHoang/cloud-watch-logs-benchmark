#!/usr/bin/env python3
"""
Simple script to ingest data from a file into CloudWatch Logs
"""

import asyncio
import json
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

import boto3
from tqdm import tqdm


class CloudWatchIngester:
    def __init__(self, log_group: str, region: str):
        self.cw_client = boto3.client('logs', region_name=region)
        self.log_group = log_group
        self.region = region
        
        # Ensure log group exists
        self._ensure_log_group_exists()
    
    def _ensure_log_group_exists(self):
        """Create log group if it doesn't exist"""
        try:
            self.cw_client.create_log_group(logGroupName=self.log_group)
            print(f"✓ Created log group: {self.log_group}")
        except self.cw_client.exceptions.ResourceAlreadyExistsException:
            print(f"✓ Using existing log group: {self.log_group}")
    
    def _ensure_log_stream_exists(self, stream_name: str):
        """Create log stream if it doesn't exist"""
        try:
            self.cw_client.create_log_stream(
                logGroupName=self.log_group,
                logStreamName=stream_name
            )
            print(f"✓ Created log stream: {stream_name}")
        except self.cw_client.exceptions.ResourceAlreadyExistsException:
            pass
    
    def load_data_from_file(self, filepath: str) -> List[Dict[str, Any]]:
        """Load data from JSON Lines file"""
        data = []
        file_path = Path(filepath)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        print(f"📁 Loading data from: {filepath}")
        
        with open(file_path, 'r') as f:
            if filepath.endswith('.jsonl') or filepath.endswith('.ndjson'):
                # JSON Lines format
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line:
                        try:
                            data.append(json.loads(line))
                        except json.JSONDecodeError as e:
                            print(f"⚠️  Warning: Invalid JSON on line {line_num}: {e}")
            else:
                # Regular JSON file
                try:
                    file_data = json.load(f)
                    if isinstance(file_data, list):
                        data = file_data
                    else:
                        data = [file_data]
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON file: {e}")
        
        print(f"✓ Loaded {len(data)} records")
        return data
    
    def ingest_to_cloudwatch(self, data: List[Dict[str, Any]], stream_name: str = None) -> int:
        """Ingest data into CloudWatch Logs with progress tracking"""
        if not data:
            print("⚠️  No data to ingest")
            return 0
        
        if stream_name is None:
            stream_name = f"ingestion-{int(time.time())}"
        
        self._ensure_log_stream_exists(stream_name)
        
        print(f"🚀 Starting ingestion to CloudWatch Logs...")
        print(f"   Log Group: {self.log_group}")
        print(f"   Log Stream: {stream_name}")
        
        start_time = time.time()
        
        # Convert data to CloudWatch log events
        log_events = []
        for doc in data:
            # Use timestamp from data if available, otherwise use current time
            if 'timestamp' in doc:
                try:
                    if isinstance(doc['timestamp'], str):
                        timestamp_ms = int(datetime.fromisoformat(
                            doc['timestamp'].replace('Z', '+00:00')
                        ).timestamp() * 1000)
                    else:
                        timestamp_ms = int(doc['timestamp'] * 1000)
                except:
                    timestamp_ms = int(time.time() * 1000)
            else:
                timestamp_ms = int(time.time() * 1000)
            
            log_events.append({
                'timestamp': timestamp_ms,
                'message': json.dumps(doc, default=str, separators=(',', ':'))
            })
        
        # Sort by timestamp (required by CloudWatch)
        log_events.sort(key=lambda x: x['timestamp'])
        
        # Send in batches with progress tracking
        batch_size = 1000  # CloudWatch limit: 10,000 events or 1MB per request
        total_sent = 0
        failed_batches = 0
        
        with tqdm(total=len(log_events), desc="Ingesting", unit="records") as pbar:
            for i in range(0, len(log_events), batch_size):
                batch = log_events[i:i + batch_size]
                
                try:
                    response = self.cw_client.put_log_events(
                        logGroupName=self.log_group,
                        logStreamName=stream_name,
                        logEvents=batch
                    )
                    
                    total_sent += len(batch)
                    pbar.update(len(batch))
                    
                    # Small delay to avoid throttling
                    time.sleep(0.05)
                    
                except Exception as e:
                    failed_batches += 1
                    pbar.write(f"❌ Failed to send batch {i//batch_size + 1}: {e}")
                    pbar.update(len(batch))
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Print summary
        print(f"\n📊 Ingestion Summary:")
        print(f"   Total records: {len(log_events):,}")
        print(f"   Successfully sent: {total_sent:,}")
        print(f"   Failed batches: {failed_batches}")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Rate: {total_sent/duration:.1f} records/second")
        
        if failed_batches > 0:
            print(f"⚠️  {failed_batches} batches failed - check AWS permissions and limits")
        else:
            print("✅ Ingestion completed successfully!")
        
        return total_sent


def main():
    parser = argparse.ArgumentParser(description='Ingest data from file to CloudWatch Logs')
    parser.add_argument('filepath', help='Path to JSON or JSONL file')
    parser.add_argument('--log-group', required=True, help='CloudWatch log group name')
    parser.add_argument('--log-stream', help='CloudWatch log stream name (auto-generated if not provided)')
    parser.add_argument('--region', default='us-east-1', help='AWS region (default: us-east-1)')
    
    args = parser.parse_args()
    
    try:
        ingester = CloudWatchIngester(
            log_group=args.log_group,
            region=args.region
        )
        
        # Load and ingest data
        data = ingester.load_data_from_file(args.filepath)
        ingester.ingest_to_cloudwatch(data, args.log_stream)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())