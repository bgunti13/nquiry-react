import random
import sys
import os
from typing import Optional
from datetime import datetime

# Add the parent directory to the path to import from the main project
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

try:
    from main import IntelligentQueryProcessor
    ORIGINAL_PROCESSOR_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import original processor: {e}")
    ORIGINAL_PROCESSOR_AVAILABLE = False

class ChatService:
    """Service for handling chat interactions"""
    
    def __init__(self):
        self.initialized = False
        self.organization_data = None
        
        # Try to initialize the original intelligent processor
        if ORIGINAL_PROCESSOR_AVAILABLE:
            try:
                self.intelligent_processor = IntelligentQueryProcessor()
                self.use_intelligent_processor = True
                print("✅ Using original intelligent query processor")
            except Exception as e:
                print(f"❌ Failed to initialize intelligent processor: {e}")
                self.use_intelligent_processor = False
        else:
            self.use_intelligent_processor = False
            
        if not self.use_intelligent_processor:
            print("⚠️ Falling back to simple keyword-based responses")
        
        # Fallback responses for when intelligent processor is not available
        self.responses = {
            "version": [
                "Our latest software version is **v2.8.3**, released on October 1st, 2025. This version includes enhanced security features, improved performance, and bug fixes. Would you like to know about the update process?",
                "The current version is **v2.8.3**. Key features include:\n- Enhanced SSL/TLS support\n- 40% faster query processing\n- New dashboard interface\n- Improved API documentation\n\nWould you like upgrade instructions?"
            ],
            "ssl": [
                "To configure SSL certificates:\n\n**1. Generate Certificate:**\n```\nopenssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365\n```\n\n**2. Update Configuration:**\n- Place certificates in `/etc/ssl/certs/`\n- Update config file with certificate paths\n- Restart the service\n\n**3. Verify Setup:**\n```\nopenssl s_client -connect yourdomain.com:443\n```\n\nWould you like more detailed steps for your specific environment?"
            ],
            "requirements": [
                "**System Requirements:**\n\n**Minimum:**\n- OS: Windows 10+ / Ubuntu 18.04+ / macOS 10.15+\n- RAM: 8GB\n- Storage: 50GB free space\n- CPU: 4 cores @ 2.4GHz\n\n**Recommended:**\n- RAM: 16GB+\n- Storage: 100GB SSD\n- CPU: 8 cores @ 3.0GHz+\n- Network: 1Gbps connection\n\n**Dependencies:**\n- Python 3.8+\n- Node.js 16+\n- MongoDB 5.0+\n\nNeed help with installation?"
            ],
            "troubleshoot": [
                "**Common Connection Issues & Solutions:**\n\n**1. Connection Timeout:**\n- Check firewall settings (ports 80, 443, 8080)\n- Verify DNS configuration\n- Test with: `telnet server_ip port`\n\n**2. Authentication Failed:**\n- Verify credentials\n- Check token expiration\n- Review user permissions\n\n**3. SSL/TLS Errors:**\n- Update certificates\n- Check cipher compatibility\n- Verify certificate chain\n\n**4. Network Connectivity:**\n```\nping server_address\nnslookup domain.com\ntraceroute server_ip\n```\n\nWhich specific error are you encountering?"
            ],
            "support": [
                "**Premium Support Plan includes:**\n\n✅ **24/7 Technical Support**\n- Phone, email, and chat support\n- Average response time: < 2 hours\n\n✅ **Dedicated Account Manager**\n- Direct contact for escalations\n- Quarterly business reviews\n\n✅ **Priority Issue Resolution**\n- Critical: 1 hour response\n- High: 4 hours response\n- Medium: 24 hours response\n\n✅ **Additional Benefits:**\n- Custom integrations support\n- Training sessions for your team\n- Early access to new features\n- Monthly health checks\n\nWould you like to upgrade your support plan?"
            ],
            "upgrade": [
                "**License Upgrade Options:**\n\n**📈 Professional → Enterprise:**\n- Unlimited users (vs 50)\n- Advanced analytics\n- Custom branding\n- Priority support\n- Price: +$200/month\n\n**🔧 Standard → Professional:**\n- API access\n- Advanced integrations\n- Custom workflows\n- Email support\n- Price: +$100/month\n\n**⚡ Upgrade Process:**\n1. Contact your account manager\n2. Review new features demo\n3. Sign upgrade agreement\n4. Automatic feature activation\n\nWould you like to schedule a demo or create a support ticket for license upgrade?"
            ],
            "tiers": [
                "**Product Tier Comparison:**\n\n**🆓 Starter (Free):**\n- 5 users max\n- Basic features\n- Community support\n- 1GB storage\n\n**💼 Professional ($99/month):**\n- 50 users\n- Advanced features\n- Email support\n- 100GB storage\n- API access\n\n**🏢 Enterprise ($299/month):**\n- Unlimited users\n- All features\n- 24/7 phone support\n- 1TB storage\n- Custom integrations\n- Dedicated account manager\n\n**🎯 Which tier best fits your needs?** I can help you choose or create a support ticket for a consultation."
            ],
            "integration": [
                "**Third-Party Integration Options:**\n\n**📊 Analytics & BI:**\n- Tableau, Power BI, Grafana\n- Real-time data sync\n- Custom dashboards\n\n**🔧 Development Tools:**\n- GitHub, GitLab, Bitbucket\n- CI/CD pipelines\n- Automated deployments\n\n**💬 Communication:**\n- Slack, Microsoft Teams\n- Email notifications\n- Webhook integrations\n\n**🗃️ Databases:**\n- PostgreSQL, MySQL, MongoDB\n- Data warehouses (Snowflake, BigQuery)\n- ETL pipelines\n\n**Setup Guide:**\n1. Go to Settings → Integrations\n2. Select your platform\n3. Follow OAuth setup\n4. Configure sync settings\n\nWhich integration are you interested in?"
            ],
            "data_retention": [
                "**Data Retention Policy:**\n\n**📋 Standard Retention:**\n- Transaction data: 7 years\n- User activity logs: 2 years\n- System logs: 1 year\n- Temporary files: 30 days\n\n**🔒 Security & Compliance:**\n- GDPR compliant\n- SOC 2 Type II certified\n- HIPAA compliance available\n- Data encryption at rest\n\n**🌍 Data Locations:**\n- Primary: US East (N. Virginia)\n- Backup: EU West (Ireland)\n- Custom regions available\n\n**⚙️ Retention Settings:**\n- Configurable per data type\n- Automatic archival\n- Secure deletion\n- Audit trail maintained\n\nNeed help configuring retention policies for your organization?"
            ],
            "backup": [
                "**Automated Backup Setup:**\n\n**🔄 Backup Types:**\n- **Full backups:** Daily at 2 AM UTC\n- **Incremental:** Every 6 hours\n- **On-demand:** Manual triggers available\n\n**⚙️ Configuration Steps:**\n\n1. **Enable Auto-Backup:**\n```bash\nconfig set backup.enabled=true\nconfig set backup.schedule=\"0 2 * * *\"\n```\n\n2. **Set Backup Location:**\n```bash\nconfig set backup.destination=\"s3://your-bucket/backups\"\nconfig set backup.retention=30\n```\n\n3. **Verify Setup:**\n```bash\nbackup test\nbackup status\n```\n\n**☁️ Storage Options:**\n- AWS S3, Google Cloud Storage\n- Azure Blob Storage\n- Local network storage\n- Hybrid configurations\n\n**🔍 Monitoring:**\n- Email notifications on success/failure\n- Dashboard with backup history\n- Restore time estimates\n\nWould you like help setting up backups for your specific environment?"
            ],
            "default": [
                "I'm here to help! I can assist you with:\n\n🔧 **Technical Support:**\n- Software versions and updates\n- Configuration and setup\n- Troubleshooting issues\n- System requirements\n\n💼 **Account & Licensing:**\n- Support plan information\n- License upgrades\n- Product tier comparisons\n\n🔌 **Integrations:**\n- Third-party tool connections\n- API documentation\n- Custom implementations\n\n📋 **Policies & Compliance:**\n- Data retention policies\n- Security practices\n- Backup procedures\n\nWhat would you like to know more about? You can also ask me to **create a support ticket** if you need human assistance."
            ]
        }
    
    async def process_message(self, message: str, user_id: str, organization_data: Optional[dict] = None) -> str:
        """Process a user message and return a response"""
        
        if organization_data and not self.initialized:
            self.organization_data = organization_data
            self.initialized = True
        
        # Try to use the original intelligent processor first
        if self.use_intelligent_processor:
            try:
                # Map organization data to the format expected by the original processor
                org_name = organization_data.get('name', 'Unknown') if organization_data else 'Unknown'
                user_email = organization_data.get('email', user_id) if organization_data else user_id
                
                print(f"🤖 Processing query with intelligent processor: '{message}'")
                print(f"👤 Organization: {org_name}, User: {user_email}")
                
                # Use the original intelligent processor
                result = self.intelligent_processor.process_query(
                    query=message,
                    user_email=user_email,
                    context=f"Organization: {org_name}"
                )
                
                if result and result.get('formatted_response'):
                    response = result['formatted_response']
                    print(f"✅ Intelligent processor returned: {response[:100]}...")
                    return response
                else:
                    print("⚠️ Intelligent processor returned empty result, using fallback")
                    
            except Exception as e:
                print(f"❌ Error with intelligent processor: {e}")
                print("🔄 Falling back to keyword-based responses")
        
        # Fallback to keyword-based responses
        print(f"🔤 Using keyword-based fallback for: '{message}'")
        message_lower = message.lower().strip()
        
        # Check for ticket creation requests
        if any(phrase in message_lower for phrase in [
            "create ticket", "create a ticket", "support ticket", "human support",
            "escalate", "need help", "contact support"
        ]):
            org_name = self.organization_data.get('name', 'your organization') if self.organization_data else 'your organization'
            return f"""I understand you'd like to create a support ticket. I can help you with that!

**🎫 Creating a support ticket will:**
- Generate a unique ticket ID for tracking
- Route your issue to the appropriate team
- Provide you with regular status updates
- Ensure proper escalation if needed

**To proceed, I'll need some details:**
- Brief summary of the issue
- Detailed description
- Priority level
- Category (Technical, Billing, etc.)

Would you like me to open the ticket creation form, or would you prefer to provide the details here in our chat?

For {org_name}, I can also escalate directly to your dedicated support team if this is urgent."""

        # Check for specific query types
        if any(word in message_lower for word in ["version", "latest", "update", "release"]):
            return random.choice(self.responses["version"])
        
        elif any(word in message_lower for word in ["ssl", "certificate", "tls", "https"]):
            return random.choice(self.responses["ssl"])
        
        elif any(word in message_lower for word in ["requirement", "system", "minimum", "hardware"]):
            return random.choice(self.responses["requirements"])
        
        elif any(word in message_lower for word in ["troubleshoot", "connection", "error", "issue", "problem"]):
            return random.choice(self.responses["troubleshoot"])
        
        elif any(word in message_lower for word in ["support plan", "premium", "support"]):
            return random.choice(self.responses["support"])
        
        elif any(word in message_lower for word in ["upgrade", "license"]):
            return random.choice(self.responses["upgrade"])
        
        elif any(word in message_lower for word in ["tier", "difference", "plan", "pricing"]):
            return random.choice(self.responses["tiers"])
        
        elif any(word in message_lower for word in ["integration", "integrate", "third-party", "api"]):
            return random.choice(self.responses["integration"])
        
        elif any(word in message_lower for word in ["data retention", "retention", "data policy"]):
            return random.choice(self.responses["data_retention"])
        
        elif any(word in message_lower for word in ["backup", "backups", "automated backup"]):
            return random.choice(self.responses["backup"])
        
        else:
            # Default response with organization context
            org_context = ""
            if self.organization_data:
                org_name = self.organization_data.get('name', '')
                if org_name:
                    org_context = f"\n\nAs a {org_name} customer, you have access to our premium support features. "
            
            return random.choice(self.responses["default"]) + org_context