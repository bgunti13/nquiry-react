# Ticket Creation Simulation System

## Overview

The ticket creation simulation system has been successfully implemented and tested. This system automatically categorizes user queries and creates appropriate support tickets based on predefined field mappings and customer information.

## Categories Supported

### 1. NOC (Network Operations Center)
**Trigger Keywords:** monitoring workflow, access, outage, reservation, decommission, custom task, reset RO user DB password

**Required Fields:**
- Description

**Auto-Populated Fields:**
- Project: MNLS, MNHT
- Work Type: Task/Outage/Access
- Summary: Generated based on description
- Priority: Medium
- Customer: Based on user domain
- Cloud Operations Request Type: production
- Cloud Operations Request Date: Alert from NOC to COPS

### 2. COPS (Cloud Operations)
**Trigger Keywords:** deployment, provisioning, troubleshooting, db refresh, db change request, datafix, file/report request, db parameter changes, custom task

**Required Fields:**
- Description

**Auto-Populated Fields:**
- Project: COPS
- Work Type: Task
- Summary: Based on description  
- Priority: Medium
- Customer: Based on user domain
- Support Projects: MNHT or MNLS based on customer
- Cloud Environmental List: production
- Cloud Operations Request Type: Change Request – DB
- Cloud Operations Request Date: Optional

### 3. MNHT (Model N Hi-Tech)
**Customer Mapping:** AMD customers
**For queries not matching NOC/COPS/CSP keywords**

**Required Fields:**
- Description
- Area
- Affected Version
- Reported Environment 

**Auto-Populated Fields:**
- Project: Model N Hi-Tech (MNHT)
- Work Type: Service Request
- Request Type: Product Support
- Summary: Based on description
- Urgency: Medium
- Impact: Moderate/Limited
- JSD Suppress Group Email Notification: No
- Support Org: Product Support

### 4. MNLS (Model N Life Sciences)
**Customer Mapping:** Novartis customers
**For queries not matching NOC/COPS/CSP keywords**

**Required Fields:**
- Description
- Area
- Affected Version  
- Reported Environment (Optional)

**Auto-Populated Fields:**
- Project: Model N Life Sciences (MNLS)
- Work Type: Service Request
- Request Type: Product Support
- Summary: Based on description
- Urgency: Medium
- Impact: Moderate/Limited
- JSD Suppress Group Email Notification: No
- Support Org: Product Support

## Files Created

### Core Implementation
1. **`ticket_creator.py`** - Main ticket creation simulation class with category detection and field mapping
2. **`ticket_mapping_config.json`** - Configuration file defining categories, keywords, and field mappings

### Testing and Demo Scripts
3. **`test_ticket_simulation.py`** - Unit tests for category detection and field mapping
4. **`demo_ticket_creation.py`** - Basic demo script creating sample tickets
5. **`improved_demo.py`** - Enhanced demo with targeted keyword testing
6. **`interactive_demo.py`** - Interactive demo showing the complete workflow

### Generated Output
7. **`ticket_simulation_output/`** - Directory containing generated demo ticket files

## Demo Ticket Examples

The system has been tested and generates properly formatted tickets like:

```
SUPPORT TICKET - MNHT
============================================================

TICKET INFORMATION
------------------
Ticket ID: MNHT-DEMO-20250923105424
Category: MNHT
Created Date: 2025-09-23T10:54:24.236841
Customer: AMD
Customer Email: support@amd.com

ORIGINAL QUERY
--------------
Pricing calculation errors in Model N Hi-Tech application

TICKET DETAILS
--------------
Description: Users reporting incorrect pricing calculations in the pricing module
Area: Pricing Module
Affected Version: 2.3.1
Reported Environment: Production
Project: Model N Hi-Tech (MNHT)
Work Type: Service Request
Request Type: Product Support
Summary: MNHT Support: Users reporting incorrect pricing calculations...
Urgency: Medium
Impact: Moderate/Limited
JSD Suppress Group Email Notification: No
Support Org: Product Support
```

## How to Use

### 1. Standalone Ticket Creation
```python
from ticket_creator import TicketCreator

creator = TicketCreator()
filepath = creator.create_ticket("Database performance issue", "user@amd.com")
```

### 2. Category Detection Only
```python
category = creator.determine_ticket_category("Deploy new version", "admin@company.com")
```

### 3. Run Interactive Demo
```bash
python interactive_demo.py
```

### 4. Run Tests
```bash
python test_ticket_simulation.py
```

## Integration with Main System

The ticket creator is already integrated into the main nQuiry system (`main.py`) and will be called automatically when:

1. No relevant information is found in JIRA search
2. No relevant information is found in MindTouch search  
3. The agent determines that ticket creation is needed

The system will:
1. Analyze the user's query and email to determine the appropriate category
2. Collect required field information from the user
3. Auto-populate standard fields based on the category
4. Generate a formatted ticket document for demo purposes
5. In a real environment, this would create an actual ticket in the appropriate system

## Testing Results

✅ **NOC Category Detection**: Working correctly with outage, monitoring, access keywords  
✅ **COPS Category Detection**: Working correctly with deployment, provisioning keywords  
✅ **MNHT Category Detection**: Working correctly for AMD customers with general issues  
✅ **MNLS Category Detection**: Working correctly for Novartis customers with general issues  
✅ **Field Mapping**: All required and auto-populated fields working correctly  
✅ **Document Generation**: Properly formatted demo tickets being created  

The ticket simulation system is now ready for demonstration and can be easily extended to integrate with actual ticketing systems when the environment becomes available.