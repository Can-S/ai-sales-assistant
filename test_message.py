"""Test the AI training business agent with Instagram inquiry"""
from src.agent import graph

message_input = {
    "message_input": {
        "platform": "instagram",
        "sender": "Sarah Chen @sarahchen_marketing",
        "recipient": "AI Training Co @aitrainingco", 
        "subject": None,
        "content": """Hi! I saw your post about AI training for teams. We're a 25-person marketing agency and I'm interested in helping our team use AI tools more effectively for content creation, campaign planning, and client reporting.

What programs do you offer and what's the pricing? We'd want something practical that our team can apply immediately.

Thanks!""",
        "timestamp": "2024-12-14 10:30:00"
    }
}

print("=" * 80)
print("TESTING AI TRAINING BUSINESS AGENT - INSTAGRAM INQUIRY")
print("=" * 80)
print("\nMessage details:")
print(f"Platform: {message_input['message_input']['platform']}")
print(f"From: {message_input['message_input']['sender']}")
print(f"To: {message_input['message_input']['recipient']}")
print(f"\nMessage Content:")
print(message_input['message_input']['content'])
print("\n" + "=" * 80)
print("Running classification and response generation...")
print("=" * 80 + "\n")

try:
    result = graph.invoke(message_input)
    
    print("\n" + "=" * 80)
    print("RESULT")
    print("=" * 80)
    print(f"\nClassification: {result.get('classification_decision', 'Not set')}")
    
    if result.get('classification_decision') == 'respond':
        print("\n✅ [SUCCESS] Message correctly classified as RESPOND!")
        print("\nThe agent should:")
        print("- Recommend 'AI for Productivity & Automation' program ($2,500 for 15 people)")
        print("- Mention additional cost for 10 more employees ($150 x 10 = $1,500)")
        print("- Total estimated cost: $4,000")
        print("- Suggest booking a discovery call")
        
        if 'messages' in result and len(result['messages']) > 0:
            print("\n" + "-" * 80)
            print("AGENT RESPONSE:")
            print("-" * 80)
            for msg in result['messages']:
                if hasattr(msg, 'content'):
                    print(msg.content)
                    
    elif result.get('classification_decision') == 'ignore':
        print("\n❌ [FAIL] Message incorrectly classified as IGNORE")
        print("This is a business inquiry and should be responded to!")
        
    elif result.get('classification_decision') == 'notify':
        print("\n⚠️  [UNEXPECTED] Message classified as NOTIFY")
        print("Business inquiries should be classified as RESPOND, not NOTIFY")
        
except Exception as e:
    print(f"\n❌ [ERROR] {e}")
    import traceback
    traceback.print_exc()
