from request_handler.submit_request_handler import process_template

def test_process_template():
    """Test the process_template function with various test cases"""
    print("Testing process_template function...")
    
    # Test data
    data = {
        "username": "testuser",
        "password": "testpass123",
        "email": "test@example.com",
        "id": 12345,
        "active": True
    }
    
    # Test case 1: Simple string replacement
    template1 = "Hello {{username}}, your email is {{email}}"
    result1 = process_template(template1, data)
    print("\nTest case 1 - Simple string replacement:")
    print(f"Template: {template1}")
    print(f"Result:   {result1}")
    
    # Test case 2: Dictionary with nested placeholders
    template2 = {
        "user": {
            "name": "{{username}}",
            "email": "{{email}}",
            "id": "{{id}}"
        },
        "credentials": {
            "password": "{{password}}",
            "active": "{{active}}"
        }
    }
    result2 = process_template(template2, data)
    print("\nTest case 2 - Dictionary with nested placeholders:")
    print(f"Template: {template2}")
    print(f"Result:   {result2}")
    
    # Test case 3: List with placeholders
    template3 = [
        "User {{username}}",
        {"id": "{{id}}", "email": "{{email}}"},
        ["{{password}}", "{{active}}"]
    ]
    result3 = process_template(template3, data)
    print("\nTest case 3 - List with placeholders:")
    print(f"Template: {template3}")
    print(f"Result:   {result3}")
    
    # Test case 4: Missing placeholder
    template4 = {"name": "{{username}}", "role": "{{role}}"}
    result4 = process_template(template4, data)
    print("\nTest case 4 - Missing placeholder:")
    print(f"Template: {template4}")
    print(f"Result:   {result4}")
    
    # Test case 5: Real-world API template example
    template5 = {
        "http_method": "POST",
        "endpoint_path": "/api/login",
        "request_payload_template": {
            "username": "{{username}}",
            "password": "{{password}}",
            "remember_me": True
        }
    }
    result5 = process_template(template5, data)
    print("\nTest case 5 - Real-world API template example:")
    print(f"Template: {template5}")
    print(f"Result:   {result5}")

if __name__ == "__main__":
    test_process_template()
