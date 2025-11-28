"""
Find Organization Name Matches
"""

from organization_access_controller import org_access_controller

def find_matches():
    """Find what's causing the false positives"""
    
    query = "Salesforce accounts are not syncing to MN prod"
    query_lower = query.lower()
    
    print(f"🔍 ANALYZING QUERY: '{query}'")
    print("=" * 60)
    
    all_orgs = org_access_controller.all_jira_organizations
    aliases = org_access_controller.org_name_to_aliases
    
    print(f"Total organizations: {len(all_orgs)}")
    print()
    
    # Check each organization and its aliases
    matches = []
    for org_name in all_orgs:
        # Check org name
        org_lower = org_name.lower()
        
        # Check for matches
        import re
        
        # Check full org name
        pattern = r'\b' + re.escape(org_lower) + r'\b'
        if re.search(pattern, query_lower):
            matches.append(f"FULL ORG: '{org_name}' matched in query")
        
        # Check aliases
        if org_name in aliases:
            for alias in aliases[org_name]:
                alias_lower = alias.lower()
                alias_pattern = r'\b' + re.escape(alias_lower) + r'\b'
                if re.search(alias_pattern, query_lower):
                    matches.append(f"ALIAS: '{alias}' (from {org_name}) matched in query")
        
        # Check for partial word matches that might be causing issues
        words_in_query = query_lower.split()
        org_words = org_lower.split()
        
        for query_word in words_in_query:
            for org_word in org_words:
                if query_word == org_word:
                    matches.append(f"WORD MATCH: '{query_word}' matches word in '{org_name}'")
    
    if matches:
        print("🚫 FOUND MATCHES:")
        for match in matches:
            print(f"   {match}")
    else:
        print("✅ No matches found - this should be allowed")
    
    print()
    
    # Also check specific problematic orgs
    problem_orgs = ['Galderma', 'Baxter International Inc.', 'Apotex Inc.']
    print("🔍 CHECKING PROBLEM ORGANIZATIONS:")
    for org in problem_orgs:
        org_lower = org.lower()
        print(f"\nOrg: '{org}'")
        print(f"Lowercase: '{org_lower}'")
        
        # Check if any word in org matches any word in query
        org_words = org_lower.split()
        query_words = query_lower.split()
        
        for org_word in org_words:
            for query_word in query_words:
                if org_word == query_word or org_word in query_word or query_word in org_word:
                    print(f"   ⚠️ MATCH: '{org_word}' ~ '{query_word}'")
        
        # Check regex pattern
        pattern = r'\b' + re.escape(org_lower) + r'\b'
        if re.search(pattern, query_lower):
            print(f"   ✅ Regex match found")
        else:
            print(f"   ❌ No regex match - why is this being blocked?")

if __name__ == "__main__":
    find_matches()