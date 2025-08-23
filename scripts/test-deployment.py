#!/usr/bin/env python3
"""
Deployment Test Script for PDF to Excel SaaS
Tests all endpoints and deployment health after fixes.
"""
import requests
import boto3
import json
import time
import sys
from datetime import datetime

# Configuration
FRONTEND_URL = "http://pdf-excel-saas-prod-alb-1547358143.ap-southeast-2.elb.amazonaws.com"
BACKEND_API_URL = f"{FRONTEND_URL}/api"
REGION = "ap-southeast-2"

def test_frontend():
    """Test frontend deployment"""
    print("🌐 Testing Frontend...")
    try:
        response = requests.get(FRONTEND_URL, timeout=10)
        if response.status_code == 200:
            print(f"  ✅ Frontend accessible: {response.status_code}")
            return True
        else:
            print(f"  ❌ Frontend error: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Frontend connection failed: {e}")
        return False

def test_backend_health():
    """Test backend health endpoint"""
    print("🔧 Testing Backend Health...")
    try:
        response = requests.get(f"{BACKEND_API_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Backend health check: {data}")
            return True
        else:
            print(f"  ❌ Backend health error: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Backend health connection failed: {e}")
        return False

def test_backend_root():
    """Test backend root endpoint"""
    print("📋 Testing Backend Root...")
    try:
        response = requests.get(f"{BACKEND_API_URL}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Backend root: {data}")
            return True
        else:
            print(f"  ❌ Backend root error: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Backend root connection failed: {e}")
        return False

def check_ecs_services():
    """Check ECS service status"""
    print("🐳 Checking ECS Services...")
    try:
        ecs_client = boto3.client('ecs', region_name=REGION)
        
        # Check cluster
        clusters = ecs_client.describe_clusters(clusters=['pdf-excel-saas-prod'])
        cluster = clusters['clusters'][0]
        print(f"  📊 Cluster Status: {cluster['status']}")
        print(f"  📊 Running Tasks: {cluster['runningTasksCount']}")
        
        # Check services
        services = ecs_client.list_services(cluster='pdf-excel-saas-prod')
        
        for service_arn in services['serviceArns']:
            service_name = service_arn.split('/')[-1]
            service_details = ecs_client.describe_services(
                cluster='pdf-excel-saas-prod',
                services=[service_arn]
            )
            service = service_details['services'][0]
            print(f"  🔧 {service_name}:")
            print(f"    Status: {service['status']}")
            print(f"    Desired: {service['desiredCount']}, Running: {service['runningCount']}")
            
        return cluster['runningTasksCount'] > 0
        
    except Exception as e:
        print(f"  ❌ ECS check failed: {e}")
        return False

def check_target_groups():
    """Check target group health"""
    print("🎯 Checking Target Group Health...")
    try:
        elbv2_client = boto3.client('elbv2', region_name=REGION)
        
        target_groups = [
            'arn:aws:elasticloadbalancing:ap-southeast-2:654499586766:targetgroup/pdf-excel-saas-prod-frontend-tg1/2d73c25e5780dcbe',
            'arn:aws:elasticloadbalancing:ap-southeast-2:654499586766:targetgroup/pdf-excel-saas-prod-backend-tg1/624d10cc4f445c11'
        ]
        
        all_healthy = True
        
        for tg_arn in target_groups:
            tg_name = tg_arn.split('/')[-2]
            health = elbv2_client.describe_target_health(TargetGroupArn=tg_arn)
            
            print(f"  🎯 {tg_name}:")
            for target in health['TargetHealthDescriptions']:
                status = target['TargetHealth']['State']
                reason = target['TargetHealth'].get('Reason', '')
                print(f"    Target {target['Target']['Id']}: {status} {reason}")
                
                if status not in ['healthy', 'initial']:
                    all_healthy = False
                    
        return all_healthy
        
    except Exception as e:
        print(f"  ❌ Target group check failed: {e}")
        return False

def run_comprehensive_test():
    """Run all tests and provide summary"""
    print("🚀 PDF to Excel SaaS - Deployment Test")
    print("=" * 50)
    print(f"🕐 Test started at: {datetime.now()}")
    print("")
    
    tests = [
        ("ECS Services", check_ecs_services),
        ("Target Groups", check_target_groups),
        ("Frontend", test_frontend),
        ("Backend Health", test_backend_health),
        ("Backend API", test_backend_root),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        result = test_func()
        results.append((test_name, result))
        time.sleep(2)  # Brief pause between tests
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Deployment is successful!")
        print(f"\n🌐 Frontend URL: {FRONTEND_URL}")
        print(f"🔧 Backend API: {BACKEND_API_URL}")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed. Check logs above for details.")
        
        if not any(result for name, result in results if name in ["Frontend", "Backend Health"]):
            print("\n💡 Next steps:")
            print("1. Check if containers are still starting up")
            print("2. Wait 2-3 minutes for health checks to pass")
            print("3. Re-run this test script")
        return False

def main():
    """Main execution"""
    if len(sys.argv) > 1 and sys.argv[1] == "--wait":
        print("⏳ Waiting 60 seconds for services to start...")
        time.sleep(60)
    
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
