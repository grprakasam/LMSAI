#!/usr/bin/env python3
"""
Test script to verify navigation links and routes are working correctly
"""

def test_routes_accessibility():
    """Test that all routes are properly defined and accessible"""
    print("Testing Route Accessibility:")
    print("=" * 50)
    
    try:
        # Import the Flask app components
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from routes import main_bp
        from flask import Flask
        
        # Create a test app
        app = Flask(__name__)
        app.register_blueprint(main_bp)
        
        # Get all the routes
        routes = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint.startswith('main.'):
                routes.append({
                    'endpoint': rule.endpoint,
                    'route': str(rule.rule),
                    'methods': list(rule.methods - {'HEAD', 'OPTIONS'})
                })
        
        # Check for our specific routes
        required_routes = [
            ('main.index', '/'),
            ('main.dashboard', '/dashboard'),
            ('main.quiz', '/quiz'),
            ('main.playground', '/playground')
        ]
        
        found_routes = {route['endpoint']: route['route'] for route in routes}
        
        print("Found routes:")
        for route in routes:
            print(f"  {route['endpoint']}: {route['route']} {route['methods']}")
        
        print("\nChecking required routes:")
        all_found = True
        for endpoint, expected_route in required_routes:
            if endpoint in found_routes:
                actual_route = found_routes[endpoint]
                if actual_route == expected_route:
                    print(f"✅ {endpoint}: {expected_route}")
                else:
                    print(f"❌ {endpoint}: expected {expected_route}, got {actual_route}")
                    all_found = False
            else:
                print(f"❌ {endpoint}: NOT FOUND")
                all_found = False
        
        return all_found
        
    except Exception as e:
        print(f"❌ Error testing routes: {e}")
        return False

def test_template_syntax():
    """Test that templates have correct url_for syntax"""
    print("\nTesting Template URL Syntax:")
    print("=" * 50)
    
    templates_to_check = {
        'templates/dashboard.html': ['main.quiz', 'main.playground'],
        'templates/quiz.html': ['main.dashboard', 'main.playground'],
        'templates/playground.html': ['main.dashboard', 'main.quiz']
    }
    
    all_good = True
    
    for template_path, expected_refs in templates_to_check.items():
        print(f"\nChecking {template_path}:")
        try:
            with open(template_path, 'r') as f:
                content = f.read()
            
            for ref in expected_refs:
                if f"url_for('{ref}')" in content:
                    print(f"  ✅ {ref}")
                else:
                    print(f"  ❌ {ref} - not found or incorrect syntax")
                    all_good = False
                    
        except Exception as e:
            print(f"  ❌ Error reading {template_path}: {e}")
            all_good = False
    
    return all_good

def test_navigation_structure():
    """Test that navigation links are properly structured in templates"""
    print("\nTesting Navigation Structure:")
    print("=" * 50)
    
    templates = ['templates/dashboard.html', 'templates/quiz.html', 'templates/playground.html']
    
    required_elements = [
        'class="btn btn-sm"',
        'fas fa-question-circle',  # Quiz icon
        'fas fa-code',  # Playground icon
        'navbar',
        'user-menu'
    ]
    
    all_good = True
    
    for template_path in templates:
        print(f"\nChecking {template_path}:")
        try:
            with open(template_path, 'r') as f:
                content = f.read()
            
            for element in required_elements:
                if element in content:
                    print(f"  ✅ {element}")
                else:
                    print(f"  ❌ {element} - missing")
                    all_good = False
                    
            # Check for proper Flask template syntax
            if '{{ url_for(' in content:
                print(f"  ✅ Flask url_for syntax found")
            else:
                print(f"  ❌ Flask url_for syntax missing")
                all_good = False
                
        except Exception as e:
            print(f"  ❌ Error reading {template_path}: {e}")
            all_good = False
    
    return all_good

def test_route_functions():
    """Test that route functions are properly defined"""
    print("\nTesting Route Functions:")
    print("=" * 50)
    
    try:
        with open('routes.py', 'r') as f:
            routes_content = f.read()
        
        required_functions = [
            ('def dashboard():', 'render_template(\'dashboard.html\''),
            ('def quiz():', 'render_template(\'quiz.html\''),
            ('def playground():', 'render_template(\'playground.html\'')
        ]
        
        all_good = True
        
        for func_def, expected_return in required_functions:
            if func_def in routes_content:
                print(f"✅ {func_def}")
                if expected_return in routes_content:
                    print(f"  ✅ Returns correct template")
                else:
                    print(f"  ❌ Template return not found")
                    all_good = False
            else:
                print(f"❌ {func_def} - not found")
                all_good = False
        
        return all_good
        
    except Exception as e:
        print(f"❌ Error reading routes.py: {e}")
        return False

def generate_fix_suggestions():
    """Generate suggestions for common fixes"""
    print("\nCommon Fix Suggestions:")
    print("=" * 50)
    
    suggestions = [
        "1. Ensure Flask app is running and accessible",
        "2. Check that blueprints are properly registered",
        "3. Verify login_required decorator isn't blocking access",
        "4. Check browser console for JavaScript errors",
        "5. Ensure all templates exist in templates/ directory", 
        "6. Verify CSS classes aren't interfering with click events",
        "7. Check that no JavaScript preventDefault is blocking links",
        "8. Test with different browsers",
        "9. Check Flask development server logs for errors",
        "10. Verify database is properly initialized"
    ]
    
    for suggestion in suggestions:
        print(f"  {suggestion}")

def run_comprehensive_test():
    """Run all navigation tests"""
    print("Navigation Links Test Suite")
    print("=" * 70)
    
    tests = [
        ("Route Accessibility", test_routes_accessibility),
        ("Template URL Syntax", test_template_syntax),
        ("Navigation Structure", test_navigation_structure),
        ("Route Functions", test_route_functions)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed_tests += 1
        except Exception as e:
            print(f"❌ {test_name} test failed with error: {e}")
    
    print("\n" + "=" * 70)
    print(f"TEST SUMMARY: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED!")
        print("\nNavigation links should be working correctly.")
        print("If links still don't work, check:")
        print("• Flask server is running")
        print("• User is logged in (login_required)")
        print("• Browser console for JavaScript errors")
        print("• Network tab for failed requests")
    else:
        print(f"❌ {total_tests - passed_tests} tests failed")
        generate_fix_suggestions()

if __name__ == '__main__':
    run_comprehensive_test()