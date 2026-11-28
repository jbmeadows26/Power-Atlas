#!/usr/bin/env python3
"""Compile conservative public analyst status from retained outputs and receipts.

Run-level conclusions never imply analysis, publication, or production outcomes.
Only explicit stage evidence may establish an axis, and current production also
requires DS-001 mechanical release context supplied separately.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
RECEIPTS = ROOT / "business-intelligence/analyst-execution-receipts.json"
OUTPUT = ROOT / "site/business-intelligence/data/analyst-registry.json"
DEFINITIONS = [
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
    ('Forecast Performance Analyst','brent-forecast-ledger.jsonl',None,'Chronological baseline error comparison; retain unsuccessful forecasts'),
]
CONCLUSIONS = {'success','failure','cancelled','skipped','timed_out','action_required','neutral','stale'}
STAGES = ('analysis', 'validation', 'publication', 'production')
STAGE_STATES = {
    'analysis': {'success','failed','skipped','cancelled','unavailable'},
    'validation': {'success','failed','skipped','cancelled','unavailable'},
    'publication': {'success','failed','skipped','cancelled','unavailable'},
    'production': {'verified','failed','stale','unavailable'},
}
RUN_URL = re.compile(r'https://github\.com/jbmeadows26/Power-Atlas/actions/runs/\d+(?:/job/\d+)?')
SHA40 = re.compile(r'[0-9a-f]{40}')
SHA64 = re.compile(r'[0-9a-f]{64}')


def _timestamp(value, field):
    if not isinstance(value, str):
        raise ValueError(f'{field} must be an ISO-8601 timestamp')
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise ValueError(f'{field} must be an ISO-8601 timestamp') from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError(f'{field} must identify UTC')
    return parsed


def validate_receipts(receipts):
    if not isinstance(receipts, list):
        raise ValueError('Receipts must be a list')
    seen = set()
    for index, receipt in enumerate(receipts):
        if not isinstance(receipt, dict):
            raise ValueError(f'receipt[{index}] must be an object')
        required = {'conclusion','headSha','updatedAt','url','workflowName'}
        missing = sorted(required - receipt.keys())
        if missing:
            raise ValueError(f'receipt[{index}] missing required fields {missing}')
        if receipt['conclusion'] not in CONCLUSIONS:
            raise ValueError(f"receipt[{index}] unknown conclusion {receipt['conclusion']!r}")
        if not isinstance(receipt['workflowName'], str) or not receipt['workflowName'].strip() or len(receipt['workflowName']) > 200:
            raise ValueError(f'receipt[{index}] invalid workflow identity')
        if not isinstance(receipt['url'], str) or not RUN_URL.fullmatch(receipt['url']):
            raise ValueError(f'receipt[{index}] invalid run URL')
        if receipt['url'] in seen:
            raise ValueError(f'receipt[{index}] duplicates run URL')
        seen.add(receipt['url'])
        if not isinstance(receipt['headSha'], str) or not SHA40.fullmatch(receipt['headSha']):
            raise ValueError(f'receipt[{index}] invalid head SHA')
        _timestamp(receipt['updatedAt'], f'receipt[{index}].updatedAt')
        stages = receipt.get('stageEvidence')
        if stages is None:
            continue
        if not isinstance(stages, dict) or set(stages) - set(STAGES):
            raise ValueError(f'receipt[{index}] invalid stage evidence')
        for stage, record in stages.items():
            if not isinstance(record, dict) or record.get('status') not in STAGE_STATES[stage]:
                raise ValueError(f'receipt[{index}] invalid {stage} status')
            evidence = record.get('evidence')
            if not isinstance(evidence, list) or not evidence or not all(isinstance(item, str) and item.strip() for item in evidence):
                raise ValueError(f'receipt[{index}] {stage} evidence must be nonempty')
            if record['status'] == 'failed' and (not isinstance(record.get('failureClassification'), str) or not isinstance(record.get('reason'), str)):
                raise ValueError(f'receipt[{index}] failed {stage} lacks classification and reason')
            if record.get('recordedAt') is not None:
                _timestamp(record['recordedAt'], f'receipt[{index}].{stage}.recordedAt')
            if stage == 'production' and record['status'] in {'verified','stale'}:
                if not isinstance(record.get('releaseCommit'), str) or not SHA40.fullmatch(record['releaseCommit']):
                    raise ValueError(f'receipt[{index}] production evidence lacks release commit')
        identity = receipt.get('snapshotIdentity')
        if identity is not None:
            if not isinstance(identity, dict) or not SHA64.fullmatch(identity.get('sha256','')):
                raise ValueError(f'receipt[{index}] invalid snapshot identity')
            _timestamp(identity.get('generatedAt'), f'receipt[{index}].snapshotIdentity.generatedAt')
            if identity.get('path') != 'eastern-axis/public/analysis/global-conflict-watch.json':
                raise ValueError(f'receipt[{index}] unauthorized snapshot identity path')
    return receipts


def _run_number(receipt):
    return int(receipt['url'].split('/runs/', 1)[1].split('/', 1)[0])


def _sorted_runs(receipts, workflow):
    runs = [receipt for receipt in receipts if workflow and receipt['workflowName'] == workflow]
    return sorted(runs, key=lambda receipt: (_timestamp(receipt['updatedAt'], 'updatedAt'), _run_number(receipt)), reverse=True)


def _trusted_release_commit(release_context):
    if not isinstance(release_context, dict) or release_context.get('status') != 'Verified':
        return None
    context = release_context.get('releaseContext')
    if not isinstance(context, dict) or context.get('schema') != 'eastern-axis.release-context.v1' or context.get('status') != 'Verified':
        return None
    commit = context.get('deployedCommit')
    if not isinstance(commit, str) or not SHA40.fullmatch(commit) or release_context.get('commit') != commit:
        return None
    return commit


def _axis(runs, stage, release_context):
    explicit = [receipt for receipt in runs if stage in receipt.get('stageEvidence', {})]
    history = []
    for receipt in explicit:
        record = receipt['stageEvidence'][stage]
        status = record['status']
        if stage == 'production' and status == 'verified':
            current = _trusted_release_commit(release_context)
            if current is None:
                status = 'unavailable'
            elif current != record['releaseCommit']:
                status = 'stale'
        history.append({
            'status': status,
            'recordedStatus': record['status'],
            'recordedAt': record.get('recordedAt') or receipt['updatedAt'],
            'headSha': receipt['headSha'],
            'evidence': record['evidence'],
            'failureClassification': record.get('failureClassification'),
            'reason': record.get('reason'),
            'releaseCommit': record.get('releaseCommit'),
            'runUrl': receipt['url'],
        })
    current = 'unavailable'
    if runs and explicit and runs[0]['url'] == explicit[0]['url']:
        current = history[0]['status']
    success_state = 'verified' if stage == 'production' else 'success'
    last_success = next((item for item in history if item['recordedStatus'] == success_state), None)
    return {'status': current, 'lastSuccessful': last_success, 'history': history}


def build(receipts, release_context=None):
    validate_receipts(receipts)
    analysts = []
    for index, (name, artifact, workflow, method) in enumerate(DEFINITIONS, 1):
        runs = _sorted_runs(receipts, workflow)
        axes = {stage: _axis(runs, stage, release_context) for stage in STAGES}
        path = ROOT / 'eastern-axis/public/analysis' / artifact if artifact else None
        data = None
        if path and path.exists() and path.suffix == '.json':
            data = json.loads(path.read_text())
        output_date = next((data[key] for key in ('generatedAt','checkedAt') if data and data.get(key)), None)
        latest = runs[0] if runs else None
        if axes['publication']['status'] == 'failed':
            legacy_status = 'failed'
        elif path and path.exists():
            legacy_status = 'partial'
        else:
            legacy_status = 'planned'
        analysis_success = axes['analysis']['lastSuccessful']
        analysts.append({
            'id': f'analyst-{index:02d}', 'name': name, 'responsibilities': method,
            'intelligenceRequirements': ['Original attributable observations','Explicit observation period','Declared customer dependency before private relevance claim'],
            'inputSources': [f'eastern-axis/public/analysis/{artifact}'] if artifact else [],
            'methodology': method,
            'outputSchema': 'eastern-axis.finding.v1: dependencyId, classification, observations, source, observationDate, freshness, implications, limitations, options',
            'operationalStatus': legacy_status,
            'analyticalStatus': axes['analysis']['status'],
            'validationStatus': axes['validation']['status'],
            'publicationStatus': axes['publication']['status'],
            'productionVerificationStatus': axes['production']['status'],
            'executionStages': axes,
            'lastSuccessfulExecution': analysis_success['recordedAt'] if analysis_success else None,
            'executionEvidence': analysis_success['runUrl'] if analysis_success else None,
            'lastSuccessfulAnalysis': axes['analysis']['lastSuccessful'],
            'lastSuccessfulPublication': axes['publication']['lastSuccessful'],
            'lastProductionVerification': axes['production']['lastSuccessful'],
            'latestExecution': latest,
            'outputGeneratedAt': output_date,
            'outputGeneratedAtMeaning': 'Generation time of the retained artifact; not the latest analytical attempt or underlying observation freshness.',
            'dataFreshness': 'Must assess each underlying observation; output generation is not observation freshness.',
            'outputValidation': 'Retained artifact exists; complete analyst responsibilities and production acceptance remain unverified.' if path and path.exists() else 'No validated shared output registered.',
            'coverageLimitations': ['Partial artifact coverage does not establish an operational analyst across its full remit.','No continuous private monitoring when browser is closed.'],
        })
    return {
        'schemaVersion': 2,
        'method': 'Analysis, validation, publication and current-production verification are independent. Run conclusions and artifact presence never establish a stage.',
        'releaseContextStatus': 'verified' if _trusted_release_commit(release_context) else 'unavailable',
        'analysts': analysts,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--release-context', type=Path)
    args = parser.parse_args()
    receipts = json.loads(RECEIPTS.read_text())
    context = json.loads(args.release_context.read_text()) if args.release_context else None
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(build(receipts, context), indent=2) + '\n')


if __name__ == '__main__':
    main()
