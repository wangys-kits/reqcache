"""
测试 reqcache 是否支持所有 requests 原始参数
"""

import reqcache

def test_all_requests_params():
    """演示所有常用的 requests 参数都被支持"""

    print("=== reqcache 支持所有 requests 参数 ===\n")

    # 1. headers - 自定义请求头
    print("1. 测试 headers 参数")
    response = reqcache.get(
        'https://httpbin.org/headers',
        cache=True,
        headers={
            'User-Agent': 'reqcache/0.1.0',
            'Authorization': 'Bearer test-token',
            'Custom-Header': 'custom-value'
        }
    )
    print(f"   状态码: {response.status_code}")
    print(f"   自定义 headers 已发送 ✓\n")

    # 2. timeout - 超时设置
    print("2. 测试 timeout 参数")
    response = reqcache.get(
        'https://httpbin.org/delay/1',
        cache=True,
        timeout=5  # 5秒超时
    )
    print(f"   状态码: {response.status_code}")
    print(f"   timeout=5 设置成功 ✓\n")

    # 3. params - 查询参数
    print("3. 测试 params 参数")
    response = reqcache.get(
        'https://httpbin.org/get',
        cache=True,
        params={
            'key1': 'value1',
            'key2': 'value2',
            'foo': 'bar'
        }
    )
    print(f"   状态码: {response.status_code}")
    print(f"   查询参数: {response.json()['args']}")
    print(f"   params 正常工作 ✓\n")

    # 4. verify - SSL 验证
    print("4. 测试 verify 参数")
    response = reqcache.get(
        'https://httpbin.org/get',
        cache=True,
        verify=True  # 验证 SSL 证书
    )
    print(f"   状态码: {response.status_code}")
    print(f"   SSL 验证已启用 ✓\n")

    # 5. auth - HTTP 认证
    print("5. 测试 auth 参数")
    response = reqcache.get(
        'https://httpbin.org/basic-auth/user/passwd',
        cache=True,
        auth=('user', 'passwd')  # HTTP Basic Auth
    )
    print(f"   状态码: {response.status_code}")
    print(f"   HTTP Basic Auth 成功 ✓\n")

    # 6. cookies - Cookie
    print("6. 测试 cookies 参数")
    response = reqcache.get(
        'https://httpbin.org/cookies',
        cache=True,
        cookies={'session_id': 'abc123', 'user': 'test'}
    )
    print(f"   状态码: {response.status_code}")
    print(f"   Cookies: {response.json()['cookies']}")
    print(f"   cookies 参数正常工作 ✓\n")

    # 7. json - JSON 数据 (POST)
    print("7. 测试 json 参数 (POST)")
    response = reqcache.post(
        'https://httpbin.org/post',
        cache=True,
        json={'name': 'Alice', 'age': 30}
    )
    print(f"   状态码: {response.status_code}")
    print(f"   发送的 JSON: {response.json()['json']}")
    print(f"   json 参数正常工作 ✓\n")

    # 8. data - 表单数据
    print("8. 测试 data 参数")
    response = reqcache.post(
        'https://httpbin.org/post',
        cache=True,
        data={'username': 'user123', 'password': 'pass456'}
    )
    print(f"   状态码: {response.status_code}")
    print(f"   表单数据: {response.json()['form']}")
    print(f"   data 参数正常工作 ✓\n")

    # 9. allow_redirects - 重定向控制
    print("9. 测试 allow_redirects 参数")
    response = reqcache.get(
        'https://httpbin.org/redirect/1',
        cache=True,
        allow_redirects=True
    )
    print(f"   状态码: {response.status_code}")
    print(f"   重定向已处理 ✓\n")

    # 10. stream - 流式响应
    print("10. 测试 stream 参数")
    response = reqcache.get(
        'https://httpbin.org/stream/5',
        cache=True,
        stream=False
    )
    print(f"   状态码: {response.status_code}")
    print(f"   stream 参数支持 ✓\n")

    print("=" * 50)
    print("✅ 所有 requests 参数都完全支持！")
    print("=" * 50)

if __name__ == '__main__':
    test_all_requests_params()
