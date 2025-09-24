"""Test document upload functionality"""
import io
import sys
import os

# Add current directory to path to import our modules
sys.path.insert(0, os.path.dirname(__file__))

from streamlit_app_clean import extract_text_from_file

class MockUploadedFile:
    """Mock Streamlit uploaded file for testing"""
    def __init__(self, name: str, content: bytes):
        self.name = name
        self.content = content
    
    def read(self):
        return self.content

def test_text_file_processing():
    """Test text file processing"""
    print("Testing text file processing...")
    
    # Create mock text file
    text_content = "This is a test document for the RAG system."
    mock_file = MockUploadedFile("test.txt", text_content.encode('utf-8'))
    
    # Test extraction
    filename, extracted_text = extract_text_from_file(mock_file)
    
    print(f"Filename: {filename}")
    print(f"Extracted text: {extracted_text}")
    print(f"Success: {extracted_text == text_content}")
    print("-" * 50)

def test_unsupported_file():
    """Test unsupported file type"""
    print("Testing unsupported file type...")
    
    mock_file = MockUploadedFile("test.xyz", b"some content")
    filename, extracted_text = extract_text_from_file(mock_file)
    
    print(f"Filename: {filename}")
    print(f"Extracted text: {extracted_text}")
    print(f"Contains error message: {'Unsupported file type' in extracted_text}")
    print("-" * 50)

if __name__ == "__main__":
    print("🧪 Testing Document Upload Functionality")
    print("=" * 50)
    
    test_text_file_processing()
    test_unsupported_file()
    
    print("✅ Document processing tests completed!")