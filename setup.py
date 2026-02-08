#!/usr/bin/env python3
"""
CaseCrawl Quickstart Setup Script
Cross-platform setup for Mac, Windows, and Linux
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_step(message):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{message}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def run_command(cmd, cwd=None, shell=False, check=True):
    """Run a command and return success status"""
    try:
        if shell and isinstance(cmd, list):
            cmd = ' '.join(cmd)
        result = subprocess.run(
            cmd if shell else cmd.split() if isinstance(cmd, str) else cmd,
            cwd=cwd,
            shell=shell,
            check=check,
            capture_output=True,
            text=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr
    except FileNotFoundError:
        return False, f"Command not found: {cmd[0] if isinstance(cmd, list) else cmd.split()[0]}"

def check_prerequisites():
    """Check if required tools are installed"""
    print_step("Checking Prerequisites")
    
    required = {
        'python': ('python3 --version', 'Python 3.11+'),
        'docker': ('docker --version', 'Docker'),
        'npm': ('npm --version', 'Node.js/npm'),
    }
    
    missing = []
    for name, (cmd, desc) in required.items():
        success, output = run_command(cmd.split()[0] if ' ' in cmd else cmd, check=False)
        if success:
            print_success(f"{desc}: {output.strip() if output else 'Installed'}")
        else:
            print_error(f"{desc}: Not found")
            missing.append(desc)
    
    if missing:
        print_error(f"Missing prerequisites: {', '.join(missing)}")
        print("Please install them and run this script again.")
        sys.exit(1)
    
    return True

def setup_python_environment():
    """Create and setup Python virtual environment"""
    print_step("Setting up Python Environment")
    
    project_root = Path(__file__).parent.absolute()
    venv_path = project_root / "venv"
    
    # Create virtual environment
    if venv_path.exists():
        print_warning("Virtual environment already exists, skipping creation")
    else:
        print("Creating virtual environment...")
        success, output = run_command([sys.executable, "-m", "venv", str(venv_path)])
        if not success:
            print_error(f"Failed to create virtual environment: {output}")
            return False
        print_success("Virtual environment created")
    
    # Determine pip/python paths
    if platform.system() == "Windows":
        pip_cmd = str(venv_path / "Scripts" / "pip")
        python_cmd = str(venv_path / "Scripts" / "python")
    else:
        pip_cmd = str(venv_path / "bin" / "pip")
        python_cmd = str(venv_path / "bin" / "python")
    
    # Upgrade pip
    print("Upgrading pip...")
    run_command([python_cmd, "-m", "pip", "install", "--upgrade", "pip"], check=False)
    
    # Install requirements with fixes
    print("Installing backend dependencies (this may take a few minutes)...")
    req_file = project_root / "backend" / "requirements.txt"
    
    # Install numpy<2 first (compatibility fix)
    print("  Installing NumPy (compatibility version)...")
    success, output = run_command([pip_cmd, "install", "numpy<2", "--quiet"], check=False)
    if not success:
        print_warning(f"NumPy install warning: {output}")
    
    # Install main requirements
    success, output = run_command([pip_cmd, "install", "-r", str(req_file)], check=False)
    if not success:
        print_error(f"Failed to install requirements: {output}")
        return False
    
    print_success("Backend dependencies installed")
    
    # Install Playwright browsers
    print("Installing Playwright browsers (this may take a while)...")
    success, output = run_command([python_cmd, "-m", "playwright", "install", "chromium"], check=False)
    if not success:
        print_warning(f"Playwright install warning: {output}")
    else:
        print_success("Playwright browsers installed")
    
    return python_cmd, pip_cmd

def setup_frontend():
    """Setup frontend dependencies"""
    print_step("Setting up Frontend")
    
    project_root = Path(__file__).parent.absolute()
    frontend_path = project_root / "frontend"
    
    # Clean install
    node_modules = frontend_path / "node_modules"
    package_lock = frontend_path / "package-lock.json"
    
    if node_modules.exists():
        print("Cleaning existing node_modules...")
        shutil.rmtree(node_modules)
    if package_lock.exists():
        package_lock.unlink()
    
    # Install dependencies
    print("Installing frontend dependencies...")
    success, output = run_command(["npm", "install"], cwd=str(frontend_path), check=False)
    if not success:
        print_error(f"Failed to install frontend dependencies: {output}")
        return False
    
    print_success("Frontend dependencies installed")
    return True

def setup_docker_services():
    """Start Docker services"""
    print_step("Starting Docker Services")
    
    project_root = Path(__file__).parent.absolute()
    
    # Check if docker compose is available
    success, _ = run_command(["docker", "compose", "version"], check=False)
    compose_cmd = ["docker", "compose"] if success else ["docker-compose"]
    
    print("Starting PostgreSQL and Redis...")
    success, output = run_command(compose_cmd + ["up", "-d", "db", "redis"], cwd=str(project_root), check=False)
    if not success:
        print_error(f"Failed to start Docker services: {output}")
        print("Make sure Docker Desktop is running")
        return False
    
    print_success("Docker services started")
    print("  - PostgreSQL on port 15432")
    print("  - Redis on port 16379")
    return True

def setup_database(python_cmd):
    """Setup database tables"""
    print_step("Setting up Database")
    
    project_root = Path(__file__).parent.absolute()
    backend_path = project_root / "backend"
    
    # Wait for PostgreSQL to be ready
    print("Waiting for PostgreSQL to be ready...")
    import time
    time.sleep(3)
    
    # Create tables via Python script (avoids alembic issues)
    print("Creating database tables...")
    setup_script = """
