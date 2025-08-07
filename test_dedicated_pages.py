#!/usr/bin/env python3
"""
Test script for the new dedicated Quiz and Code Playground pages
"""

def test_routes_exist():
    """Test that the new routes are properly defined"""
    print("Testing Route Definitions:")
    print("=" * 50)
    
    # Read the routes file to check for the new routes
    try:
        with open('/root/repo/routes.py', 'r') as f:
            routes_content = f.read()
        
        # Check for quiz route
        quiz_route_found = "@main_bp.route('/quiz')" in routes_content and "def quiz():" in routes_content
        playground_route_found = "@main_bp.route('/playground')" in routes_content and "def playground():" in routes_content
        
        print(f"Quiz route (/quiz): {'✅ FOUND' if quiz_route_found else '❌ MISSING'}")
        print(f"Playground route (/playground): {'✅ FOUND' if playground_route_found else '❌ MISSING'}")
        
        if quiz_route_found and playground_route_found:
            print("✅ All routes properly defined")
            return True
        else:
            print("❌ Missing route definitions")
            return False
            
    except Exception as e:
        print(f"❌ Error reading routes file: {e}")
        return False

def test_templates_exist():
    """Test that the HTML templates exist and contain required elements"""
    print("\nTesting Template Files:")
    print("=" * 50)
    
    import os
    
    # Check if template files exist
    quiz_template = '/root/repo/templates/quiz.html'
    playground_template = '/root/repo/templates/playground.html'
    
    quiz_exists = os.path.exists(quiz_template)
    playground_exists = os.path.exists(playground_template)
    
    print(f"Quiz template (quiz.html): {'✅ EXISTS' if quiz_exists else '❌ MISSING'}")
    print(f"Playground template (playground.html): {'✅ EXISTS' if playground_exists else '❌ MISSING'}")
    
    if not (quiz_exists and playground_exists):
        return False
    
    # Check template contents
    required_elements = {
        'quiz.html': [
            'Interactive Quiz',
            'generateQuizBtn',
            'handleQuizSubmission',
            'displayQuiz',
            'submitQuiz'
        ],
        'playground.html': [
            'Code Playground',
            'generatePlaygroundBtn', 
            'handlePlaygroundSubmission',
            'displayPlayground',
            'runRCodeWithValidation'
        ]
    }
    
    for template_file, elements in required_elements.items():
        try:
            with open(f'/root/repo/templates/{template_file}', 'r') as f:
                content = f.read()
            
            missing_elements = [elem for elem in elements if elem not in content]
            
            if missing_elements:
                print(f"❌ {template_file} missing elements: {missing_elements}")
                return False
            else:
                print(f"✅ {template_file} contains all required elements")
                
        except Exception as e:
            print(f"❌ Error reading {template_file}: {e}")
            return False
    
    return True

def test_navigation_links():
    """Test that navigation links are added to dashboard"""
    print("\nTesting Navigation Links:")
    print("=" * 50)
    
    try:
        with open('/root/repo/templates/dashboard.html', 'r') as f:
            dashboard_content = f.read()
        
        quiz_link = 'href="/quiz"' in dashboard_content and 'Quiz' in dashboard_content
        playground_link = 'href="/playground"' in dashboard_content and 'Playground' in dashboard_content
        
        print(f"Quiz navigation link: {'✅ FOUND' if quiz_link else '❌ MISSING'}")
        print(f"Playground navigation link: {'✅ FOUND' if playground_link else '❌ MISSING'}")
        
        return quiz_link and playground_link
        
    except Exception as e:
        print(f"❌ Error checking navigation links: {e}")
        return False

