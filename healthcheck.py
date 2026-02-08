#!/usr/bin/env python3
"""
CaseCrawl Health Check Script
Verifies that all services are running correctly
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def check(result, message):
    if result:
        print(f"{Colors.GREEN}✓{Colors.END} {message}")
        return True
    else:
        print(f"{Colors.RED}✗{Colors.END} {message}")
        return False

def warn(message):
    print(f"{Colors.YELLOW}⚠{Colors.END} {message}")

def info(message):
    print(f"{Colors.BLUE}ℹ{Colors.END} {message}")

def check_docker_services():
    """Check if Docker services are running"""
    print(f"\n{Colors.BOLD}Docker Services:{Colors.END}")
    
    import subprocess
    try:
        result = subprocess.run(
            ["docker", "compose", "ps", "--format", "table {{.Service}}\t{{.Status}}"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent)
        )
        if "running" in result.stdout.lower():
            for line in result.stdout.strip().split('\n')[1:]:  # Skip header
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        service, status = parts[0], parts[1]
                        if 'running' in status.lower():
                            check(True, f"{service}: {status}")
                        else:
                            check(False, f"{service}: {status}")
            return True
        else:
            check(False, "No Docker services running")
            return False
    except Exception as e:
        check(False, f"Docker check failed: {e}")
        return False

def check_database():
    """Check database connection"""
    print(f"\n{Colors.BOLD}Database:{Colors.END}")
    
    try:
        import asyncpg
        from app.core.config import get_settings
        
        settings = get_settings()
        
        async def test_db():
            conn = await asyncpg.connect(settings.database_url.replace('postgresql+asyncpg://', 'postgresql://'))
            result = await conn.fetchval("SELECT 1")
            await conn.close()
            return result == 1
        
        result = asyncio.run(test_db())
        return check(result, "PostgreSQL connection")
    except ImportError:
        warn("asyncpg not installed, skipping database check")
        return None
    except Exception as e:
        return check(False, f"Database connection: {e}")

def check_redis():
    """Check Redis connection"""
    print(f"\n{Colors.BOLD}Redis:{Colors.END}")
    
    try:
        import redis
        from app.core.config import get_settings
        
        settings = get_settings()
        r = redis.from_url(settings.redis_url)
        r.ping()
        return check(True, "Redis connection")
    except ImportError:
        warn("redis not installed, skipping Redis check")
        return None
    except Exception as e:
        return check(False, f"Redis connection: {e}")

def check_backend_api():
    """Check if backend API is running"""
    print(f"\n{Colors.BOLD}Backend API:{Colors.END}")
    
    try:
        import urllib.request
        import json
        
        req = urllib.request.Request(
            "http://localhost:18000/health",
            method="GET",
            headers={"Accept": "application/json"}
        )
        
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                if data.get("status") == "healthy":
                    check(True, "API is healthy")
                    info(f"  App: {data.get('app', 'Unknown')}")
                    info(f"  Version: {data.get('version', 'Unknown')}")
                    return True
                else:
                    return check(False, "API health check failed")
        except urllib.error.HTTPError as e:
            return check(False, f"API returned error: {e.code}")
    except Exception as e:
        return check(False, f"API not accessible: {e}")

def check_frontend():
    """Check if frontend is running"""
    print(f"\n{Colors.BOLD}Frontend:{Colors.END}")
    
    try:
        import urllib.request
        
        req = urllib.request.Request(
            "http://localhost:13000",
            method="GET"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    return check(True, "Frontend is running")
                else:
                    return check(False, f"Frontend returned status {response.status}")
        except urllib.error.HTTPError as e:
            return check(False, f"Frontend returned error: {e.code}")
    except Exception as e:
        return check(False, f"Frontend not accessible: {e}")

def check_celery():
    """Check if Celery is running"""
    print(f"\n{Colors.BOLD}Celery Worker:{Colors.END}")
    
    try:
        import subprocess
        result = subprocess.run(
            ["pgrep", "-f", "celery.*worker"],
            capture_output=True
        )
        if result.returncode == 0:
            return check(True, "Celery worker is running")
        else:
            return check(False, "Celery worker not found (run 'make worker')")
    except Exception as e:
        return check(False, f"Celery check failed: {e}")

def main():
    print(f"""
{Colors.BOLD}
   ____                __________      __
  / ___|__ _ ___  ___ / / ____\ \    / /
 | |   / _` / __|/ _ \ / |  __ \ \  / / 
 | |__| (_| \__ \  __/ || |___| \ \/ /  
  \____\__,_|___/\___/ ||_____|  \__/   
                     \_/
{Colors.END}
{Colors.BLUE}Health Check{Colors.END}
""")
    
    checks = []
    
    # Run checks
    checks.append(("Docker", check_docker_services()))
    checks.append(("Database", check_database()))
    checks.append(("Redis", check_redis()))
    checks.append(("Backend API", check_backend_api()))
    checks.append(("Frontend", check_frontend()))
    checks.append(("Celery", check_celery()))
    
    # Summary
    print(f"\n{Colors.BOLD}{'='*50}{Colors.END}")
    
    passed = sum(1 for _, result in checks if result is True)
    failed = sum(1 for _, result in checks if result is False)
    skipped = sum(1 for _, result in checks if result is None)
    
    print(f"\n{Colors.BOLD}Summary:{Colors.END}")
    print(f"  {Colors.GREEN}Passed:{Colors.END}   {passed}")
    print(f"  {Colors.RED}Failed:{Colors.END}   {failed}")
    if skipped > 0:
        print(f"  {Colors.YELLOW}Skipped:{Colors.END}  {skipped}")
    
    if failed == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}All checks passed! ✓{Colors.END}")
        print(f"\nAccess your application at:")
        print(f"  - Frontend: http://localhost:13000")
        print(f"  - API Docs: http://localhost:18000/docs")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}Some checks failed.{Colors.END}")
        print(f"\nTroubleshooting:")
        print(f"  1. Make sure Docker Desktop is running: docker compose up -d")
        print(f"  2. Start the backend: make dev")
        print(f"  3. Start the frontend: make dev-frontend")
        print(f"  4. Start Celery: make worker")
        return 1

if __name__ == "__main__":
    sys.exit(main())
