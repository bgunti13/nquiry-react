# nQuiry Ticket Creation Integration Guide

## 🎫 Overview

The nQuiry system now includes an integrated ticket creation simulation that automatically detects when users want to create support tickets and generates realistic ticket documents based on query categorization.

## 🚀 How It Works

### 1. **Automatic Detection**
The system detects ticket creation requests in two ways:
- **Direct requests**: User says "create ticket", "make ticket", etc.
- **Response to prompts**: User responds "yes", "sure", "okay" after seeing "Would you like me to create a support ticket?"

### 2. **Smart Categorization**
Tickets are automatically categorized based on:
- **Keywords in query**: database, access, deployment, etc.
- **Customer domain**: amd.com → MNHT, novartis.com → MNLS
- **Issue type mapping**: 5 categories (NOC, COPS, CSP, MNHT, MNLS)

### 3. **Realistic Ticket Generation**
Each ticket includes:
- Auto-generated ticket ID
- Category-specific required fields
- Customer-specific populated fields
- Professional formatting
- Saved text file for demo purposes

## 📋 Ticket Categories

### NOC (Network Operations Center)
**Keywords**: monitoring, access, outage, reservation, decommission
**Fields**: Project, Work Type (Task/Outage/Access), Priority, Customer

### COPS (Cloud Operations)
**Keywords**: deployment, provisioning, troubleshooting, database, db refresh
**Fields**: Project, Work Type, Priority, Customer, Support Projects, Environmental List

### CSP (Customer Success Platform)
**Keywords**: grant access, revoke access, permissions
**Fields**: Project, Work Type, Priority, Customer

### MNHT (Model N Hi-Tech)
**Customer**: AMD (amd.com domain)
**Fields**: Project, Work Type, Request Type, Urgency, Impact, Support Org

### MNLS (Model N Life Sciences)
**Customer**: Novartis (novartis.com domain)
**Fields**: Project, Work Type, Request Type, Urgency, Impact, Support Org

## 💻 Integration Points

### 1. **Main Application Flow** (`main.py`)
```python
# Modified process_query method now checks for ticket creation requests
def process_query(self, user_id: str, query: str, history=None):
    # Detects "yes" responses to ticket prompts
    if self.is_ticket_creation_request(query, previous_response):
        return self.process_ticket_creation_request(user_id, query, original_query)
    # ... normal processing
```

### 2. **Streamlit App** (`streamlit_app.py`)
The app automatically handles ticket creation through the existing query processing flow:
- User asks a question
- System provides response with ticket creation prompt if needed
- User responds "yes"
- System creates simulated ticket and displays results

### 3. **Response Formatter** (`response_formatter.py`)
```python
# New method for ticket simulation
def create_simulated_ticket(self, query: str, user_email: str = "", additional_description: str = ""):
    # Automatically categorizes and generates ticket
```

## 🧪 Testing

### Run Tests
```bash
cd "c:\Users\bgunti\Desktop\nquiry"
python test_integrated_ticket_creation.py
```

### Manual Testing
1. Start streamlit app: `streamlit run streamlit_app.py`
2. Enter customer email (e.g., admin@amd.com)
3. Ask a question like "Database not syncing properly"
4. When prompted "Would you like me to create a support ticket?", respond "yes"
5. System automatically creates and displays ticket

## 📁 Generated Files

Tickets are saved to `ticket_simulation_output/` with format:
```
ticket_demo_{CATEGORY}_{CUSTOMER}_{TIMESTAMP}.txt
```

Example: `ticket_demo_COPS_AMD_20250922_132042.txt`

## 🔧 Configuration

### Ticket Mapping (`ticket_mapping_config.json`)
- Category keywords and mappings
- Required and populated fields per category
- Customer domain mappings

### Customization Points
1. **Add new categories**: Update `ticket_mapping_config.json`
2. **Modify keywords**: Edit category keywords in config
3. **Change field mappings**: Update required/populated fields
4. **Add customer domains**: Extend customer_mappings section

## 🎯 Example Workflows

### Database Issue (COPS Category)
1. User: "Database refresh is failing"
2. System: Searches knowledge base, finds insufficient info
3. System: "❓ Would you like me to create a support ticket?"
4. User: "yes"
5. System: Creates COPS ticket with database-specific fields

### Access Request (NOC Category)
1. User: "Need access to monitoring dashboard"
2. System: "❓ Would you like me to create a support ticket?"
3. User: "sure"
4. System: Creates NOC ticket with access request type

### Product Support (MNHT/MNLS)
1. User: "How to configure Model N for AMD users"
2. System: Identifies AMD customer, creates MNHT ticket
3. System: Includes product support specific fields

## 🚨 Important Notes

- **Simulation Only**: This creates demo tickets for testing purposes
- **Production Ready**: Logic is ready for real ticket system integration
- **Context Aware**: Uses conversation history to identify original queries
- **Customer Specific**: Automatically maps customer domains to correct categories
- **Extensible**: Easy to add new categories and mappings

## 🔄 Next Steps for Production

1. **Replace simulation with real API calls** to your ticketing system
2. **Add authentication** for ticket creation
3. **Implement ticket tracking** and status updates
4. **Add email notifications** for ticket creation
5. **Integrate with existing workflows** and approval processes