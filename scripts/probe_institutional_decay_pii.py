"""Bounded no-credential probe of OECD PII public SDMX CSV delivery.

Probe and report metadata ONLY; do not invent, impute or commit partial data.
Standard library, no external services beyond official OECD data endpoint.
"""
import json
import urllib.request
import urllib.error

BASE="https://sdmx.oecd.org/public/rest/data/OECD.GOV.PSI,DSD_PII@DF_PUBLIC_INTEGRITY,"
KEY="/GBR+FRA+POL.A..._T."
QUERY="?startPeriod=2023&endPeriod=2025&dimensionAtObservation=AllDimensions"
URL=BASE+KEY+QUERY


def probe():
    result={"endpoint":URL,"status":"unavailable","sampleIsNotFullCountryPanel":True}
    request=urllib.request.Request(URL,headers={
        "Accept":"csvfile", "User-Agent":"PowerAtlasInstitutionalDecayResearch/1.0",
    })
    try:
        with urllib.request.urlopen(request,timeout=25) as response:
            raw=response.read(60000)
            content_type=response.headers.get("Content-Type","")
            text=raw.decode("utf-8-sig",errors="replace")
            lines=[s for s in text.splitlines() if s.strip()]
            result.update(httpStatus=response.status,contentType=content_type,
                          bytesSampled=len(raw),
                          headerSnippet=lines[0][:500] if lines else "",
                          dataSnippet=lines[1][:400] if len(lines)>1 else "",
                          status="candidate_response_needs_schema_validation" if lines else "empty")
    except urllib.error.HTTPError as exc:
        result.update(httpStatus=exc.code,reason=str(exc.reason),status="http_error")
    except (OSError,TimeoutError,UnicodeError) as exc:
        result.update(errorType=type(exc).__name__,reason=str(exc)[:300],status="transport_error")
    return result


if __name__=="__main__":
    print(json.dumps(probe(),indent=2))
