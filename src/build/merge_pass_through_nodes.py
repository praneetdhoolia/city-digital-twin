"""Merge a MATSim network's pass-through nodes into longer links (9.207).

A node that only passes traffic through - one link in and one out, or the
two anti-parallel pairs of a two-way street - decides nothing: it is where
one OSM way ends and the next begins. At a small sample fraction each such
node costs the queue a whole link: a link's storage is its length times its
lanes times the fraction, so a 65 m link at 1 % stores a tenth of a vehicle
and the mobsim reads it as a gate (9.206). Merging the chain gives the queue
the street's real length back without changing its capacity, its speed, its
lanes, its modes or its class.

Two links merge across a node only when they agree on every value the run
reads (`freespeed`, `capacity`, `permlanes`, `oneway`, `modes` and the OSM
class attributes) and the merged length stays under the converter's own
`A.network.max_link_length_m`, so a merged link is never longer than one the
converter would itself have written. The in-link keeps its id and its
attributes; the ids of the links it absorbed and their OSM way ids are
recorded on it (`merged_link_ids`, `merged_osm_way_ids`) so a reading can
still be traced to the source ways. A link that carries or is named by a
turn restriction (`disallowedNextLinks`) never merges: its id is a reference
another link holds. Nodes are visited in id order and the maps are updated
live, so a chain merges the same way whatever its length, and the output is
written with a zero-header gzip so the network stays byte-reproducible.

Usage (also called by build_matsim_network.py on the base network):

    python src/build/merge_pass_through_nodes.py <network.xml.gz> <out.xml.gz> --max-length 500
"""
import argparse
import collections
import gzip
import json
import re
import sys

HEADER_END = '<links'
NODE_RE = re.compile(r'\s*<node id="([^"]+)"[^>]*?(?:/>|>.*?</node>)', re.S)
LINK_BLOCK_RE = re.compile(r'\s*<link\b.*?</link>|\s*<link\b[^>]*/>', re.S)
LINK_HEAD_RE = re.compile(r'<link\b([^>]*?)/?>')
ATTR_RE = re.compile(r'(\w[\w:]*)="([^"]*)"')
LINK_ATTRIBUTE_RE = re.compile(r'<attribute name="([^"]+)" class="([^"]+)">([^<]*)</attribute>')
NODE_ATTRIBUTES_RE = re.compile(r'<attributes>')

# the link values that must agree before two links become one; the OSM class
# attributes the run-input assembly reads (`osm:way:highway`) are compared too
MERGE_KEYS = ('freespeed', 'capacity', 'permlanes', 'oneway', 'modes')
MERGE_ATTRIBUTES = ('osm:way:highway', 'osm:way:railway')
TURN_RESTRICTION = 'disallowedNextLinks'


def parse_links(body):
    """Every link block as a dict: its head fields, its attributes, its text."""
    links = collections.OrderedDict()
    for m in LINK_BLOCK_RE.finditer(body):
        block = m.group(0)
        head = LINK_HEAD_RE.search(block)
        fields = dict(ATTR_RE.findall(head.group(1)))
        attrs = collections.OrderedDict((n, (c, t)) for n, c, t in LINK_ATTRIBUTE_RE.findall(block))
        links[fields['id']] = dict(fields=fields, attrs=attrs, block=block)
    return links


def frozen_links(links):
    """Links a turn restriction lives on or names: their ids are references."""
    frozen = set()
    for lid, link in links.items():
        if TURN_RESTRICTION not in link['attrs']:
            continue
        frozen.add(lid)
        try:
            by_mode = json.loads(link['attrs'][TURN_RESTRICTION][1])
        except ValueError:
            continue
        for sequences in by_mode.values():
            for sequence in sequences:
                frozen.update(sequence)
    return frozen


def compatible(a, b):
    fa, fb = a['fields'], b['fields']
    if any(fa.get(k) != fb.get(k) for k in MERGE_KEYS):
        return False
    return all(a['attrs'].get(k, ('', ''))[1] == b['attrs'].get(k, ('', ''))[1]
               for k in MERGE_ATTRIBUTES)