import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import get_settings
from app.models import Base

async def setup():
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("Database tables created successfully!")

asyncio.run(setup())
"""
    
    success, output = run_command(
        [python_cmd, "-c", setup_script],
        cwd=str(backend_path),
        check=False
    )
    
    if not success:
        print_warning(f"Database setup warning: {output}")
        print("Tables will be created automatically when the app starts")
    else:
        print_success("Database tables created")
    
    return True

def create_env_file():
    """Create .env file if it doesn't exist"""
    project_root = Path(__file__).parent.absolute()
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"
    
    if env_file.exists():
        print_step("Environment file already exists, skipping creation")
        return True
    
    print_step("Creating .env file")
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print_success("Created .env from .env.example")
        print("Please review and update the .env file with your settings")
    else:
        # Create default .env
        default_env = """# Application Settings
DEBUG=true
LOG_LEVEL=INFO
STRUCTURED_LOGGING=false

# Database (using non-standard port to avoid conflicts)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:15432/casecrawl

# Redis (using non-standard port to avoid conflicts)
REDIS_URL=redis://localhost:16379/0

# Security
SECRET_KEY=your-secret-key-change-in-production

# File Storage
DOWNLOAD_DIR=./data/downloads
FILE_RETENTION_DAYS=30

# Westlaw Settings
WESTLAW_BASE_URL=https://www.westlawasia.com

# Rate Limiting
SEARCHES_PER_MINUTE=4
DOWNLOADS_PER_MINUTE=3
MAX_CONCURRENT_BATCHES=1

# Browser Configuration
BROWSER_HEADLESS=false
BROWSER_VIEWPORT_WIDTH=1920
BROWSER_VIEWPORT_HEIGHT=1080
BROWSER_LOCALE=en-GB
BROWSER_TIMEZONE=Asia/Hong_Kong

# Behavioral Delays (seconds)
DELAY_BETWEEN_ACTIONS_MIN=3.0
DELAY_BETWEEN_ACTIONS_MAX=8.0
PAGE_LOAD_WAIT_MIN=3.0
PAGE_LOAD_WAIT_MAX=6.0
POST_SEARCH_WAIT_MIN=4.0
POST_SEARCH_WAIT_MAX=7.0

# Typing delays (ms)
TYPING_DELAY_MIN=50
TYPING_DELAY_MAX=150
"""
        with open(env_file, 'w') as f:
            f.write(default_env)
        print_success("Created default .env file")
    
    return True

def print_final_instructions(python_cmd):
    """Print final setup instructions"""
    print_step("Setup Complete!")
    
    project_root = Path(__file__).parent.absolute()
    
    print(f"""
{Colors.GREEN}CaseCrawl has been successfully set up!{Colors.END}

{Colors.BOLD}To start the application:{Colors.END}

1. {Colors.YELLOW}Start the backend API:{Colors.END}
   cd backend
   {python_cmd} -m uvicorn app.main:app --reload --port 18000

2. {Colors.YELLOW}Start the frontend (in a new terminal):{Colors.END}
   cd frontend
   npm run dev

3. {Colors.YELLOW}Start the Celery worker (in a new terminal):{Colors.END}
   cd backend
   {python_cmd} -m celery -A app.core.celery worker --loglevel=info

{Colors.BOLD}Access Points:{Colors.END}
  - Frontend:    http://localhost:13000
  - API Docs:    http://localhost:18000/docs
  - Flower:      http://localhost:15555 (optional, run 'make flower')

{Colors.BOLD}Useful Commands:{Colors.END}
  - Stop Docker:     docker compose down
  - View logs:       docker compose logs -f
  - Run tests:       cd backend && pytest tests/

{Colors.BOLD}Next Steps:{Colors.END}
  1. Update the .env file with your Westlaw credentials
  2. Open http://localhost:13000 in your browser
  3. Upload a CSV file with case information

{Colors.YELLOW}For issues, check the logs or run setup.py again.{Colors.END}
""")

def main():
    """Main setup function"""
    print(f"""
{Colors.BOLD}
   ____                __________      __
  / ___|__ _ ___  ___ / / ____\ \    / /
 | |   / _` / __|/ _ \ / |  __ \ \  / / 
 | |__| (_| \__ \  __/ || |___| \ \/ /  
  \____\__,_|___/\___/ ||_____|  \__/   
                     \_/
{Colors.END}
{Colors.BLUE}Westlaw Asia Crawler - Setup Script{Colors.END}
{Colors.BLUE}Platform: {platform.system()} {platform.machine()}{Colors.END}
""")
    
    try:
        # Run setup steps
        check_prerequisites()
        python_cmd, pip_cmd = setup_python_environment()
        setup_frontend()
        create_env_file()
        setup_docker_services()
        setup_database(python_cmd)
        
        print_final_instructions(python_cmd)
        
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
