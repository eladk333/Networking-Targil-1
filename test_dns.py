#!/usr/bin/env python3
"""
Comprehensive DNS Resolver Test Script
Tests all scenarios: direct A records, NS delegation, caching, and non-existent domains
"""

import socket
import subprocess
import time
import sys
from typing import Optional

# Configuration
RESOLVER_PORT = 5555
PARENT_SERVER_PORT = 12345
CHILD_SERVER_PORT = 22222
GRANDCHILD_SERVER_PORT = 33333
CACHE_TIMEOUT = 20

class DNSClient:
    """Simple DNS client for testing"""
    def __init__(self, server_ip: str, server_port: int):
        self.server_ip = server_ip
        self.server_port = server_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(3.0)
    
    def query(self, domain: str) -> Optional[str]:
        """Send a DNS query and return the response"""
        try:
            self.sock.sendto(domain.encode('utf-8'), (self.server_ip, self.server_port))
            data, _ = self.sock.recvfrom(1024)
            response = data.decode('utf-8').strip()
            return response
        except socket.timeout:
            return None
        except Exception as e:
            print(f"Error querying {domain}: {e}")
            return None
    
    def close(self):
        self.sock.close()


def start_server(port: int, zone_file: str) -> subprocess.Popen:
    """Start a DNS server process"""
    cmd = ['python3', 'father_server.py', str(port), zone_file]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(0.5)  # Give server time to start
    return proc


def start_resolver(port: int, parent_ip: str, parent_port: int, cache_timeout: int) -> subprocess.Popen:
    """Start a DNS resolver process"""
    cmd = ['python3', 'resolver_server.py', str(port), parent_ip, str(parent_port), str(cache_timeout)]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(0.5)  # Give resolver time to start
    return proc


def extract_ip(response: Optional[str]) -> str:
    """Extract IP from DNS response"""
    if response is None:
        return "no response"
    if response == "non-existent domain":
        return response
    try:
        parts = response.split(',')
        if len(parts) == 3:
            return parts[1]  # Return IP address
        return response
    except:
        return response


