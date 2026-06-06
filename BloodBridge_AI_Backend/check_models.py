import boto3
from core.config import get_settings

s = get_settings()
client = boto3.client('bedrock', region_name=s.AWS_REGION, 
                     aws_access_key_id=s.AWS_ACCESS_KEY_ID,
                     aws_secret_access_key=s.AWS_SECRET_ACCESS_KEY)

print("Listing available foundation models...")
response = client.list_foundation_models()
models = response['modelSummaries']

# Filter for Anthropic and Nova
enabled = [m for m in models if 'anthropic' in m['modelId'].lower() or 'nova' in m['modelId'].lower()]

print(f"\n✅ Found {len(enabled)} Anthropic/Nova models:\n")
for m in enabled[:15]:
    print(f"  • {m['modelId']}")
