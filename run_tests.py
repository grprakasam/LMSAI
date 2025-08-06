#!/usr/bin/env python3
# run_tests.py - Test runner script
import os
import sys
import subprocess

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n🔍 {description}")
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ {description} - FAILED")
            if result.stderr:
                print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def main():
    """Run all tests and checks"""
    print("🧪 Running R Tutor Pro Tests and Quality Checks")
    print("=" * 50)
    
    results = []
    
    # Test Python syntax compilation
    print("\n📝 Testing Python syntax...")
    py_files = [
        'app_main.py',
        'routes.py',
        'test_integration.py',
        'app/core/config.py',
        'app/core/extensions.py',
        'app/core/factory.py',
        'app/models/user.py',
        'app/models/tutorial.py',
        'app/models/usage.py'
    ]
    
    syntax_ok = True
    for py_file in py_files:
        if os.path.exists(py_file):
            result = run_command(f"python3 -m py_compile {py_file}", f"Syntax check: {py_file}")
            if not result:
                syntax_ok = False
        else:
            print(f"⚠️  File not found: {py_file}")
    
    results.append(("Python Syntax", syntax_ok))
    
    # Test imports (without Flask dependencies)
    print("\n📦 Testing import structure...")
    import_tests = [
        "import app.core.config; print('Config OK')",
        "import app.models.user; print('User model OK')",
        "from app.models import User, Tutorial; print('Models OK')"
    ]
    
    imports_ok = True
    for test in import_tests:
        try:
            exec(test)
            print(f"✅ Import test passed")
        except Exception as e:
            print(f"❌ Import test failed: {e}")
            imports_ok = False
    
    results.append(("Import Structure", imports_ok))
    
    # Check file structure
    print("\n📁 Checking modular file structure...")
    required_dirs = [
        'app',
        'app/core',
        'app/models', 
        'app/services',
        'app/utils',
        'app/auth',
        'app/api',
        'static',
        'templates'
    ]
    
    structure_ok = True
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✅ Directory exists: {dir_path}")
        else:
            print(f"❌ Missing directory: {dir_path}")
            structure_ok = False
    
    results.append(("File Structure", structure_ok))
    
    # Check critical files
    print("\n📄 Checking critical files...")
    critical_files = [
        'app_main.py',
        'requirements.txt',
        'Procfile',
        'templates/index.html',
        'templates/dashboard.html',
        'static/style.css'
    ]
    
    files_ok = True
    for file_path in critical_files:
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            print(f"✅ File OK: {file_path}")
        else:
            print(f"❌ Missing or empty: {file_path}")
            files_ok = False
    
    results.append(("Critical Files", files_ok))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<20} {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Code is ready for deployment.")
        return 0
    else:
        print("💥 SOME TESTS FAILED! Please review the issues above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())