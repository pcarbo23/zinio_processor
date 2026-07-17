import requests
import re
import datetime

def generate_basefile_value(pub_name: str, cover_date_str: str) -> str:
    """
    Generates a standardized basefile string from the publication name and issue cover date:
    - Magazine name converted to lowercase, special characters removed, whitespace/hyphens replaced with a single hyphen.
    - Cover date formatted as YYYY-MM-DD.
    """
    name = pub_name.lower()
    # Remove non-alphanumeric, non-whitespace, non-hyphen characters
    name = re.sub(r'[^a-z0-9\s-]', '', name)
    # Replace whitespace and hyphens with a single hyphen
    name = re.sub(r'[\s-]+', '-', name)
    # Clean leading/trailing hyphens
    name = name.strip('-')
    
    if cover_date_str:
        date_part = cover_date_str.split('T')[0]
        match = re.match(r'^(\d{4})-(\d{2})-(\d{2})', date_part)
        if match:
            formatted_date = match.group(0)
        else:
            formatted_date = datetime.date.today().isoformat()
    else:
        formatted_date = datetime.date.today().isoformat()
        
    return f"{name}_{formatted_date}"

def fetch_and_parse_metadata(api_url: str, token: str, newsstand_id: str, publication_id: str, issue_id: str) -> dict:
    """
    Fetches publication and issue data from the Zinio API, extracts and formats key fields:
    - 'Title': Combines publication name and issue name.
    - 'Language': Language code of the publication.
    - 'SourcePublisher': Publisher name of the publication.
    - 'Description': Description of the publication.
    - 'SourceDate': Date parsed from issue cover date, formatted as YYYY-MM-DD.
    - 'SourceRights': Copyright string combining the year of cover date and publisher name.
    - 'BaseFile': Magazine name formatted (all lowercase, no special characters, whitespace replaced with hyphens) + _ + cover date (YYYY-MM-DD).
    - 'Identifier': String 'us-nls-dm-' followed by BaseFile.
    """
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Fetch Publication Details
    pub_url = f"{api_url}/newsstand/v2/newsstands/{newsstand_id}/publications"
    pub_resp = requests.get(pub_url, headers=headers, timeout=15)
    pub_resp.raise_for_status()
    publications = pub_resp.json().get("data", [])
    
    selected_pub = None
    target_pub_id = int(publication_id)
    for pub in publications:
        if pub.get("id") == target_pub_id:
            selected_pub = pub
            break
            
    if not selected_pub:
        raise ValueError(f"Publication with ID {publication_id} not found in synced publications list.")
        
    # 2. Fetch Issue Details
    issues_url = f"{api_url}/newsstand/v2/newsstands/{newsstand_id}/publications/{publication_id}/issues"
    issues_resp = requests.get(issues_url, headers=headers, timeout=15)
    issues_resp.raise_for_status()
    issues = issues_resp.json().get("data", [])
    
    selected_issue = None
    target_issue_id = int(issue_id)
    for issue in issues:
        if issue.get("id") == target_issue_id:
            selected_issue = issue
            break
            
    if not selected_issue:
        raise ValueError(f"Issue with ID {issue_id} not found in issues list for publication {publication_id}.")

    # 3. Extract and parse fields
    pub_name = selected_pub.get("name", "")
    issue_name = selected_issue.get("name", "")
    title = f"{pub_name} - {issue_name}" if pub_name and issue_name else (pub_name or issue_name)
    
    language = selected_pub.get("language", {}).get("code", "en")
    
    publisher_name = selected_pub.get("publisher", {}).get("name", "")
    description = selected_pub.get("description", "")
    
    cover_date = selected_issue.get("cover_date", "")
    source_date = ""
    year = ""
    if cover_date:
        date_part = cover_date.split('T')[0]
        match = re.match(r'^(\d{4})-(\d{2})-(\d{2})', date_part)
        if match:
            source_date = match.group(0)
            year = match.group(1)
            
    if not source_date:
        today = datetime.date.today()
        source_date = today.isoformat()
        year = str(today.year)
        
    source_rights = f"{year} {publisher_name}".strip()
    
    basefile = generate_basefile_value(pub_name, cover_date)
    identifier = f"us-nls-dm-{basefile}"
    
    return {
        "Title": title,
        "Language": language,
        "SourcePublisher": publisher_name,
        "Description": description,
        "SourceDate": source_date,
        "SourceRights": source_rights,
        "BaseFile": basefile,
        "Identifier": identifier
    }