def merge_network(xml, max_length_m):
    """The network text with its pass-through nodes merged, and the counts."""
    split = xml.index(HEADER_END)
    head, body = xml[:split], xml[split:]
    nodes = collections.OrderedDict()
    for m in NODE_RE.finditer(head):
        nodes[m.group(1)] = m.group(0)
    links = parse_links(body)
    frozen = frozen_links(links)
    in_links = collections.defaultdict(list)
    out_links = collections.defaultdict(list)
    for lid, link in links.items():
        out_links[link['fields']['from']].append(lid)
        in_links[link['fields']['to']].append(lid)
    counts = collections.Counter(nodes_before=len(nodes), links_before=len(links))
    removed_nodes, removed_links = set(), set()
    lengths_before = [float(l['fields']['length']) for l in links.values()]

    def pairs_at(node):
        ins, outs = in_links.get(node, []), out_links.get(node, [])
        if len(ins) == 1 and len(outs) == 1:
            a, b = ins[0], outs[0]
            if links[a]['fields']['from'] == links[b]['fields']['to']:
                return None          # a dead-end spur folded back on itself
            return [(a, b)]
        if len(ins) == 2 and len(outs) == 2:
            froms = {links[l]['fields']['from']: l for l in ins}
            tos = {links[l]['fields']['to']: l for l in outs}
            if len(froms) != 2 or set(froms) != set(tos):
                return None
            neighbours = sorted(froms)
            if node in neighbours:
                return None
            return [(froms[neighbours[0]], tos[neighbours[1]]),
                    (froms[neighbours[1]], tos[neighbours[0]])]
        return None

    for node in sorted(nodes):
        if NODE_ATTRIBUTES_RE.search(nodes[node]):
            counts['nodes_kept_with_attributes'] += 1
            continue
        pairs = pairs_at(node)
        if pairs is None:
            continue
        if any(a in frozen or b in frozen for a, b in pairs):
            counts['nodes_kept_turn_restriction'] += 1
            continue
        if any(not compatible(links[a], links[b]) for a, b in pairs):
            counts['nodes_kept_links_differ'] += 1
            continue
        if any(float(links[a]['fields']['length']) + float(links[b]['fields']['length']) > max_length_m
               for a, b in pairs):
            counts['nodes_kept_length_cap'] += 1
            continue
        for a, b in pairs:
            la, lb = links[a], links[b]
            la['fields']['length'] = repr(float(la['fields']['length']) + float(lb['fields']['length']))
            la['fields']['to'] = lb['fields']['to']
            absorbed_ids = (la['attrs'].get('merged_link_ids', ('', ''))[1].split(',') if 'merged_link_ids' in la['attrs'] else [])
            absorbed_ids += [b] + (lb['attrs']['merged_link_ids'][1].split(',') if 'merged_link_ids' in lb['attrs'] else [])
            la['attrs']['merged_link_ids'] = ('java.lang.String', ','.join(absorbed_ids))
            ways = (la['attrs'].get('merged_osm_way_ids', ('', ''))[1].split(',') if 'merged_osm_way_ids' in la['attrs'] else [])
            for src in (la, lb):
                w = src['attrs'].get('osm:way:id', ('', ''))[1]
                if w and w not in ways and w != la['attrs'].get('osm:way:id', ('', ''))[1]:
                    ways.append(w)
            if 'merged_osm_way_ids' in lb['attrs']:
                ways += [w for w in lb['attrs']['merged_osm_way_ids'][1].split(',') if w not in ways]
            if ways:
                la['attrs']['merged_osm_way_ids'] = ('java.lang.String', ','.join(ways))
            # rewire the maps: b's to-node now receives a
            tail = in_links[lb['fields']['to']]
            tail[tail.index(b)] = a
            removed_links.add(b)
            del links[b]
        removed_nodes.add(node)
        del in_links[node]
        del out_links[node]
        counts['nodes_merged'] += 1
        counts['links_merged_away'] += len(pairs)

    out = []
    for node, text in nodes.items():
        if node not in removed_nodes:
            out.append(text)
    node_text = ''.join(out)
    link_blocks = []
    for lid, link in links.items():
        link_blocks.append(render_link(link))
    nodes_start = head.index('<nodes')
    nodes_end = head.index('</nodes>')
    new_head = head[:nodes_start] + '<nodes>' + node_text + '\n\t' + head[nodes_end:]
    links_open_end = body.index('>') + 1
    links_close = body.rindex('</links>')
    new_body = body[:links_open_end] + ''.join(link_blocks) + '\n\t' + body[links_close:]
    lengths_after = [float(l['fields']['length']) for l in links.values()]
    counts.update(nodes_after=len(nodes) - len(removed_nodes), links_after=len(links),
                  median_link_m_before=round(median(lengths_before), 1),
                  median_link_m_after=round(median(lengths_after), 1),
                  km_before=round(sum(lengths_before) / 1000, 1),
                  km_after=round(sum(lengths_after) / 1000, 1))
    return new_head + new_body, dict(counts)


def median(values):
    ordered = sorted(values)
    n = len(ordered)
    if not n:
        return 0.0
    mid = n // 2
    return ordered[mid] if n % 2 else (ordered[mid - 1] + ordered[mid]) / 2


def render_link(link):
    f = link['fields']
    order = ['id', 'from', 'to', 'length', 'freespeed', 'capacity', 'permlanes', 'oneway', 'modes']
    keys = order + [k for k in f if k not in order]
    head = ' '.join('%s="%s"' % (k, f[k]) for k in keys if k in f)
    if not link['attrs']:
        return '\n\t\t<link %s />' % head
    rows = ''.join('\n\t\t\t\t<attribute name="%s" class="%s">%s</attribute>' % (n, c, t)
                   for n, (c, t) in link['attrs'].items())
    return '\n\t\t<link %s >\n\t\t\t<attributes>%s\n\t\t\t</attributes>\n\t\t</link>' % (head, rows)


def merge_file(source, destination, max_length_m):
    with gzip.open(source, 'rt', encoding='utf-8') as f:
        xml = f.read()
    merged, counts = merge_network(xml, max_length_m)
    with open(destination, 'wb') as fh:
        g = gzip.GzipFile(fileobj=fh, mode='wb', mtime=0)
        g.write(merged.encode('utf-8'))
        g.close()
    return counts


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('source')
    ap.add_argument('destination')
    ap.add_argument('--max-length', type=float, required=True,
                    help='metres; the converter\'s A.network.max_link_length_m')
    a = ap.parse_args(argv)
    counts = merge_file(a.source, a.destination, a.max_length)
    print(json.dumps(counts, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
