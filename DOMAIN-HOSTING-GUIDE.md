# 🌐 Domain and Hosting Setup Guide

## Overview
Your PDF to Excel SaaS will be hosted on AWS with a custom domain. This guide covers everything from domain registration to SSL setup.

## 🏗️ Infrastructure Architecture

```
Internet → CloudFront CDN → Application Load Balancer → ECS Services
                           ↓
                         Route 53 DNS
                           ↓
                      yourdomain.com
```

## Phase 1: Domain Registration (Choose One Option)

### Option A: Register New Domain (Recommended)

**Step 1: Choose a Domain Name**
Consider these options:
- `pdftoexcel.com` / `pdftoexcel.io`
- `convertpdf.com` / `convertpdf.io` 
- `pdftospreadsheet.com`
- `quickpdfconvert.com`
- `excellentpdf.com`

**Step 2: Register Domain**

**Via AWS Route 53 (Easiest Integration):**
1. Go to AWS Console → Route 53
2. Click "Registered domains" → "Register domain"
3. Search for your chosen domain
4. Complete registration ($12-15/year)
5. AWS automatically creates hosted zone

**Via External Registrar (Cheaper):**
1. Go to Namecheap, Google Domains, or GoDaddy
2. Register domain ($8-12/year)
3. Note: You'll need to configure DNS manually

### Option B: Use Subdomain (Free)
If you already own a domain, use a subdomain like:
- `pdf.yourdomain.com`
- `convert.yourdomain.com`
- `tools.yourdomain.com`

## Phase 2: AWS Infrastructure Setup

### Step 1: Deploy Infrastructure
```bash
# Pull latest code
git pull origin feat/initial-app-foundation

# Run the Python deployment script (no PowerShell issues)
python scripts/deploy_manual.py
```

### Step 2: Get ALB DNS Name
After deployment, check `infrastructure-outputs.json`:
```json
{
  "alb_dns_name": {
    "value": "pdf-excel-alb-123456.us-east-1.elb.amazonaws.com"
  }
}
```

## Phase 3: DNS Configuration

### Option A: If Using Route 53 (AWS Domain)

**Step 1: Create Records**
1. Go to Route 53 → Hosted zones → yourdomain.com
2. Create A record:
   - **Name**: Leave empty (for root domain)
   - **Type**: A - IPv4 address
   - **Alias**: Yes
   - **Alias target**: Select your ALB
3. Create CNAME record for www:
   - **Name**: www
   - **Type**: CNAME
   - **Value**: yourdomain.com

### Option B: If Using External Registrar

**Step 1: Create AWS Hosted Zone**
1. Go to Route 53 → Create hosted zone
2. Enter your domain name
3. Note the 4 name servers (ns-xxx.awsdns-xxx.com)

**Step 2: Update Domain Registrar**
1. Go to your domain registrar (Namecheap, etc.)
2. Find DNS/Nameserver settings
3. Replace default nameservers with AWS nameservers
4. Wait 24-48 hours for propagation

**Step 3: Create DNS Records** (Same as Option A)

### Option C: If Using Subdomain

**Step 1: Create CNAME Record**
In your existing DNS provider:
- **Name**: pdf (or your chosen subdomain)
- **Type**: CNAME
- **Value**: your-alb-dns-name.us-east-1.elb.amazonaws.com

## Phase 4: SSL Certificate Setup

### Step 1: Request Certificate in AWS Certificate Manager
1. Go to AWS Console → Certificate Manager
2. Click "Request certificate"
3. Choose "Request a public certificate"
4. Add domain names:
   - `yourdomain.com`
   - `www.yourdomain.com`
5. Choose DNS validation
6. Click "Request"

### Step 2: Validate Certificate
1. In Certificate Manager, click your certificate
2. Copy the CNAME record details
3. Add these CNAMEs to Route 53 (or your DNS provider)
4. Wait for validation (usually 5-10 minutes)

### Step 3: Attach Certificate to Load Balancer
1. Go to EC2 → Load Balancers
2. Select your ALB (`pdf-excel-saas-prod-alb`)
3. Click "Listeners" tab
4. Click "Add listener"
5. Configure HTTPS listener:
   - **Protocol**: HTTPS
   - **Port**: 443
   - **Default SSL certificate**: Select your certificate
   - **Default actions**: Forward to target group

