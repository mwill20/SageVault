"""Debug RAG indexing - test what files are being processed"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from streamlit_app_clean import parse_github_url

# Updated fetch_github_files to match the new signature
def fetch_github_files(owner: str, repo: str, max_files: int = 100, github_token: str = None):
    import requests
    
    files = {}
    headers = {}
    if github_token:
        headers['Authorization'] = f'token {github_token}'
    
    # Get repository tree
    tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1"
    response = requests.get(tree_url, headers=headers, timeout=30)
    
    if response.status_code != 200:
        tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/master?recursive=1"
        response = requests.get(tree_url, headers=headers, timeout=30)
    
    if response.status_code != 200:
        raise Exception(f"Could not access repository: {response.status_code}")
    
    tree_data = response.json()
    
    # Filter for text files
    text_extensions = {
        '.md', '.txt', '.rst', '.adoc', '.wiki',
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.hpp', '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala',
        '.css', '.html', '.htm', '.scss', '.sass', '.less',
        '.json', '.yml', '.yaml', '.xml', '.toml', '.cfg', '.ini', '.conf', '.config',
        '.sh', '.bash', '.zsh', '.ps1', '.bat', '.cmd',
        '.sql', '.r', '.m', '.pl', '.lua', '.vim', '.dockerfile'
    }
    
    common_text_files = {'readme', 'license', 'changelog', 'contributing', 'authors', 'credits', 'makefile', 'dockerfile', 'requirements'}
    
    count = 0
    for item in tree_data.get('tree', []):
        if item['type'] != 'blob' or count >= max_files:
            continue
            
        path = item['path']
        filename = path.lower()
        
        is_text_file = (
            any(filename.endswith(ext) for ext in text_extensions) or
            any(common_name in filename for common_name in common_text_files)
        )
        
        if not is_text_file:
            continue
        
        # Fetch file content
        try:
            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/{path}"
            file_response = requests.get(raw_url, headers=headers, timeout=15)
            
            if file_response.status_code != 200:
                raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/{path}"
                file_response = requests.get(raw_url, headers=headers, timeout=15)
            
            if file_response.status_code == 200 and len(file_response.content) < 100000:
                try:
                    content = file_response.content.decode('utf-8', errors='ignore')
                    if content.strip():
                        files[path] = content
                        count += 1
                except:
                    continue
        except:
            continue
    
    return files
from simple_rag import create_vector_store, search_vector_store

def debug_repository_indexing(repo_url: str):
    """Debug what happens when we index a repository"""
    print(f"🔍 Debugging repository: {repo_url}")
    print("=" * 60)
    
    # Parse URL
    try:
        owner, repo = parse_github_url(repo_url)
        print(f"Owner: {owner}, Repo: {repo}")
    except Exception as e:
        print(f"❌ Error parsing URL: {e}")
        return
    
    # Fetch files
    try:
        files = fetch_github_files(owner, repo)
        print(f"\n📁 Files fetched: {len(files)}")
        print("-" * 40)
        
        for i, (file_path, content) in enumerate(files.items()):
            char_count = len(content)
            print(f"{i+1:2d}. {file_path:<40} ({char_count:>6,} chars)")
            if i >= 9:  # Show first 10
                remaining = len(files) - 10
                if remaining > 0:
                    print(f"     ... and {remaining} more files")
                break
                
    except Exception as e:
        print(f"❌ Error fetching files: {e}")
        return
    
    if not files:
        print("❌ No files found!")
        return
    
    # Create vector store
    try:
        print(f"\n🔗 Creating vector store...")
        collection = create_vector_store(files, f"debug_{owner}_{repo}")
        print("✅ Vector store created successfully")
        
        # Test searches
        test_queries = [
            "What does this project do?",
            "How do I install this?", 
            "What are the main classes and functions in the code?",
            "Show me the core implementation details",
            "How does the authentication work in the code?",
            "What are the main Python modules and their purpose?"
        ]
        
        print(f"\n❓ Testing queries...")
        print("-" * 40)
        
        for query in test_queries:
            print(f"\nQuery: '{query}'")
            results = search_vector_store(collection, query, k=3)
            
            if results:
                for i, result in enumerate(results):
                    file_path = result['file_path']
                    similarity = result['similarity']
                    text_preview = result['text'][:100].replace('\n', ' ')
                    print(f"  {i+1}. {file_path} (sim: {similarity}) - {text_preview}...")
            else:
                print("  No results found")
                
    except Exception as e:
        print(f"❌ Error with vector store: {e}")

if __name__ == "__main__":
    # Test with repositories that have actual Python code
    test_repos = [
        "https://github.com/psf/requests",    # Popular Python HTTP library
        "https://github.com/pallets/flask",   # Flask web framework
    ]
    
    for repo_url in test_repos:
        debug_repository_indexing(repo_url)
        print("\n" + "="*80 + "\n")