# Dynamic Customer Role Mapping System

## 🎯 Overview

The nQuiry system now uses **dynamic customer role mappings** that are loaded from an Excel file instead of hardcoded values. This allows easy management and updates of customer organizations and their MindTouch roles without touching code.

## 📊 Current System Status

- **✅ 120 customers loaded** from `LS-HT Customer Info.xlsx` (2 sheets)
- **✅ 87 unique domains mapped** (duplicates automatically handled)
- **✅ 3 role types supported**: 
  - **42 customers** → `GoS-PBN` (LS-N platform from LS sheet)
  - **19 customers** → `GoS-PBF` (LS-Flex platform from LS sheet)
  - **26 customers** → `GoS-HT` (All customers from HT sheet)
- **✅ Multi-sheet support**: Reads both LS and HT sheets automatically
- **✅ Auto-refresh**: System automatically reloads when Excel file changes
- **✅ Fallback handling**: Unknown customers get default `customer` role

## 📋 Excel File Format

The system reads from **`LS-HT Customer Info.xlsx`** with **2 sheets**:

### Sheet 1: 'LS' (Life Sciences)
| Customer | Platform | Prod. Version |
|----------|----------|---------------|
| Abbott ADC | LS-N | Spring 24 |
| Pfizer Inc. | LS-Flex | Fall 24 |

### Sheet 2: 'HT' (High Tech) 
| Customer | US Primary | Prod. Version |
|----------|------------|---------------|
| AMD (Xilinx) | Ruchika Vats | Fall 22 |
| Microchip | Lei Ke | Fall 24 |

### Role Mapping Rules:
- **LS Sheet**: Uses Platform column
  - **`LS-N`** → **`GoS-PBN`** (Life Sciences - PBN)
  - **`LS-Flex`** → **`GoS-PBF`** (Life Sciences - PBF)
- **HT Sheet**: All customers automatically get
  - **`HT`** → **`GoS-HT`** (High Tech)

## 🔄 How It Works

1. **Domain Generation**: Customer name → Email domain
   - "Abbott ADC" → `abbott.com`
   - "Pfizer Inc." → `pfizer.com`
   - "Johnson & Johnson" → `johnson.com`

2. **Role Assignment**: Platform code → MindTouch role
   - LS-N → `=GoS-PBN`
   - LS-Flex → `=GoS-PBF`

3. **Auto-Refresh**: System checks file modification time and reloads automatically

## ➕ Adding New Customers

### Method 1: Life Sciences Customers
1. Open `LS-HT Customer Info.xlsx`
2. Go to **'LS' sheet**
3. Add new row with:
   - **Customer**: Company name (e.g., "Roche Inc")
   - **Platform**: Role code (`LS-N` or `LS-Flex`)
   - **Prod. Version**: Any value (optional)
4. Save the file
5. System automatically refreshes on next query

### Method 2: High Tech Customers
1. Open `LS-HT Customer Info.xlsx`
2. Go to **'HT' sheet** 
3. Add new row with:
   - **Customer**: Company name (e.g., "Intel Corp")
   - **US Primary**: Contact person (optional)
   - **Prod. Version**: Any value (optional)
4. Save the file
5. System automatically assigns `GoS-HT` role

## 🔧 Management Commands

### Check System Status
```bash
py -c "from customer_role_manager import customer_role_manager; print(customer_role_manager.get_mapping_stats())"
```

### Test Specific Customer
```bash
py -c "from tools.mindtouch_tool import MindTouchTool; tool = MindTouchTool(customer_email='test@pfizer.com'); print(tool.get_customer_info())"
```

### View All Mappings
```bash
py customer_role_manager.py
```

## 📈 System Benefits

### ✅ For Manager:
- **Easy updates**: Just edit Excel file
- **No code changes**: Add customers without developer
- **Visual management**: See all customers in Excel
- **Version control**: Track changes in Excel

### ✅ For Developers:
- **Automatic refresh**: No system restart needed
- **Fallback handling**: Graceful handling of unknown customers
- **Extensible**: Easy to add new role types
- **Testable**: Built-in test functions

### ✅ For System:
- **Real-time updates**: Changes take effect immediately
- **Performance**: Mappings cached in memory
- **Reliability**: Fallback to safe defaults
- **Audit trail**: All changes tracked in Excel

## 🚀 Future Enhancements

1. **High Tech Customers**: Add `HT` platform column for High Tech companies
2. **Multiple Roles**: Support customers with multiple roles (e.g., AMD with HT + CDM)
3. **Excel Validation**: Add data validation rules to Excel
4. **Web Interface**: Create web form for non-technical updates
5. **Database Migration**: Move from Excel to database if needed

## 🆘 Troubleshooting

### Issue: Customer not found
- **Check Excel file**: Ensure customer is listed with correct Platform
- **Check domain generation**: "Company Inc." → `company.com`
- **Test manually**: Use test commands above

### Issue: Wrong role assigned
- **Check Platform column**: Should be `LS-N`, `LS-Flex`, or `HT`
- **Case sensitivity**: Platform codes are case-sensitive
- **Refresh system**: Save Excel file to trigger refresh

### Issue: System not updating
- **File permissions**: Ensure Excel file is not locked/read-only
- **File path**: Ensure `LS-HT Customer Info.xlsx` is in correct folder
- **Manual refresh**: Restart system if needed

## 📞 Support

For technical support:
1. Run diagnostic commands above
2. Check system logs for errors
3. Verify Excel file format matches specification
4. Contact development team with error details

---

## 📋 Quick Reference Card

**Add Customer**: Add row to Excel → Save → Automatic refresh  
**Check Status**: `py customer_role_manager.py`  
**Test Customer**: `py test_dynamic_system.py`  
**Role Codes**: `LS-N`→PBN, `LS-Flex`→PBF, `HT`→HT  
**File Location**: `LS-HT Customer Info.xlsx`  

**✅ System automatically handles**: Domain generation, Role mapping, File monitoring, Fallback defaults
