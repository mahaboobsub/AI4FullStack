import boto3
from core.config import get_settings

s = get_settings()
client = boto3.client('bedrock', region_name=s.AWS_REGION, 
                     aws_access_key_id=s.AWS_ACCESS_KEY_ID,
                     aws_secret_access_key=s.AWS_SECRET_ACCESS_KEY)

print("Listing inference profiles...")
try:
    response = client.list_inference_profiles()
    profiles = response.get('inferenceProfileSummaries', [])
    
    # Filter for Anthropic Claude 4
    claude4 = [p for p in profiles if 'claude' in p['inferenceProfileId'].lower() and '4' in p['inferenceProfileId']]
    
    print(f"\n✅ Found {len(claude4)} Claude 4 inference profiles:\n")
    for p in claude4[:15]:
        print(f"  • {p['inferenceProfileId']}")
        if 'models' in p:
            print(f"    Models: {p['models']}")
except Exception as e:
    print(f"Error: {e}")