### Step 4: Redirect HTTP to HTTPS
1. Edit the HTTP (port 80) listener
2. Change default action to "Redirect to HTTPS"
3. Set status code to 301 (permanent redirect)

## Phase 5: CloudFront CDN Setup (Optional but Recommended)

### Benefits of CloudFront:
- Faster global loading times
- Additional DDoS protection
- Reduced server load
- Better SEO rankings

### Step 1: Create CloudFront Distribution
1. Go to CloudFront → Create distribution
2. Configure origin:
   - **Origin domain**: your-alb-dns-name.us-east-1.elb.amazonaws.com
   - **Protocol**: HTTPS only
3. Configure default cache behavior:
   - **Viewer protocol policy**: Redirect HTTP to HTTPS
   - **Allowed HTTP methods**: GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE
4. Configure distribution settings:
   - **Alternate domain names**: yourdomain.com, www.yourdomain.com
   - **Custom SSL certificate**: Select your certificate
5. Create distribution (takes 15-20 minutes)

### Step 2: Update DNS to Point to CloudFront
1. Go back to Route 53
2. Update A record for yourdomain.com:
   - **Alias target**: CloudFront distribution
3. Update CNAME for www.yourdomain.com:
   - **Value**: CloudFront domain name

## Phase 6: Email Configuration for Notifications

### Option A: AWS SES (Recommended)

**Step 1: Verify Domain**
1. Go to SES → Verified identities
2. Create identity → Domain
3. Enter your domain
4. Add DNS records provided by SES

**Step 2: Request Production Access**
1. Go to SES → Account dashboard
2. Click "Request production access"
3. Fill out the form explaining your use case

### Option B: Gmail SMTP (Quick Setup)

**Step 1: Enable 2FA on Gmail**
1. Go to Google Account security
2. Enable 2-factor authentication

**Step 2: Generate App Password**
1. Go to Google Account → Security → App passwords
2. Generate password for "Mail"
3. Save this password

**Step 3: Update Environment Variables**
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=yagakeerthikiran@gmail.com
SMTP_PASS=your_gmail_app_password
NOTIFICATION_EMAIL=yagakeerthikiran@gmail.com
```

## Phase 7: Complete Integration Steps

### Step 1: Update Environment Variables
After infrastructure deployment, update your `.env.prod` with:

```bash
# Update these with your actual values
NEXT_PUBLIC_APP_URL=https://yourdomain.com
BACKEND_URL=https://yourdomain.com
DATABASE_URL=postgresql://dbadmin:password@your-rds-endpoint:5432/pdfexcel

# Add email settings
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=yagakeerthikiran@gmail.com
SMTP_PASS=your_gmail_app_password
NOTIFICATION_EMAIL=yagakeerthikiran@gmail.com
```

### Step 2: Set Up Service Accounts
Follow the detailed steps in `SERVICE-SETUP-GUIDE.md`:
1. **Stripe** (for payments)
2. **Supabase** (for authentication)
3. **Sentry** (for error tracking)
4. **PostHog** (for analytics)

### Step 3: Configure GitHub Secrets
```bash
# Pull latest changes to get the fixed scripts
git pull origin feat/initial-app-foundation

# Set up GitHub secrets (use the Python script method)
python scripts/setup_github_secrets.py
```

### Step 4: Deploy Application
```bash
# Commit your environment changes
git add .env.prod
git commit -m "Add production environment configuration"

# Push to trigger deployment
git push origin feat/initial-app-foundation:main
```

### Step 5: Monitor Deployment
1. Check GitHub Actions: https://github.com/yagakeerthikiran/pdf-to-excel-saas/actions
2. Monitor AWS ECS services
3. Check email notifications
4. Test your domain: https://yourdomain.com

## Phase 8: Post-Deployment Testing

### Step 1: Verify DNS Propagation
```bash
# Check if DNS is working
nslookup yourdomain.com
dig yourdomain.com

