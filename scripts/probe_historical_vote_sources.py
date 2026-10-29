"""Bounded diagnostic probes for absent Voteview 114th-117th Congresses.

No raw member voting records are stored. Prints only official tag paths,
counts and HTTP statuses. Independent of production feed.
"""
from collections import Counter
from urllib.error import HTTPError,URLError
from urllib.request import Request,urlopen
from xml.etree import ElementTree as ET
import re
from html.parser import HTMLParser

URLS=[
"https://clerk.house.gov/evs/2015/roll001.xml",
"https://clerk.house.gov/evs/2015/ROLL_000.asp",
"https://clerk.house.gov/evs/2021/roll001.xml",
"https://www.senate.gov/legislative/LIS/roll_call_lists/vote_menu_114_1.xml",
"https://www.senate.gov/legislative/LIS/roll_call_votes/vote1141/vote_114_1_00001.xml",
"https://www.senate.gov/legislative/LIS/roll_call_votes/vote1172/vote_117_2_00001.xml",
"https://voteview.com/static/data/out/votes/H114_votes.csv",
"https://voteview.com/static/data/out/votes/S114_votes.csv",
"https://voteview.com/static/data/out/votes/HS114_votes.csv",
"https://voteview.com/static/data/out/members/H114_members.csv",
"https://voteview.com/static/data/out/members/S114_members.csv",
"https://voteview.com/static/data/out/members/HS114_members.csv",
"https://voteview.com/static/data/out/members/HS115_members.csv",
"https://voteview.com/static/data/out/members/HS116_members.csv",
"https://voteview.com/static/data/out/members/HS117_members.csv"
]
LIMIT=180000
for url in URLS:
    try:
        with urlopen(Request(url,headers={"User-Agent":"PowerAtlasResearch/1.0 official-public-record-audit"}),timeout=22) as response:
            raw=response.read(LIMIT+1)
            status=response.status
        tags={}
        if raw.lstrip().startswith(b"<") and not raw.lstrip().startswith(b"<!doctype html"):
            try:
                root=ET.fromstring(raw)
                tags=dict(Counter(node.tag.rsplit('}',1)[-1] for node in root.iter()).most_common(18))
                for key in ('recorded-vote','legislator','member','vote','vote_cast','party','vote_number','vote_date'):
                    tags.setdefault(key,Counter(node.tag.rsplit('}',1)[-1] for node in root.iter()).get(key,0))
                # Only key/attributes of first recorded member; not private info
                record=next((x for x in root.iter() if x.tag.rsplit('}',1)[-1] in ('recorded-vote','member')),None)
                tags["sample_member_tags"]=[x.tag.rsplit('}',1)[-1] for x in record.iter()] if record is not None else []
                tags["sample_member_attr_keys"]=list(record.attrib) if record is not None else []
            except ET.ParseError:tags={"XML_parse":"truncated_or_non_xml"}
        elif b"roll" in raw.lower():
            nums=re.findall(rb'roll0*([0-9]{1,4})[.]xml',raw,re.I)
            tags={"roll_xml_links":len(set(nums)),"examples":[x.decode() for x in nums[:3]]}
        if b',' in raw[:500] and url.endswith(".csv"):
            lines=raw.decode("utf-8",errors="replace").splitlines()
            rows=[line.split(",") for line in lines[1:8]]
            tags={"csv_header":lines[0],"sample_bytes":len(raw),"csv_lines_first_chunk":len(lines),"first_rows":[[row[i] if i < len(row) else "" for i in ((0,1,2,3,4) if "/votes/" in url else (0,1,2,6))] for row in rows],"last_row":lines[-2].split(",")[:4]}
        print("SOURCE",url,"HTTP",status,"bytes_first_chunk",len(raw),"TAGS",tags,flush=True)
    except (HTTPError,URLError,TimeoutError) as exc:
        print("SOURCE",url,"ERROR",str(exc)[:180],flush=True)
