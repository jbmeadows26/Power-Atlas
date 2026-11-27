"""Validate and derive maturity exclusively from the Eastern Axis registry.

Evidence is an attestation with retrievable artifacts, not proof merely because
this validator accepts its shape. Independent review and actual execution remain
required. No private records may be added to the public registry.
"""
import argparse
import json
from pathlib import Path

DEFAULT = Path(__file__).resolve().parents[1] / 'site/development-control/acceptance.json'
STATES = {'Verified', 'Partial', 'Failed', 'Pending', 'Not applicable', 'Blocked'}


def summarize(data):
    def require(condition, message):
        if not condition:
            raise ValueError(message)

    require(data.get('schema') == 'eastern-axis.acceptance.v1', 'Unknown registry schema')
    requirements = data['requirements']
    ids = [r['id'] for r in requirements]
    require(len(ids) == 20 and set(ids) == {f'EA-{i:03}' for i in range(1, 21)}, 'Expected unique EA-001 through EA-020')
    gate_ids = [g['id'] for g in data['releaseGates']]
    require(len(gate_ids) == 11 and set(gate_ids) == {f'G{i:02}' for i in range(1, 12)}, 'Expected eleven unique release gates')
    evidence = {e['id']: e for e in data['evidence']}
    require(len(evidence) == len(data['evidence']), 'Duplicate evidence IDs')
    by_id = {r['id']: r for r in requirements}
    visited = set()
    def visit(identifier, active):
        require(identifier not in active, 'Dependency cycle')
        if identifier in visited:
            return
        for dep in by_id[identifier]['dependencies']:
            require(dep in by_id, 'Unknown dependency')
            visit(dep, active | {identifier})
        visited.add(identifier)
    for identifier in ids:
        visit(identifier, set())
    counts = {state: 0 for state in STATES}
    results = {}
    stage_counts = {}
    criterion_counts = {state: 0 for state in STATES}
    gate_counts = {state: 0 for state in STATES}
    for requirement in requirements:
        gates = requirement['gates']
        require(len(gates) == 11 and {g['id'] for g in gates} == set(gate_ids), 'Missing or duplicate gate')
        criteria = requirement['criteria']
        require(bool(criteria), 'Missing acceptance criteria')
        require(len({c['id'] for c in criteria}) == len(criteria), 'Duplicate criterion')
        for record in criteria + gates:
            state = record['state']
            require(state in STATES, 'Unknown acceptance state')
            counts[state] += 1
            (criterion_counts if record in criteria else gate_counts)[state] += 1
            if state == 'Not applicable':
                require(bool(record.get('reason', '').strip()), 'Inapplicable gate requires rationale')
                require(record['id'] not in {'G01', 'G09'}, 'Data and deployment gates are mandatory')
            for reference in record['evidence']:
                require(reference in evidence, 'Unknown evidence reference')
            if state == 'Verified':
                require(bool(record['evidence']), 'Verification requires evidence')
                for reference in record['evidence']:
                    e = evidence[reference]
                    require(all(e.get(k) for k in ('executedAt', 'commit', 'artifact', 'method', 'scope', 'result')), 'Incomplete evidence')
                    require(e['result'] == 'passed', 'Failed or unexecuted evidence cannot verify')
                    require(len(e['commit']) == 40 and all(c in '0123456789abcdef' for c in e['commit']), 'Evidence needs full commit SHA')
                    stage = e.get('stage', e['scope'])
                    require(stage in {'source', 'implemented', 'local', 'ci', 'deployed', 'production', 'commercial'}, 'Unknown evidence stage')
                    if record.get('stage') == 'production':
                        require(stage == 'production' and e.get('deployedCommit') == e['commit'], 'Production stage requires deployed evidence')
                    if record['id'] == 'G09':
                        require(e['scope'] == 'production' and e.get('deployedCommit') == e['commit'], 'Deployment requires production SHA match')
        for record in criteria + gates:
            if record['state'] == 'Verified':
                stage = record.get('stage', 'unspecified')
                stage_counts[stage] = stage_counts.get(stage, 0) + 1
        applicable = [r for r in criteria + gates if r['state'] != 'Not applicable']
        local_pass = bool(applicable) and all(r['state'] == 'Verified' for r in applicable)
        results[requirement['id']] = {'acceptanceSatisfied': local_pass, 'continuous': requirement['continuous']}
    # A dependency cannot be hidden by an otherwise successful capability.
    def ready(identifier):
        return results[identifier]['acceptanceSatisfied'] and all(ready(d) for d in by_id[identifier]['dependencies'])
    for identifier in ids:
        results[identifier]['releaseReady'] = ready(identifier)
        results[identifier]['complete'] = ready(identifier) and not results[identifier]['continuous']
    return {'states': counts, 'criterionStates': criterion_counts, 'gateStates': gate_counts, 'verifiedByStage': stage_counts, 'verifiedAcceptanceRecords': counts['Verified'],
            'applicableAcceptanceRecords': sum(counts.values()) - counts['Not applicable'],
            'notApplicableRecords': counts['Not applicable'], 'requirements': results}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('registry', nargs='?', type=Path, default=DEFAULT)
    args = parser.parse_args()
    print(json.dumps(summarize(json.loads(args.registry.read_text())), indent=2))