# Test from different locations
# Use: https://www.whatsmydns.net/
```

### Step 2: Test SSL Certificate
1. Visit https://yourdomain.com
2. Check for green lock icon
3. Use SSL checker: https://www.ssllabs.com/ssltest/

### Step 3: Test Application Flow
1. **Homepage**: https://yourdomain.com
2. **User registration**: Create test account
3. **File upload**: Upload a test PDF
4. **Conversion**: Verify PDF to Excel conversion
5. **Download**: Download converted file
6. **Payment**: Test subscription upgrade (use Stripe test mode)

### Step 4: Performance Testing
1. **Page Speed**: Use Google PageSpeed Insights
2. **Load Testing**: Use tools like Artillery.io
3. **Uptime Monitoring**: Set up UptimeRobot or similar

## Phase 9: Monitoring and Maintenance

### Ongoing Monitoring Setup

**AWS CloudWatch Alarms:**
1. ECS service health
2. Database connections
3. Error rates
4. Response times

**Email Alerts Configuration:**
```python
# Your monitoring script will send emails for:
# - Service failures
# - High error rates  
# - Performance issues
# - Security alerts
# - Backup failures
```

**Business Metrics Tracking:**
1. User registrations
2. File conversions
3. Subscription upgrades
4. Revenue metrics
5. Customer churn

### Security Checklist
- [ ] SSL certificate valid and auto-renewing
- [ ] All HTTP traffic redirected to HTTPS
- [ ] WAF enabled on CloudFront
- [ ] Database encryption enabled
- [ ] S3 bucket policies secured
- [ ] IAM roles follow least privilege
- [ ] Regular security scanning enabled

### Backup Strategy
- [ ] Database automated backups enabled
- [ ] S3 versioning and lifecycle policies
- [ ] Code repository backups
- [ ] Configuration backups
- [ ] Disaster recovery plan documented

## Phase 10: Business Launch Preparation

### Marketing Setup
1. **Analytics**: PostHog events tracking
2. **SEO**: Meta tags, sitemap, robots.txt
3. **Social Media**: Open Graph tags
4. **Landing Page**: Conversion optimization

### Legal Requirements
1. **Privacy Policy**: GDPR compliance
2. **Terms of Service**: Clear usage terms
3. **Cookie Policy**: Required for EU users
4. **Data Processing**: User data handling

### Customer Support
1. **Help Documentation**: User guides
2. **Support Email**: support@yourdomain.com
3. **Knowledge Base**: FAQ section
4. **Live Chat**: Consider Intercom or similar

## Cost Optimization Tips

### AWS Cost Management
1. **Right-sizing**: Monitor and adjust instance sizes
2. **Reserved Instances**: For predictable workloads
3. **Spot Instances**: For background workers
4. **S3 Intelligent Tiering**: For file storage
5. **CloudWatch Cost Monitoring**: Set billing alerts

### Expected Monthly Costs
- **AWS Infrastructure**: $150-250
- **Domain**: $1-2
- **External Services**: $0-50 (free tiers)
- **Total**: ~$150-300/month

### Revenue Optimization
- **Free Tier**: 5 conversions/day (lead generation)
- **Pro Tier**: $9.99/month (main revenue)
- **Enterprise**: Custom pricing for high-volume users
- **API Access**: Additional revenue stream

## Troubleshooting Common Issues

### DNS Not Resolving
- Check nameserver configuration
- Wait for DNS propagation (up to 48 hours)
- Use DNS checker tools

### SSL Certificate Issues
- Verify domain ownership
- Check certificate covers all domain variants
- Ensure certificate is attached to load balancer

### Application Not Loading
- Check ECS service status
- Verify target group health
- Review CloudWatch logs

### Email Notifications Not Working
- Verify SMTP credentials
- Check spam folders
- Test with different email providers

## Success Metrics

### Technical KPIs
- **Uptime**: >99.9%
- **Response time**: <2 seconds
- **Error rate**: <1%
- **Conversion success**: >98%

### Business KPIs
- **User acquisition**: Target 100 signups/month
- **Conversion rate**: 10% free to paid
- **Monthly recurring revenue**: Target $1000+
- **Customer satisfaction**: >4.5/5 rating

---

## 🎉 Congratulations!

Once you complete all these steps, you'll have a fully functional, production-ready PDF to Excel SaaS with:

✅ **Custom domain with SSL**
✅ **Global CDN distribution**
✅ **Automated monitoring**
✅ **Email notifications**
✅ **Scalable infrastructure**
✅ **Payment processing**
✅ **User authentication**
✅ **Error tracking**
✅ **Business analytics**

Your SaaS is ready to serve customers worldwide! 🚀

---

*For support with any of these steps, refer to the specific service documentation or create an issue in the GitHub repository.*