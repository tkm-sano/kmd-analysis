"""Stateless, explicitly paired D3 streams with a stable serialized domain."""
import csv
from hashlib import sha256
import io
import json

VERSION = 'd3-rng-v2-sha256'
EXECUTION = 'iterative-d3-v2'
INT31 = (1 << 31) - 1
SCOPES = ('pilot', 'formal', 'diagnostic')


def key(context, group, purpose, iteration=-1, call=0):
    return (VERSION, EXECUTION, context['stage'], context['scale'], context['trial'],
            group, context.get('branch', -1), iteration, purpose, call)


def derive(logical_key, retry=0):
    data = json.dumps([logical_key, retry], separators=(',', ':'), ensure_ascii=True).encode('ascii')
    # Python's random.Random and NumPy PCG64 accept this nonnegative 128-bit seed
    # without our code shrinking it to uint32. C alone needs an int31 boundary.
    return int.from_bytes(sha256(data).digest()[:16], 'big')


def event(context, group, purpose, iteration=-1, call=0):
    return derive(key(context, group, purpose, iteration, call))


def context(stage, scale, index):
    if stage not in SCOPES:
        raise ValueError('UNKNOWN_RNG_STAGE')
    return dict(stage=stage, scale=scale, trial=index)


def call_seeds(ctx, method, iteration, maximum=24):
    if method == 'D_classical':
        return {'rng_seed': event(ctx, method, 'order-search', iteration)}
    return {'measurement_seeds': {
        'optimization': [event(ctx, method, 'learn-sample', iteration, i) for i in range(maximum)],
        'final': event(ctx, method, 'final-sample', iteration)}}


def rows(contexts, *, excluded):
    """Enumerate effective integers before execution and reject unresolved collisions."""
    used = set(excluded)
    c_used = set(excluded)
    for ctx in contexts:
        def add(group, purpose, iteration=-1, call=0, retry=0):
            logical = key(ctx, group, purpose, iteration, call)
            seed = derive(logical, retry)
            if group == 'C_Idual':
                seed %= INT31
            if seed in used:
                raise ValueError(f'DUPLICATE_EFFECTIVE_SEED:{logical}')
            used.add(seed)
            return (*logical, retry, seed)

        yield add('trial', 'trial-identity')
        # Resolve C's finite-domain conflicts deterministically, in registered case
        # order against the earlier plan and the forbidden old seed set.
        c_key = key(ctx, 'C_Idual', 'routing-and-cp')
        retry = 0
        while derive(c_key, retry) % INT31 in c_used:
            retry += 1
        row = add('C_Idual', 'routing-and-cp', retry=retry)
        c_used.add(row[-1])
        yield row
        for branch in range(4):
            bctx = ctx | {'branch': branch}
            logical = key(bctx, 'D_shared', 'branch-identity')
            seeds = [logical]
            for t in range(10):
                seeds.extend(key(bctx,'D_shared',p,t) for p in ('outer-neighbours','whole-transfer','local-window'))
                seeds.append(key(bctx,'D_classical','order-search',t))
                seeds.extend(key(bctx,'D_quantum','learn-sample',t,i) for i in range(24))
                seeds.append(key(bctx,'D_quantum','final-sample',t))
            for logical in seeds:
                seed = derive(logical)
                if seed in used:
                    raise ValueError(f'DUPLICATE_EFFECTIVE_SEED:{logical}')
                used.add(seed)
                yield (*logical, 0, seed)


def build(contexts, excluded=()):
    table = list(rows(contexts, excluded=set(excluded)))
    output = io.StringIO(newline='')
    writer = csv.writer(output, lineterminator='\n')
    writer.writerow(('rng_version','execution','stage','scale','trial','group','branch','iteration','purpose','call','retry','effective_seed'))
    writer.writerows(table)
    cases = {(r[2],r[3],r[4],r[5],r[6]):r[-1] for r in table if r[8] in ('trial-identity','branch-identity','routing-and-cp')}
    return output.getvalue(), cases
