"""Access/rights gate for optional external redistricting providers.

Never use a token or credentials unless they were explicitly connected and
the provider's approval and dataset licence permit the requested operation.
This module makes *no network requests* and writes *no secrets* to disk.
"""
from __future__ import annotations
import os

PLANSCORE_URL="https://planscore.org/"
RDH_API_URL="https://redistrictingdatahub.org/data/download-data/api-redistricting/"

def provider_access(env=None):
    if env is None:env=os.environ
    planscore_token=bool(str(env.get("PLANSCORE_API_TOKEN") or "").strip())
    rdh_credentials=bool(str(env.get("RDH_USERNAME") or "").strip() and
                         str(env.get("RDH_PASSWORD") or "").strip())
    rdh_approved=str(env.get("RDH_API_APPROVED") or "").strip().lower()=="true"
    return {
      "planscore":{
        "provider":PLANSCORE_URL,
        "requires_auth":True,
        "mode":"token_present_manual_terms_check_required" if planscore_token else "published_methodology_metadata_only",
        "permit_live_calls":False, # only after explicit per-endpoint terms and user permission
        "token_value_stored":False
      },
      "redistricting_data_hub":{
        "provider":RDH_API_URL,
        "requires_auth":True,
        "mode":"approved_credentials_present_license_check_required" if (rdh_credentials and rdh_approved)
               else "public_file_manifest_metadata_only",
        "permit_bulk_download":False, # separate approved API script and dataset-specific licensing required
        "approved_account_indicator":rdh_approved and rdh_credentials,
        "credentials_stored":False
      }
    }

if __name__=="__main__":
    import json
    print(json.dumps(provider_access(),indent=2))