def run_tests():
    """Run comprehensive DNS tests"""
    print("=" * 60)
    print("DNS Resolver Comprehensive Test Suite")
    print("=" * 60)
    
    # Start servers
    print("\n[1] Starting DNS servers...")
    parent_server = start_server(PARENT_SERVER_PORT, 'zone.txt')
    print(f"   ✓ Parent server started on port {PARENT_SERVER_PORT} (zone.txt)")
    
    child_server = start_server(CHILD_SERVER_PORT, 'zone2.txt')
    print(f"   ✓ Child server started on port {CHILD_SERVER_PORT} (zone2.txt)")
    
    grandchild_server = start_server(GRANDCHILD_SERVER_PORT, 'zone3.txt')
    print(f"   ✓ Grandchild server started on port {GRANDCHILD_SERVER_PORT} (zone3.txt)")
    
    # Start resolver
    print(f"\n[2] Starting DNS resolver...")
    resolver = start_resolver(RESOLVER_PORT, '127.0.0.1', PARENT_SERVER_PORT, CACHE_TIMEOUT)
    print(f"   ✓ Resolver started on port {RESOLVER_PORT}")
    
    time.sleep(1)  # Give everything time to initialize
    
    # Create test client
    client = DNSClient('127.0.0.1', RESOLVER_PORT)
    
    # Test counters
    total_tests = 0
    passed_tests = 0
    
    print("\n" + "=" * 60)
    print("Running Tests")
    print("=" * 60)
    
    # Test 1: Direct A record from parent server
    print("\n[Test 1] Direct A record lookup (biu.ac.il)")
    total_tests += 1
    response = client.query('biu.ac.il')
    ip = extract_ip(response)
    if response and ip == '1.2.3.4':
        print(f"   ✓ PASS: Got correct IP {ip}")
        passed_tests += 1
    else:
        print(f"   ✗ FAIL: Expected 1.2.3.4, got {ip} (response: {response})")
    
    # Test 2: Another direct A record
    print("\n[Test 2] Direct A record lookup (example.com)")
    total_tests += 1
    response = client.query('example.com')
    ip = extract_ip(response)
    if response and ip == '1.2.3.7':
        print(f"   ✓ PASS: Got correct IP {ip}")
        passed_tests += 1
    else:
        print(f"   ✗ FAIL: Expected 1.2.3.7, got {ip} (response: {response})")
    
    # Test 3: NS delegation to child server
    print("\n[Test 3] NS delegation lookup (www.google.co.il)")
    total_tests += 1
    response = client.query('www.google.co.il')
    ip = extract_ip(response)
    if response and ip == '1.2.3.8':
        print(f"   ✓ PASS: Got correct IP {ip} via NS delegation")
        passed_tests += 1
    else:
        print(f"   ✗ FAIL: Expected 1.2.3.8, got {ip} (response: {response})")
    
    # Test 4: Another NS delegation
    print("\n[Test 4] NS delegation lookup (mail.google.co.il)")
    total_tests += 1
    response = client.query('mail.google.co.il')
    ip = extract_ip(response)
    if response and ip == '1.2.3.9':
        print(f"   ✓ PASS: Got correct IP {ip} via NS delegation")
        passed_tests += 1
    else:
        print(f"   ✗ FAIL: Expected 1.2.3.9, got {ip} (response: {response})")
    
    # Test 5: Cache test - query same domain again (should be faster/from cache)
    print("\n[Test 5] Cache test - re-query biu.ac.il")
    total_tests += 1
    start_time = time.time()
    response = client.query('biu.ac.il')
    elapsed = time.time() - start_time
    ip = extract_ip(response)
    if response and ip == '1.2.3.4':
        print(f"   ✓ PASS: Got correct cached IP {ip} (took {elapsed:.4f}s)")
        passed_tests += 1
    else:
        print(f"   ✗ FAIL: Expected 1.2.3.4, got {ip} (response: {response})")
    
    # Test 6: Cache test for NS delegation
    print("\n[Test 6] Cache test - re-query www.google.co.il")
    total_tests += 1
    start_time = time.time()
    response = client.query('www.google.co.il')
    elapsed = time.time() - start_time
    ip = extract_ip(response)
    if response and ip == '1.2.3.8':
        print(f"   ✓ PASS: Got correct cached IP {ip} (took {elapsed:.4f}s)")
        passed_tests += 1
    else:
        print(f"   ✗ FAIL: Expected 1.2.3.8, got {ip} (response: {response})")
    
    # Test 7: Non-existent domain
    print("\n[Test 7] Non-existent domain (notfound.com)")
    total_tests += 1
    response = client.query('notfound.com')
    if response and response == "non-existent domain":
        print(f"   ✓ PASS: Got 'non-existent domain'")
        passed_tests += 1
    else:
        print(f"   ✗ FAIL: Expected 'non-existent domain', got '{response}'")
    
        # Test 8: Non-existent subdomain under delegated zone
    print("\n[Test 8] Non-existent subdomain (xyz.co.il)")
    total_tests += 1
    response = client.query('xyz.co.il')
    if response and response == "non-existent domain":
        print(f"   ✓ PASS: Got 'non-existent domain'")
        passed_tests += 1
    else:
        print(f"   ✗ FAIL: Expected 'non-existent domain', got '{response}'")
    
    # Test 9: Double NS delegation - Parent -> Child -> Grandchild
    print("\n[Test 9] Double NS delegation lookup (server.internal.co.il)")
    total_tests += 1
    response = client.query('server.internal.co.il')
    ip = extract_ip(response)
    if response and ip == '1.2.3.12':
        print(f"   ✓ PASS: Got correct IP {ip} via double NS delegation")
        passed_tests += 1
    else:
        print(f"   ✗ FAIL: Expected 1.2.3.12, got {ip} (response: {response})")
    
    # Test 10: Another double NS delegation
    print("\n[Test 10] Double NS delegation lookup (api.internal.co.il)")
    total_tests += 1
    response = client.query('api.internal.co.il')
    ip = extract_ip(response)
    if response and ip == '1.2.3.13':
        print(f"   ✓ PASS: Got correct IP {ip} via double NS delegation")
        passed_tests += 1
    else:
        print(f"   ✗ FAIL: Expected 1.2.3.13, got {ip} (response: {response})")
    
    # Test 11: Cache test for double NS delegation
    print("\n[Test 11] Cache test - re-query server.internal.co.il")
    total_tests += 1
    start_time = time.time()
    response = client.query('server.internal.co.il')
    elapsed = time.time() - start_time
    ip = extract_ip(response)
    if response and ip == '1.2.3.12':
        print(f"   ✓ PASS: Got correct cached IP {ip} (took {elapsed:.4f}s)")
        passed_tests += 1
    else:
        print(f"   ✗ FAIL: Expected 1.2.3.12, got {ip} (response: {response})")
    
    # Test 12: Third record from grandchild server
    print("\n[Test 12] Double NS delegation lookup (db.internal.co.il)")
    total_tests += 1
    response = client.query('db.internal.co.il')
    ip = extract_ip(response)
    if response and ip == '1.2.3.14':
        print(f"   ✓ PASS: Got correct IP {ip} via double NS delegation")
        passed_tests += 1
    else:
        print(f"   ✗ FAIL: Expected 1.2.3.14, got {ip} (response: {response})")
    
    # Cleanup
    print("\n" + "=" * 60)
    
    # Cleanup
    print("\n" + "=" * 60)
    print("Cleaning up...")
    print("=" * 60)
    client.close()
    parent_server.terminate()
    child_server.terminate()
    grandchild_server.terminate()
    resolver.terminate()
    
    time.sleep(0.5)
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print("=" * 60)
    
    if passed_tests == total_tests:
        print("\n✓ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n✗ {total_tests - passed_tests} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    try:
        exit_code = run_tests()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
