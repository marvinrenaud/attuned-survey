
import sys
import os

# Add project root (parent of backend)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.src.services.email_templates import PARTNER_REQUEST_TEMPLATE

url = "attuned://getattuned.app/connectionRequestsPage"
name = "My Test Partner"

# Render
rendered = PARTNER_REQUEST_TEMPLATE.format(partner_name=name, invite_url=url)

print("--- RENDERED HTML SNIPPET ---")
# Find line with link
for line in rendered.split('\n'):
    if "btn-primary" in line:
        print(line.strip())
    if "button not working" in line.lower() or "copy this link" in line.lower():
        print(line.strip())

if f'href="{url}"' in rendered:
    print("\nSUCCESS: Link found in HTML")
else:
    print("\nFAILURE: Link NOT found in HTML")
