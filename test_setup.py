#!/usr/bin/env python3
import os
from dotenv import load_dotenv

print("\n" + "=" * 70)
print("🔍 SETUP DIAGNOSTIC")
print("=" * 70 + "\n")

# Load environment
load_dotenv()

# Check imports
print("📦 Checking Python packages...")
try:
    import boto3
    print("   ✅ boto3")
except ImportError:
    print("   ❌ boto3 - Run: pip install boto3")

try:
    import anthropic
    print("   ✅ anthropic")
except ImportError:
    print("   ❌ anthropic - Run: pip install anthropic")

try:
    from dotenv import load_dotenv
    print("   ✅ python-dotenv")
except ImportError:
    print("   ❌ python-dotenv - Run: pip install python-dotenv")

# Check .env file
print("\n🔑 Checking environment variables...")
if os.path.exists('.env'):
    print("   ✅ .env file exists")
else:
    print("   ❌ .env file missing - Run: cp .env.example .env")

claude_key = os.getenv('CLAUDE_API_KEY')
if claude_key:
    print(f"   ✅ CLAUDE_API_KEY set (starts with: {claude_key[:10]}...)")
else:
    print("   ❌ CLAUDE_API_KEY missing in .env file")

region = os.getenv('AWS_REGION')
if region:
    print(f"   ✅ AWS_REGION set to: {region}")
else:
    print("   ❌ AWS_REGION missing in .env file")

# Check AWS credentials
print("\n☁️  Checking AWS credentials...")
try:
    import boto3
    sts = boto3.client('sts', region_name='us-east-1')
    identity = sts.get_caller_identity()
    print(f"   ✅ AWS credentials valid")
    print(f"      Account: {identity['Account']}")
except Exception as e:
    print(f"   ❌ AWS credentials failed: {str(e)[:50]}...")
    print("      Run: aws configure")

print("\n" + "=" * 70)
print("✅ Diagnostic complete!")
print("=" * 70 + "\n")
