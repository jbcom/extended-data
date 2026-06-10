#!/usr/bin/env python3
"""Example: Basic AWS Connector usage.

This example demonstrates how to use the AWS connector to interact with
AWS Organizations and S3.

Requirements:
    pip install extended-data[aws]

Environment Variables:
    AWS_ACCESS_KEY_ID: AWS access key
    AWS_SECRET_ACCESS_KEY: AWS secret key
    AWS_DEFAULT_REGION: AWS region (optional, defaults to us-east-1)
"""

from __future__ import annotations

import os
import sys


def main() -> int:
    """Demonstrate AWS connector usage."""
    # Check for required environment variables
    if not os.getenv("AWS_ACCESS_KEY_ID"):
        print("Error: AWS_ACCESS_KEY_ID environment variable is required.")
        return 1

    try:
        from extended_data.connectors import AWSConnector, AWSConnectorFull
    except ImportError:
        print("Error: Could not import extended_data.connectors. Install with: pip install extended-data[aws]")
        return 1

    # Basic connector - just session management
    print("Creating basic AWS connector...")
    AWSConnector()
    print("Basic connector created successfully.")

    # Full connector with all operations
    print("\nCreating full AWS connector...")
    full_connector = AWSConnectorFull()
    print("Full connector created successfully.")

    # List S3 buckets
    print("\n--- S3 Buckets ---")
    try:
        buckets = full_connector.list_buckets()
        for bucket in buckets[:5]:  # Show first 5
            print(f"  Bucket: {bucket}")
        if len(buckets) > 5:
            print(f"  ... and {len(buckets) - 5} more buckets")
    except Exception as e:
        print(f"  Could not list buckets: {e}")

    # List organization accounts (if using Organizations)
    print("\n--- Organization Accounts ---")
    try:
        accounts = full_connector.get_accounts()
        for account in accounts[:5]:
            print(f"  Account: {account}")
        if len(accounts) > 5:
            print(f"  ... and {len(accounts) - 5} more accounts")
    except Exception as e:
        print(f"  Could not list accounts: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
