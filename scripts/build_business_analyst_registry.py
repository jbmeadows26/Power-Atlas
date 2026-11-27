"""Compile public analyst coverage from retained outputs and inspected Actions receipts.
No customer information or model inference enters this registry.
"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DEFINITIONS=[
('Early Warning Analyst','physical-early-warning.json','Eastern Axis physical early warning','Dated physical indicators and source-specific thresholds'),
('Global Conflict Analyst','global-conflict-watch.json','Eastern Axis global conflict analyst','Geographic source corroboration; no unsupported attribution'),
('Military Asset Analyst','military-asset-changes.json','Eastern Axis military asset analyst','Dated official inventory observations and change comparison'),
('Product Shortage Analyst','product-shortage-outlook.json','Eastern Axis product shortage intelligence','Independent supply proxies; no confirmed stockout from price alone'),
('Supply Chain Analyst','physical-early-warning.json',None,'Declared route matching against dated physical observations'),
('Procurement Analyst','product-shortage-outlook.json',None,'Input-price changes and exact tariff reference; legal applicability withheld'),
('Corporate Analyst','financial-transmission.json',None,'Official issuer filing evidence; missing coverage is unavailable'),
('Economic Analyst','financial-markets.json',None,'Published macro/market observations and explicit date checks'),
('Financial Contagion Analyst','financial-transmission.json',None,'Financial transmission indicators; correlation is not causation'),
('Energy Analyst','product-shortage-outlook.json',None,'Original energy observations and benchmark scope'),
('Regulatory Analyst',None,None,'Original legal notices with jurisdiction and effective date'),
('Cyber Analyst',None,None,'Original advisory plus approved vendor/version applicability'),
('Workforce Analyst',None,None,'Original labor observations plus declared workforce dependency'),
('Opportunity Analyst','product-shortage-outlook.json',None,'Independent falling-input-price evidence; no invented savings'),
('Business Strategy Analyst',None,None,'Approved dependency and validated finding to bounded options'),
('Personal Intelligence Analyst',None,None,'Separate private household matching; never business profile transfer'),
('Evidence Validation Analyst','early-warning-triage.json','Eastern Axis signal analyst','Evidence ID validation, freshness and unsupported-claim suppression'),
('Forecast Performance Analyst','brent-forecast-ledger.jsonl',None,'Chronological baseline error comparison; retain unsuccessful forecasts')]
def build(receipts):
 result=[]
 for i,(name,artifact,workflow,method) in enumerate(DEFINITIONS,1):
  runs=[r for r in receipts if workflow and r['workflowName']==workflow]
  last=next((r for r in runs if r['conclusion']=='success'),None)
  latest=runs[0] if runs else None
  path=ROOT/'eastern-axis/public/analysis'/artifact if artifact else None
  data=None
  if path and path.exists() and path.suffix=='.json':data=json.loads(path.read_text())
  output_date=next((data[k] for k in ['generatedAt','checkedAt'] if data and data.get(k)),None)
  status='failed' if latest and latest['conclusion']=='failure' else 'partial' if path and path.exists() else 'planned'
  result.append({'id':f'analyst-{i:02d}','name':name,'responsibilities':method,'intelligenceRequirements':['Original attributable observations','Explicit observation period','Declared customer dependency before private relevance claim'], 'inputSources':[f'eastern-axis/public/analysis/{artifact}'] if artifact else [],'methodology':method,'outputSchema':'eastern-axis.finding.v1: dependencyId, classification, observations, source, observationDate, freshness, implications, limitations, options','operationalStatus':status,'lastSuccessfulExecution':last['updatedAt'] if last else None,'executionEvidence':last['url'] if last else None,'latestExecution':latest,'outputGeneratedAt':output_date,'dataFreshness':'Must assess each underlying observation; output generation is not observation freshness.','outputValidation':'Retained artifact exists; complete analyst responsibilities and production acceptance remain unverified.' if path and path.exists() else 'No validated shared output registered.','coverageLimitations':['Partial artifact coverage does not establish an operational analyst across its full remit.','No continuous private monitoring when browser is closed.']})
 return {'schemaVersion':1,'method':'Statuses derive from retained public outputs and explicitly inspected workflow receipts. No analyst is operational merely because code exists.','analysts':result}
if __name__=='__main__':
 receipts=json.loads((ROOT/'business-intelligence/analyst-execution-receipts.json').read_text())
 output=ROOT/'site/business-intelligence/data/analyst-registry.json';output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(build(receipts),indent=2)+'\n')
