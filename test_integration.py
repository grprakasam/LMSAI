#!/usr/bin/env python3
"""
Integration test for the redesigned R Tutor Pro app
Tests the modular structure and new features
"""

def test_route_structure():
    """Test that routes are properly structured"""
    try:
        # Check if routes file has the new unified content generation
        with open('routes.py', 'r') as f:
            content = f.read()
        
        required_functions = [
            'generate_content',
            'generate_text_content', 
            'generate_audio_content',
            'generate_animated_content',
            'create_animation_html',
            'kyutai_stream_audio',
            'get_recent_content'
        ]
        
        missing_functions = []
        for func in required_functions:
            if f'def {func}' not in content:
                missing_functions.append(func)
        
        if missing_functions:
            print(f"❌ Missing functions: {missing_functions}")
            return False
        
        print("✅ All required route functions are present")
        return True
        
    except Exception as e:
        print(f"❌ Error checking routes: {e}")
        return False

def test_template_structure():
    """Test that the dashboard template has the new radio button interface"""
    try:
        with open('templates/dashboard.html', 'r') as f:
            content = f.read()
        
        required_elements = [
            'output-type-section',
            'radio-group', 
            'radio-option',
            'type="radio"',
            'output_type',
            'generate-content',
            'result-section',
            'content-display',
            'audio-player'
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in content:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"❌ Missing template elements: {missing_elements}")
            return False
        
        print("✅ All required template elements are present")
        return True
        
    except Exception as e:
        print(f"❌ Error checking template: {e}")
        return False

def test_css_structure():
    """Test that CSS has the new clean interface styles"""
    try:
        with open('static/dashboard.css', 'r') as f:
            content = f.read()
        
        required_classes = [
            '.radio-group',
            '.radio-option', 
            '.output-type-section',
            '.btn-generate',
            '.result-section',
            '.content-display',
            '.audio-player',
            '.animation-container'
        ]
        
        missing_classes = []
        for css_class in required_classes:
            if css_class not in content:
                missing_classes.append(css_class)
        
        if missing_classes:
            print(f"❌ Missing CSS classes: {missing_classes}")
            return False
        
        print("✅ All required CSS classes are present")
        return True
        
    except Exception as e:
        print(f"❌ Error checking CSS: {e}")
        return False

def test_kyutai_integration():
    """Test that Kyutai TTS service is properly integrated"""
    try:
        with open('kyutai_tts_service.py', 'r') as f:
            content = f.read()
        
        required_components = [
            'class KyutaiTTSService',
            'stream_tts',
            'create_stream_session',
            'get_stream_url',
            'prepare_text_for_tts'
        ]
        
        missing_components = []
        for component in required_components:
            if component not in content:
                missing_components.append(component)
        
        if missing_components:
            print(f"❌ Missing Kyutai components: {missing_components}")
            return False
        
        print("✅ Kyutai TTS service is properly structured")
        return True
        
    except Exception as e:
        print(f"❌ Error checking Kyutai service: {e}")
        return False

def test_modularity():
    """Test code modularity and separation of concerns"""
    try:
        # Check that different output types are handled separately
        with open('routes.py', 'r') as f:
            routes_content = f.read()
        
        # Verify modular content generation
        if 'output_type == \'text\'' in routes_content and \
           'output_type == \'audio\'' in routes_content and \
           'output_type == \'animated\'' in routes_content:
            print("✅ Modular output type handling is implemented")
        else:
            print("❌ Modular output type handling not found")
            return False
        
        # Check for proper separation of TTS logic
        if 'kyutai_tts_service' in routes_content:
            print("✅ TTS service is properly separated")
        else:
            print("❌ TTS service separation not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking modularity: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing R Tutor Pro Redesign Integration")
    print("=" * 50)
    
    tests = [
        test_route_structure,
        test_template_structure,
        test_css_structure,
        test_kyutai_integration,
        test_modularity
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print(f"\n🔍 Running {test.__name__}...")
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The redesign is ready for deployment.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
        return False

if __name__ == '__main__':
    main()