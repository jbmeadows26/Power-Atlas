"""Validate Eastern Axis acceptance evidence and derive release readiness.

The registry is the canonical assessment ledger. Current deployment identity is
supplied separately so editing the registry cannot make historical evidence
current. Without trusted release context, history is validated and current
production completion is withheld.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path, PurePosixPath
import re

DEFAULT = Path(__file__).resolve().parents[1] / 'site/development-control/acceptance.json'
STATES = {'Verified', 'Partial', 'Failed', 'Pending', 'Not applicable', 'Blocked'}
STAGES = {'source', 'local', 'ci', 'deployed', 'production', 'commercial'}
RESULTS = {'passed', 'failed'}
REQUIRED_MANDATORY_GATES = ('G01', 'G09')
PRODUCTION_GATES = {'G02', 'G05', 'G06', 'G07', 'G08'}
SHA = re.compile(r'^[0-9a-f]{40}$')
ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._:-]{0,119}$')


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _timestamp(value, label):
    _require(isinstance(value, str) and value.strip(), f'{label} timestamp is required')
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as error:
        raise ValueError(f'Invalid {label} timestamp') from error
    _require(parsed.tzinfo is not None, f'{label} timestamp needs a timezone')
    return parsed


def _full_sha(value, label):
    _require(isinstance(value, str) and SHA.fullmatch(value), f'{label} needs full commit SHA')


def normalize_release_context(value):
    """Validate external output from the mechanical release-identity verifier."""
    if value is None:
        return {'status': 'unavailable', 'reason': 'No independently verified release context supplied.', 'carryForwardEvidence': set()}
    _require(isinstance(value, dict), 'Release context must be an object')
    status = str(value.get('status', '')).lower()
    if status == 'unavailable':
        _require(isinstance(value.get('reason'), str) and value['reason'].strip(), 'Unavailable release context needs a reason')
        return {'status': 'unavailable', 'reason': value['reason'], 'carryForwardEvidence': set()}
    _require(status == 'verified', 'Release context must be verified or unavailable')
    commit = value.get('deployedCommit', value.get('commit'))
    _full_sha(commit, 'Release context')
    _require(isinstance(value.get('source'), str) and value['source'].strip(), 'Verified release context needs an independent source')
    _require(isinstance(value.get('artifact'), str) and value['artifact'].strip(), 'Verified release context needs an artifact')
    carry = value.get('carryForwardEvidence', [])
    _require(isinstance(carry, list) and len(carry) == len(set(carry)), 'Invalid release carry-forward evidence')
    _require(all(isinstance(item, str) and ID.fullmatch(item) for item in carry), 'Invalid release carry-forward evidence ID')
    return {'status': 'verified', 'deployedCommit': commit, 'source': value['source'], 'artifact': value['artifact'], 'carryForwardEvidence': set(carry)}


def load_release_context(path):
    raw = json.loads(path.read_text())
    return raw.get('releaseContext', raw)


def _safe_release_path(value):
    if not isinstance(value, str) or not value or '\\' in value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and '..' not in path.parts and path.parts[0] in {'site', 'business-intelligence', 'eastern-axis', 'personal-intelligence', 'adaptive-intelligence'}


def _validate_evidence(raw):
    _require(isinstance(raw, dict), 'Malformed evidence record')
    for field in ('id', 'executedAt', 'commit', 'artifact', 'method', 'scope', 'stage', 'result', 'disposition'):
        _require(field in raw, f'Evidence missing {field}')
    _require(isinstance(raw['id'], str) and ID.fullmatch(raw['id']), 'Invalid evidence ID')
    _timestamp(raw['executedAt'], 'evidence')
    _full_sha(raw['commit'], 'Evidence')
    for field in ('artifact', 'method', 'scope'):
        _require(isinstance(raw[field], str) and raw[field].strip(), f'Evidence {field} is required')
    _require(raw['stage'] in STAGES, 'Unknown evidence stage')
    _require(raw['result'] in RESULTS, 'Unknown evidence result')
    disposition = raw['disposition']
    _require(isinstance(disposition, dict) and disposition.get('class') in {'assessment', 'release', 'historical'}, 'Invalid evidence disposition')
    if disposition['class'] != 'assessment':
        _require(isinstance(disposition.get('reason'), str) and disposition['reason'].strip(), 'Non-assessment evidence needs a disposition reason')
    if raw['stage'] in {'deployed', 'production', 'commercial'}:
        _full_sha(raw.get('deployedCommit'), 'Deployed evidence')
        _require(raw['deployedCommit'] == raw['commit'], 'Evidence and deployed commit must match')
    elif 'deployedCommit' in raw:
        _full_sha(raw['deployedCommit'], 'Deployed evidence')
    if 'supplementalArtifacts' in raw:
        _require(isinstance(raw['supplementalArtifacts'], list) and all(isinstance(v, str) and v.strip() for v in raw['supplementalArtifacts']), 'Invalid supplemental evidence artifacts')
    if 'releaseScope' in raw:
        scope = raw['releaseScope']
        _require(isinstance(scope, dict) and scope.get('policy') == 'unchanged-assets', 'Invalid release-scope policy')
        paths = scope.get('paths')
        _require(isinstance(paths, list) and paths and len(paths) == len(set(paths)), 'Invalid release-scope paths')
        _require(all(_safe_release_path(path) for path in paths), 'Unsafe release-scope path')
        _require('site/development-control/acceptance.json' not in paths, 'Acceptance registry cannot carry its own verification forward')
        _require(raw['stage'] != 'commercial', 'Commercial evidence cannot carry forward solely because assets are unchanged')
    return raw


def _validate_assessment(record, evidence, mandatory, *, historical=False):
    label = 'Historical assessment' if historical else 'Assessment'
    _require(isinstance(record, dict), f'Malformed {label.lower()}')
    _require(record.get('state') in STATES, f'Invalid {label.lower()} state')
    refs = record.get('evidence')
    _require(isinstance(refs, list), f'{label} evidence must be a list')
    _require(len(refs) == len(set(refs)), f'Duplicate evidence references in {label.lower()}')
    for reference in refs:
        _require(reference in evidence, f'Unknown evidence reference in {label.lower()}')
        _require(evidence[reference]['disposition']['class'] == 'assessment', f'{label} cannot use release-level or unattached historical evidence')
    state = record['state']
    stage = record.get('stage')
    if state in {'Verified', 'Partial', 'Failed'}:
        _require(stage in STAGES, f'{label} needs an explicit valid stage')
        _require(refs, f'{state} {label.lower()} requires evidence')
        for reference in refs:
            _require(evidence[reference]['stage'] == stage, f'Evidence stage does not match {label.lower()} stage')
        if state == 'Verified':
            _require(all(evidence[reference]['result'] == 'passed' for reference in refs), 'Verified assessment requires passing evidence')
        elif state == 'Failed':
            _require(any(evidence[reference]['result'] == 'failed' for reference in refs), 'Failed assessment requires failed execution evidence')
        else:
            _require(any(evidence[reference]['result'] == 'passed' for reference in refs), 'Partial assessment requires passing bounded evidence')
        _timestamp(record.get('assessedAt'), 'assessment')
    else:
        _require(stage is None, f'{state} assessment cannot claim a verification stage')
        _require(not refs, f'{state} assessment cannot reference verification evidence')
    reason = record.get('reason', '')
    if state in {'Partial', 'Failed', 'Not applicable', 'Blocked'}:
        _require(isinstance(reason, str) and reason.strip(), f'{state} assessment requires a reason')
    if state == 'Not applicable':
        _require(record.get('id') not in mandatory, 'Mandatory gate cannot be waived')
    if state == 'Blocked':
        blocker = record.get('blocker')
        _require(isinstance(blocker, dict), 'Blocked assessment requires an explicit blocker')
        _require(blocker.get('type') in {'external', 'dependency', 'permission', 'source', 'commercial-participation'}, 'Invalid blocker type')
        _require(isinstance(blocker.get('description'), str) and blocker['description'].strip(), 'Blocked assessment requires blocker description')
    elif 'blocker' in record:
        _require(record['blocker'] is None, 'Only Blocked assessments may declare a blocker')
    if historical:
        _timestamp(record.get('assessedAt'), 'historical assessment')


def _validate_history(record, evidence, mandatory):
    history = record.get('assessmentHistory', [])
    _require(isinstance(history, list), 'Assessment history must be a list')
    previous_time = None
    prior_state = None
    allowed = {
        'Pending': {'Verified', 'Partial', 'Failed', 'Blocked', 'Not applicable'},
        'Partial': {'Verified', 'Failed', 'Blocked', 'Not applicable'},
        'Failed': {'Verified', 'Partial', 'Blocked'},
        'Blocked': {'Pending', 'Verified', 'Partial', 'Failed', 'Not applicable'},
        'Verified': {'Partial', 'Failed', 'Blocked'},
        'Not applicable': {'Pending', 'Verified', 'Partial', 'Failed', 'Blocked'},
    }
    for entry in history:
        candidate = dict(entry, id=record.get('id'))
        _validate_assessment(candidate, evidence, mandatory, historical=True)
        moment = _timestamp(entry['assessedAt'], 'historical assessment')
        _require(previous_time is None or moment > previous_time, 'Assessment history timestamps must increase')
        if prior_state is not None:
            _require(entry['state'] in allowed[prior_state], 'Unsupported assessment state transition')
        previous_time, prior_state = moment, entry['state']
    if prior_state is not None:
        _require(record['state'] in allowed[prior_state], 'Unsupported assessment state transition')
        if record['state'] in {'Verified', 'Partial', 'Failed'}:
            _require(_timestamp(record['assessedAt'], 'assessment') > previous_time, 'Current assessment must follow its history')
    if record['state'] in {'Verified', 'Partial', 'Failed'}:
        _require(history, 'Assessed records must preserve their prior assessment history')


def _evidence_currency(item, release_context):
    if release_context['status'] != 'verified':
        return 'unavailable'
    if item['commit'] == release_context['deployedCommit']:
        return 'current'
    if item['id'] in release_context['carryForwardEvidence'] and item.get('releaseScope', {}).get('policy') == 'unchanged-assets':
        return 'current-unchanged-scope'
    return 'stale'


def summarize(data, release_context=None):
    release_context = normalize_release_context(release_context)
    _require(isinstance(data, dict) and data.get('schema') == 'eastern-axis.acceptance.v2', 'Unknown registry schema')
    _require(data.get('states') == ['Verified', 'Partial', 'Failed', 'Pending', 'Not applicable', 'Blocked'], 'Invalid canonical state declaration')
    policy = data.get('mandatoryGatePolicy')
    _require(isinstance(policy, dict), 'Missing mandatory-gate declaration')
    _require(policy == {'schema': 'eastern-axis.mandatory-gates.v1', 'gateIds': list(REQUIRED_MANDATORY_GATES), 'nonWaivable': True}, 'Invalid or unauthorized mandatory-gate policy')
    mandatory = set(policy['gateIds'])
    release_gates = data.get('releaseGates')
    _require(isinstance(release_gates, list), 'Missing release gates')
    gate_ids = [gate.get('id') for gate in release_gates]
    _require(len(gate_ids) == 11 and set(gate_ids) == {f'G{i:02}' for i in range(1, 12)}, 'Expected eleven unique release gates')
    requirements = data.get('requirements')
    _require(isinstance(requirements, list), 'Missing requirements')
    ids = [requirement.get('id') for requirement in requirements]
    _require(len(ids) == 20 and set(ids) == {f'EA-{i:03}' for i in range(1, 21)}, 'Expected unique EA-001 through EA-020')
    evidence_list = data.get('evidence')
    _require(isinstance(evidence_list, list), 'Missing evidence registry')
    evidence = {}
    for raw in evidence_list:
        item = _validate_evidence(raw)
        _require(item['id'] not in evidence, 'Duplicate evidence IDs')
        evidence[item['id']] = item
    by_id = {requirement['id']: requirement for requirement in requirements}
    visited = set()
    def visit(identifier, active):
        _require(identifier not in active, 'Dependency cycle')
        if identifier in visited:
            return
        dependencies = by_id[identifier].get('dependencies')
        _require(isinstance(dependencies, list) and len(dependencies) == len(set(dependencies)), 'Invalid requirement dependencies')
        for dependency in dependencies:
            _require(dependency in by_id, 'Unknown dependency')
            visit(dependency, active | {identifier})
        visited.add(identifier)
    for identifier in ids:
        visit(identifier, set())
    counts = {state: 0 for state in STATES}
    current_counts = {state: 0 for state in STATES | {'Stale', 'Unavailable'}}
    criterion_counts = {state: 0 for state in STATES}
    gate_counts = {state: 0 for state in STATES}
    stage_counts = {stage: 0 for stage in STAGES}
    references = {identifier: [] for identifier in evidence}
    assessment_details = {}
    for requirement in requirements:
        criteria = requirement.get('criteria')
        gates = requirement.get('gates')
        _require(isinstance(criteria, list) and criteria, 'Missing acceptance criteria')
        _require(len({criterion.get('id') for criterion in criteria}) == len(criteria), 'Duplicate criterion')
        _require(isinstance(gates, list) and len(gates) == 11 and {gate.get('id') for gate in gates} == set(gate_ids), 'Missing or duplicate gate')
        for kind, records in (('criterion', criteria), ('gate', gates)):
            for record in records:
                _validate_assessment(record, evidence, mandatory)
                _validate_history(record, evidence, mandatory)
                counts[record['state']] += 1
                (criterion_counts if kind == 'criterion' else gate_counts)[record['state']] += 1
                if record['state'] == 'Verified':
                    stage_counts[record['stage']] += 1
                for reference in record['evidence']:
                    references[reference].append(f"{requirement['id']}:{record['id']}:current")
                for index, history in enumerate(record.get('assessmentHistory', [])):
                    for reference in history['evidence']:
                        references[reference].append(f"{requirement['id']}:{record['id']}:history:{index}")
                effective = record['state']
                currencies = [_evidence_currency(evidence[reference], release_context) for reference in record['evidence']]
                if record['state'] in {'Verified', 'Partial', 'Failed'}:
                    if kind == 'gate' and record['id'] == 'G09' and record['state'] == 'Verified':
                        effective = 'Verified' if release_context['status'] == 'verified' else 'Unavailable'
                    elif any(value == 'unavailable' for value in currencies):
                        effective = 'Unavailable'
                    elif any(value == 'stale' for value in currencies):
                        effective = 'Stale'
                current_counts[effective] += 1
                assessment_details[(requirement['id'], record['id'])] = {'state': record['state'], 'currentState': effective, 'stage': record.get('stage'), 'evidenceCurrency': currencies}
    for identifier, item in evidence.items():
        if item['disposition']['class'] == 'assessment':
            _require(references[identifier], 'Assessment evidence is not referenced by any current or historical assessment')
    evidence_currency = {identifier: _evidence_currency(item, release_context) for identifier, item in evidence.items()}
    results = {}
    for requirement in requirements:
        records = requirement['criteria'] + requirement['gates']
        applicable = [record for record in records if record['state'] != 'Not applicable']
        acceptance_satisfied = bool(applicable) and all(record['state'] == 'Verified' for record in applicable)
        current_acceptance_satisfied = bool(applicable) and all(assessment_details[(requirement['id'], record['id'])]['currentState'] == 'Verified' for record in applicable)
        production_contract = []
        for record in requirement['criteria']:
            if record['state'] != 'Not applicable':
                production_contract.append((record, {'production', 'commercial'}))
        for gate in requirement['gates']:
            if gate['state'] == 'Not applicable':
                continue
            if gate['id'] in PRODUCTION_GATES:
                production_contract.append((gate, {'production'}))
            elif gate['id'] == 'G09':
                production_contract.append((gate, {'deployed'}))
        workflow_verified = bool(production_contract) and all(record['state'] == 'Verified' and record.get('stage') in stages and assessment_details[(requirement['id'], record['id'])]['currentState'] == 'Verified' for record, stages in production_contract)
        direct = []
        for record in applicable:
            detail = assessment_details[(requirement['id'], record['id'])]
            if detail['currentState'] != 'Verified':
                direct.append({'assessmentId': record['id'], 'state': record['state'], 'currentState': detail['currentState'], 'reason': record.get('reason', '')})
        results[requirement['id']] = {'acceptanceSatisfied': acceptance_satisfied, 'currentAcceptanceSatisfied': current_acceptance_satisfied, 'productionWorkflowVerified': workflow_verified, 'continuous': bool(requirement.get('continuous')), 'directBlockers': direct, 'dependencyDerivedBlockers': []}
    def ready(identifier, active=None):
        active = active or set()
        if identifier in active:
            return False
        own = results[identifier]['currentAcceptanceSatisfied'] and results[identifier]['productionWorkflowVerified']
        return own and all(ready(dependency, active | {identifier}) for dependency in by_id[identifier]['dependencies'])
    for identifier in ids:
        results[identifier]['dependencyDerivedBlockers'] = [dependency for dependency in by_id[identifier]['dependencies'] if not ready(dependency)]
        results[identifier]['releaseReady'] = ready(identifier)
        results[identifier]['complete'] = ready(identifier) and not results[identifier]['continuous']
    return {
        'schema': 'eastern-axis.acceptance-summary.v2',
        'currentRelease': {key: value for key, value in release_context.items() if key != 'carryForwardEvidence'},
        'states': counts,
        'currentStates': current_counts,
        'criterionStates': criterion_counts,
        'gateStates': gate_counts,
        'verifiedByStage': {stage: count for stage, count in stage_counts.items() if count},
        'verifiedAcceptanceRecords': counts['Verified'],
        'currentVerifiedAcceptanceRecords': current_counts['Verified'],
        'currentProductionVerifiedRecords': sum(1 for detail in assessment_details.values() if detail['currentState'] == 'Verified' and detail['stage'] in {'deployed', 'production', 'commercial'}),
        'applicableAcceptanceRecords': sum(counts.values()) - counts['Not applicable'],
        'notApplicableRecords': counts['Not applicable'],
        'evidenceCurrency': evidence_currency,
        'staleEvidence': sorted(identifier for identifier, state in evidence_currency.items() if state == 'stale'),
        'assessmentStates': {f'{requirement}:{assessment}': detail for (requirement, assessment), detail in assessment_details.items()},
        'requirements': results,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('registry', nargs='?', type=Path, default=DEFAULT)
    parser.add_argument('--release-context', type=Path, help='Mechanically verified output from pages_release_identity.py verify')
    args = parser.parse_args()
    context = load_release_context(args.release_context) if args.release_context else None
    print(json.dumps(summarize(json.loads(args.registry.read_text()), context), indent=2))
