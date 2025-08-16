import asyncio
import logging
import os
import json
import aiohttp
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any
import subprocess
import tempfile

logger = logging.getLogger(__name__)

class IntelligentMonitoringAgent:
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.repo_owner = os.getenv('REPO_OWNER', 'yagakeerthikiran')
        self.repo_name = os.getenv('REPO_NAME', 'pdf-to-excel-saas')
        self.posthog_api_key = os.getenv('POSTHOG_PROJECT_API_KEY')
        self.posthog_host = os.getenv('POSTHOG_HOST', 'https://us.i.posthog.com')
        self.slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        
        # AWS clients
        self.cloudwatch = boto3.client('cloudwatch', region_name=self.aws_region)
        self.ecs = boto3.client('ecs', region_name=self.aws_region)
        
        # Monitoring configuration
        self.check_interval = int(os.getenv('MONITORING_INTERVAL', '60'))  # seconds
        self.error_threshold = int(os.getenv('ERROR_THRESHOLD', '10'))  # errors per minute
        self.auto_fix_enabled = os.getenv('AUTO_FIX_ENABLED', 'true').lower() == 'true'
        
        logger.info("Intelligent Monitoring Agent initialized")

    async def start_monitoring(self):
        """Start the monitoring loop"""
        logger.info("Starting intelligent monitoring...")
        
        while True:
            try:
                await self.run_health_checks()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(self.check_interval)

    async def run_health_checks(self):
        """Run all health checks and trigger fixes if needed"""
        issues = []
        
        # Frontend health check
        frontend_health = await self.check_frontend_health()
        if not frontend_health['healthy']:
            issues.append(frontend_health)
        
        # Backend health check
        backend_health = await self.check_backend_health()
        if not backend_health['healthy']:
            issues.append(backend_health)
        
        # Database health check
        db_health = await self.check_database_health()
        if not db_health['healthy']:
            issues.append(db_health)
        
        # Error rate monitoring
        error_rates = await self.check_error_rates()
        if error_rates['error_rate'] > self.error_threshold:
            issues.append({
                'type': 'high_error_rate',
                'severity': 'high',
                'message': f"Error rate {error_rates['error_rate']}/min exceeds threshold",
                'fix_strategy': 'restart_services'
            })
        
        # Process issues
        if issues:
            await self.handle_issues(issues)

    async def check_frontend_health(self) -> Dict[str, Any]:
        """Check frontend application health"""
        try:
            frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{frontend_url}/api/health", timeout=10) as response:
                    if response.status == 200:
                        return {'healthy': True, 'service': 'frontend'}
                    else:
                        return {
                            'healthy': False,
                            'service': 'frontend',
                            'type': 'service_down',
                            'severity': 'high',
                            'message': f"Frontend health check failed: HTTP {response.status}",
                            'fix_strategy': 'restart_frontend'
                        }
        except Exception as e:
            return {
                'healthy': False,
                'service': 'frontend',
                'type': 'service_unreachable',
                'severity': 'critical',
                'message': f"Frontend unreachable: {e}",
                'fix_strategy': 'restart_frontend'
            }

    async def check_backend_health(self) -> Dict[str, Any]:
        """Check backend API health"""
        try:
            backend_url = os.getenv('BACKEND_URL', 'http://localhost:8000')
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{backend_url}/health", timeout=10) as response:
                    if response.status == 200:
                        return {'healthy': True, 'service': 'backend'}
                    else:
                        return {
                            'healthy': False,
                            'service': 'backend',
                            'type': 'service_down',
                            'severity': 'high',
                            'message': f"Backend health check failed: HTTP {response.status}",
                            'fix_strategy': 'restart_backend'
                        }
        except Exception as e:
            return {
                'healthy': False,
                'service': 'backend',
                'type': 'service_unreachable',
                'severity': 'critical',
                'message': f"Backend unreachable: {e}",
                'fix_strategy': 'restart_backend'
            }

    async def check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity"""
        try:
            # This would connect to your actual database
            # For now, simulate a check
            return {'healthy': True, 'service': 'database'}
        except Exception as e:
            return {
                'healthy': False,
                'service': 'database',
                'type': 'database_error',
                'severity': 'critical',
                'message': f"Database connection failed: {e}",
                'fix_strategy': 'restart_database_connections'
            }

    async def check_error_rates(self) -> Dict[str, Any]:
        """Check error rates from CloudWatch and PostHog"""
        try:
            # Get CloudWatch metrics
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=5)
            
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/ApplicationELB',
                MetricName='HTTPCode_Target_5XX_Count',
                Dimensions=[
                    {
                        'Name': 'LoadBalancer',
                        'Value': 'app/pdf-excel-alb/1234567890'  # Your ALB name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Sum']
            )
            
            error_count = sum(point['Sum'] for point in response['Datapoints'])
            error_rate = error_count / 5  # errors per minute
            
            return {'error_rate': error_rate, 'period': '5min'}
            
        except Exception as e:
            logger.error(f"Error checking error rates: {e}")
            return {'error_rate': 0, 'period': '5min'}

    async def handle_issues(self, issues: List[Dict[str, Any]]):
        """Handle detected issues with auto-fixing"""
        logger.warning(f"Detected {len(issues)} issues")
        
        for issue in issues:
            logger.error(f"Issue: {issue['message']}")
            
            # Send notification
            await self.send_notification(issue)
            
            # Auto-fix if enabled and safe
            if self.auto_fix_enabled and self.is_auto_fixable(issue):
                await self.apply_auto_fix(issue)

    def is_auto_fixable(self, issue: Dict[str, Any]) -> bool:
        """Determine if an issue can be auto-fixed safely"""
        safe_fixes = [
            'restart_frontend',
            'restart_backend', 
            'restart_services',
            'clear_cache',
            'scale_workers'
        ]
        return issue.get('fix_strategy') in safe_fixes

    async def apply_auto_fix(self, issue: Dict[str, Any]):
        """Apply automatic fix for the issue"""
        fix_strategy = issue.get('fix_strategy')
        
        logger.info(f"Applying auto-fix: {fix_strategy}")
        
        try:
            if fix_strategy == 'restart_frontend':
                await self.restart_ecs_service('pdf-excel-frontend-service')
            elif fix_strategy == 'restart_backend':
                await self.restart_ecs_service('pdf-excel-backend-service')
            elif fix_strategy == 'restart_services':
                await self.restart_ecs_service('pdf-excel-frontend-service')
                await self.restart_ecs_service('pdf-excel-backend-service')
            elif fix_strategy == 'scale_workers':
                await self.scale_workers()
            elif fix_strategy == 'deploy_hotfix':
                await self.deploy_hotfix(issue)
            
            # Log successful fix
            await self.send_notification({
                'type': 'auto_fix_success',
                'severity': 'info',
                'message': f"Successfully applied fix: {fix_strategy}",
                'original_issue': issue['message']
            })
            
        except Exception as e:
            logger.error(f"Auto-fix failed: {e}")
            await self.send_notification({
                'type': 'auto_fix_failed',
                'severity': 'high',
                'message': f"Auto-fix failed for {fix_strategy}: {e}",
                'requires_manual_intervention': True
            })

    async def restart_ecs_service(self, service_name: str):
        """Restart an ECS service"""
        cluster_name = 'pdf-excel-cluster'
        
        self.ecs.update_service(
            cluster=cluster_name,
            service=service_name,
            forceNewDeployment=True
        )
        
        logger.info(f"Triggered restart for ECS service: {service_name}")

    async def scale_workers(self):
        """Scale up worker instances during high load"""
        cluster_name = 'pdf-excel-cluster'
        service_name = 'pdf-excel-worker-service'
        
        # Get current capacity
        response = self.ecs.describe_services(
            cluster=cluster_name,
            services=[service_name]
        )
        
        current_count = response['services'][0]['desiredCount']
        new_count = min(current_count * 2, 10)  # Cap at 10 instances
        
        self.ecs.update_service(
            cluster=cluster_name,
            service=service_name,
            desiredCount=new_count
        )
        
        logger.info(f"Scaled workers from {current_count} to {new_count}")

    async def deploy_hotfix(self, issue: Dict[str, Any]):
        """Deploy a hotfix for critical issues"""
        if not self.github_token:
            logger.error("Cannot deploy hotfix: GitHub token not configured")
            return
        
        # Create hotfix branch and commit
        hotfix_content = self.generate_hotfix_code(issue)
        
        if hotfix_content:
            # Create a PR with the hotfix
            await self.create_hotfix_pr(issue, hotfix_content)

    def generate_hotfix_code(self, issue: Dict[str, Any]) -> str:
        """Generate hotfix code based on the issue"""
        # AI-powered code generation would go here
        # For now, return basic fixes
        
        if 'memory_leak' in issue.get('message', '').lower():
            return """
            # Memory leak hotfix
            import gc
            
            def cleanup_memory():
                gc.collect()
                
            # Add to main application loop
            """
        
        elif 'rate_limit' in issue.get('message', '').lower():
            return """
            # Rate limiting hotfix
            from time import sleep
            import random
            
            def exponential_backoff(attempt):
                delay = (2 ** attempt) + random.uniform(0, 1)
                sleep(min(delay, 300))  # Max 5 minutes
            """
        
        return None

    async def create_hotfix_pr(self, issue: Dict[str, Any], fix_content: str):
        """Create a GitHub PR with the hotfix"""
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Create branch
        branch_name = f"hotfix/auto-fix-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        async with aiohttp.ClientSession() as session:
            # Get main branch SHA
            async with session.get(
                f'https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/git/refs/heads/main',
                headers=headers
            ) as response:
                main_ref = await response.json()
                main_sha = main_ref['object']['sha']
            
            # Create new branch
            await session.post(
                f'https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/git/refs',
                headers=headers,
                json={
                    'ref': f'refs/heads/{branch_name}',
                    'sha': main_sha
                }
            )
            
            # Create file with fix
            await session.put(
                f'https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/contents/hotfix.py',
                headers=headers,
                json={
                    'message': f"Auto-generated hotfix for: {issue['message']}",
                    'content': fix_content.encode('base64').decode('ascii'),
                    'branch': branch_name
                }
            )
            
            # Create PR
            await session.post(
                f'https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/pulls',
                headers=headers,
                json={
                    'title': f"🤖 Auto-generated hotfix: {issue['type']}",
                    'head': branch_name,
                    'base': 'main',
                    'body': f"""
                    ## Auto-Generated Hotfix
                    
                    **Issue**: {issue['message']}
                    **Severity**: {issue['severity']}
                    **Fix Strategy**: {issue.get('fix_strategy', 'unknown')}
                    
                    This hotfix was automatically generated by the monitoring agent.
                    Please review carefully before merging.
                    
                    Generated at: {datetime.now().isoformat()}
                    """
                }
            )

    async def send_notification(self, issue: Dict[str, Any]):
        """Send notification to Slack"""
        if not self.slack_webhook:
            return
        
        color = {
            'info': '#36a64f',
            'low': '#ffeb3b',
            'medium': '#ff9800',
            'high': '#f44336',
            'critical': '#9c27b0'
        }.get(issue.get('severity', 'medium'), '#ff9800')
        
        message = {
            'attachments': [{
                'color': color,
                'title': f"🚨 PDF to Excel SaaS Alert",
                'text': issue['message'],
                'fields': [
                    {
                        'title': 'Severity',
                        'value': issue.get('severity', 'unknown'),
                        'short': True
                    },
                    {
                        'title': 'Service',
                        'value': issue.get('service', 'unknown'),
                        'short': True
                    },
                    {
                        'title': 'Timestamp',
                        'value': datetime.now().isoformat(),
                        'short': True
                    }
                ]
            }]
        }
        
        async with aiohttp.ClientSession() as session:
            await session.post(self.slack_webhook, json=message)

async def main():
    """Main entry point for the monitoring agent"""
    agent = IntelligentMonitoringAgent()
    await agent.start_monitoring()

if __name__ == "__main__":
    asyncio.run(main())