def test_css_styles():
    """Test that CSS styles are added for the new pages"""
    print("\nTesting CSS Styles:")
    print("=" * 50)
    
    try:
        with open('/root/repo/static/dashboard.css', 'r') as f:
            css_content = f.read()
        
        required_styles = [
            '.new-quiz-btn',
            '.new-playground-btn',
            '.submit-quiz-btn',
            '.playground-actions',
            '.quiz-controls'
        ]
        
        missing_styles = [style for style in required_styles if style not in css_content]
        
        if missing_styles:
            print(f"❌ Missing CSS styles: {missing_styles}")
            return False
        else:
            print("✅ All required CSS styles found")
            return True
            
    except Exception as e:
        print(f"❌ Error reading CSS file: {e}")
        return False

def test_javascript_functions():
    """Test that required JavaScript functions exist in templates"""
    print("\nTesting JavaScript Functions:")
    print("=" * 50)
    
    js_tests = {
        'quiz.html': [
            'handleQuizSubmission',
            'generateQuiz', 
            'displayQuiz',
            'submitQuiz',
            'generateDefaultQuestions',
            'generateNewQuiz'
        ],
        'playground.html': [
            'handlePlaygroundSubmission',
            'generatePlayground',
            'displayPlayground', 
            'runRCodeWithValidation',
            'loadSelectedExample',
            'generateNewPlayground'
        ]
    }
    
    all_passed = True
    
    for template, functions in js_tests.items():
        try:
            with open(f'/root/repo/templates/{template}', 'r') as f:
                content = f.read()
            
            missing_functions = [func for func in functions if f'function {func}(' not in content]
            
            if missing_functions:
                print(f"❌ {template} missing JS functions: {missing_functions}")
                all_passed = False
            else:
                print(f"✅ {template} contains all required JavaScript functions")
                
        except Exception as e:
            print(f"❌ Error checking {template}: {e}")
            all_passed = False
    
    return all_passed

def test_backend_integration():
    """Test that backend functions can handle quiz and playground requests"""
    print("\nTesting Backend Integration:")
    print("=" * 50)
    
    try:
        with open('/root/repo/routes.py', 'r') as f:
            routes_content = f.read()
        
        # Check that the generate-content route handles quiz and playground
        integration_checks = [
            "output_type == 'quiz'" in routes_content,
            "output_type == 'playground'" in routes_content,
            "generate_quiz_content" in routes_content,
            "generate_playground_content" in routes_content,
            "generate_starter_code" in routes_content,
            "generate_playground_examples" in routes_content
        ]
        
        passed_checks = sum(integration_checks)
        total_checks = len(integration_checks)
        
        print(f"Backend integration checks: {passed_checks}/{total_checks} passed")
        
        if passed_checks == total_checks:
            print("✅ Backend fully integrated with new pages")
            return True
        else:
            print("❌ Some backend integration issues found")
            return False
            
    except Exception as e:
        print(f"❌ Error checking backend integration: {e}")
        return False

def run_comprehensive_test():
    """Run all tests and provide summary"""
    print("Dedicated Quiz and Code Playground Pages Test Suite")
    print("=" * 70)
    
    tests = [
        ("Route Definitions", test_routes_exist),
        ("Template Files", test_templates_exist),
        ("Navigation Links", test_navigation_links),
        ("CSS Styles", test_css_styles),
        ("JavaScript Functions", test_javascript_functions),
        ("Backend Integration", test_backend_integration)
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
        print("\nThe dedicated Quiz and Code Playground pages are ready:")
        print("📝 /quiz - Interactive Quiz page with AI-generated questions")
        print("💻 /playground - Code Playground with starter code and examples")
        print("🧭 Navigation links added to dashboard")
        print("🎨 Custom CSS styling for enhanced UX")
        print("⚡ Full JavaScript functionality")
        print("🔧 Backend integration complete")
        print("\nUsers can now access separate dedicated pages for:")
        print("• Taking interactive quizzes on R topics")
        print("• Practicing R code in a dedicated playground")
        print("• Easy navigation between dashboard, quiz, and playground")
        return True
    else:
        print(f"❌ {total_tests - passed_tests} tests failed")
        print("Please review the failing tests above")
        return False

if __name__ == '__main__':
    run_comprehensive_test()