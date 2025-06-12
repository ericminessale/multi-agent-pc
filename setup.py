#!/usr/bin/env python3
"""
Setup script for PC Builder Pro Demo
Handles dependency installation and knowledge base building
"""

import os
import sys
import subprocess
import platform


def download_nltk_resources():
    """Download required NLTK resources if needed"""
    try:
        import nltk
        print("\n🔧 Setting up NLTK resources...")
        
        # Create nltk_data directory in the virtual environment
        if platform.system() == "Windows":
            nltk_data_dir = os.path.join(os.getcwd(), 'venv', 'nltk_data')
        else:
            nltk_data_dir = os.path.join(os.getcwd(), 'venv', 'nltk_data')
        
        os.makedirs(nltk_data_dir, exist_ok=True)
        
        # Add to NLTK data path
        if nltk_data_dir not in nltk.data.path:
            nltk.data.path.append(nltk_data_dir)
        
        # Required NLTK resources
        resources = [
            'wordnet',
            'averaged_perceptron_tagger', 
            'averaged_perceptron_tagger_eng',
            'punkt',
            'stopwords'
        ]
        
        for resource in resources:
            try:
                nltk.data.find(f'tokenizers/{resource}' if resource == 'punkt' 
                             else f'corpora/{resource}' if resource in ['wordnet', 'stopwords']
                             else f'taggers/{resource}')
                print(f"✅ {resource} already available")
            except LookupError:
                print(f"📥 Downloading {resource}...")
                try:
                    nltk.download(resource, download_dir=nltk_data_dir, quiet=True)
                    print(f"✅ {resource} downloaded successfully")
                except Exception as e:
                    print(f"⚠️  Warning: Could not download {resource}: {e}")
        
        print("✅ NLTK resources setup complete!")
        return True
        
    except ImportError:
        print("ℹ️  NLTK not found, skipping NLTK resource setup")
        return False
    except Exception as e:
        print(f"⚠️  Warning: NLTK setup failed: {e}")
        return False


def run_command(cmd):
    """Run a command and return success status"""
    print(f"Running: {cmd}")
    try:
        subprocess.run(cmd, shell=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def main():
    print("🖥️  PC Builder Pro Demo Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version.split()[0]} detected")
    
    # Create virtual environment if it doesn't exist
    if not os.path.exists("venv"):
        print("\n📦 Creating virtual environment...")
        if not run_command(f"{sys.executable} -m venv venv"):
            print("❌ Failed to create virtual environment")
            sys.exit(1)
    
    # Determine activation command based on OS
    if platform.system() == "Windows":
        activate_cmd = "venv\\Scripts\\activate"
        pip_cmd = "venv\\Scripts\\pip"
        python_cmd = "venv\\Scripts\\python"
        sw_search_cmd = "venv\\Scripts\\sw-search"
    else:
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
        python_cmd = "venv/bin/python"
        sw_search_cmd = "venv/bin/sw-search"
    
    print(f"\n💡 To activate virtual environment: {activate_cmd}")
    
    # Upgrade pip
    print("\n📦 Upgrading pip...")
    run_command(f"{pip_cmd} install --upgrade pip")
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    if not run_command(f"{pip_cmd} install -r requirements.txt"):
        print("❌ Failed to install dependencies")
        print("💡 Try running: pip install -r requirements.txt")
        sys.exit(1)
    
    print("\n✅ Dependencies installed successfully!")
    
    # Setup NLTK resources if NLTK is available
    download_nltk_resources()
    
    # Check if knowledge base files exist
    kb_files = {
        "sales_knowledge_base.md": "sales_knowledge.swsearch",
        "support_knowledge_base.md": "support_knowledge.swsearch"
    }
    
    print("\n📚 Checking knowledge bases...")
    missing_files = []
    for source, target in kb_files.items():
        if not os.path.exists(source):
            missing_files.append(source)
            print(f"❌ Missing: {source}")
        else:
            print(f"✅ Found: {source}")
    
    if missing_files:
        print("\n⚠️  Some knowledge base files are missing!")
        print("Please ensure you have the knowledge base markdown files.")
        return
    
    # Ask if user wants to build search indexes
    print("\n🔍 RAG Search Setup")
    print("Would you like to build the search indexes now?")
    print("This enables RAG search capabilities for the agents.")
    response = input("Build search indexes? (y/n): ").lower().strip()
    
    if response == 'y':
        print("\n🏗️  Building search indexes...")
        for source, target in kb_files.items():
            if os.path.exists(target):
                print(f"⚠️  {target} already exists, skipping...")
                continue
            
            print(f"\n📝 Building {target} from {source}...")
            cmd = f"{sw_search_cmd} {source} --output {target}"
            if not run_command(cmd):
                print(f"❌ Failed to build {target}")
                print("💡 You can manually build it later with:")
                print(f"   sw-search {source} --output {target}")
            else:
                print(f"✅ Successfully built {target}")
    
    # Create .env file if it doesn't exist
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            print("\n🔐 Creating .env file from template...")
            with open(".env.example", "r") as src, open(".env", "w") as dst:
                dst.write(src.read())
            print("✅ Created .env file from .env.example template")
            print("💡 Edit .env file to customize configuration")
        else:
            print("\n🔐 Creating basic .env file...")
            with open(".env", "w") as f:
                f.write("""# PC Builder Pro Configuration
# Copy settings from .env.example if available

# Context Management
USE_DATABASE_CONTEXT=false
CONTEXT_DB_PATH=pc_builder_context.db
CONTEXT_TTL_HOURS=24

# Add your custom configuration here
""")
            print("✅ Created basic .env file")
    
    print("\n🎉 Setup Complete!")
    print("\n📖 Next steps:")
    print(f"1. Activate virtual environment: {activate_cmd}")
    print("2. Edit .env file to add any API keys (optional)")
    print("3. Run the demo: python pc_builder_service.py")
    print("\n💡 The service will run on http://localhost:3001")
    print("\n📞 Available routes:")
    print("   / (root)  - Triage agent")
    print("   /sales    - Sales specialist")
    print("   /support  - Technical support")


if __name__ == "__main__":
    main()