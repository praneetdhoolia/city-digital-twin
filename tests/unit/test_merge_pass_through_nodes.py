"""The pass-through merge keeps every metre, mode and junction (9.207).

A chain A-B-C-D of identical one-way links merges to one link A-D of the
summed length; a two-way street merges both directions; a junction, a link
whose values differ, a turn restriction and the length cap all hold their
node. The measurement the record cites was made by this code on the second
city's base network; nothing wires it into a build.
"""
import gzip
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from build import merge_pass_through_nodes as mp  # noqa: E402


def link(lid, a, b, length, modes='car', cap='600.0', attrs=None, extra=''):
    rows = ''.join('\n\t\t\t\t<attribute name="%s" class="java.lang.String">%s</attribute>' % kv
                   for kv in (attrs or [('osm:way:highway', 'residential'), ('osm:way:id', lid)]))
    return ('\n\t\t<link id="%s" from="%s" to="%s" length="%s" freespeed="8.3" capacity="%s" '
            'permlanes="1.0" oneway="1" modes="%s" >\n\t\t\t<attributes>%s%s\n\t\t\t</attributes>\n\t\t</link>'
            % (lid, a, b, length, cap, modes, rows, extra))


def network(nodes, links):
    head = ('<?xml version="1.0" encoding="UTF-8"?>\n<network>\n\t<nodes>'
            + ''.join('\n\t\t<node id="%s" x="%d" y="0" >\n\t\t</node>' % (n, i * 10) for i, n in enumerate(nodes))
            + '\n\t</nodes>\n\t<links capperiod="01:00:00">')
    return head + ''.join(links) + '\n\t</links>\n</network>\n'


def parsed(xml):
    links = mp.parse_links(xml[xml.index('<links'):])
    nodes = [m.group(1) for m in mp.NODE_RE.finditer(xml[:xml.index('<links')])]
    return nodes, links


def test_a_chain_of_identical_links_becomes_one_link_of_the_summed_length():
    xml = network('ABCD', [link('1', 'A', 'B', 30.0), link('2', 'B', 'C', 40.0), link('3', 'C', 'D', 50.0)])
    out, counts = mp.merge_network(xml, 500)
    nodes, links = parsed(out)
    assert nodes == ['A', 'D'] and list(links) == ['1']
    assert links['1']['fields']['to'] == 'D' and float(links['1']['fields']['length']) == 120.0
    assert links['1']['attrs']['merged_link_ids'][1] == '2,3'
    assert links['1']['attrs']['merged_osm_way_ids'][1] == '2,3'
    assert counts['nodes_merged'] == 2 and counts['km_before'] == counts['km_after']


def test_a_two_way_street_merges_both_directions_and_a_junction_holds():
    xml = network('ABCX', [link('1', 'A', 'B', 30.0), link('2', 'B', 'A', 30.0),
                           link('3', 'B', 'C', 40.0), link('4', 'C', 'B', 40.0),
                           link('5', 'X', 'C', 10.0)])
    out, counts = mp.merge_network(xml, 500)
    nodes, links = parsed(out)
    assert 'B' not in nodes and 'C' in nodes           # C is a junction: three links meet
    assert links['1']['fields']['to'] == 'C' and links['4']['fields']['to'] == 'A'
    assert float(links['1']['fields']['length']) == 70.0 == float(links['4']['fields']['length'])
    assert counts['nodes_merged'] == 1


def test_differing_values_turn_restrictions_and_the_cap_hold_their_nodes():
    restriction = ('\n\t\t\t\t<attribute name="disallowedNextLinks" '
                   'class="org.matsim.core.network.turnRestrictions.DisallowedNextLinks">'
                   '{"car":[["8"]]}</attribute>')
    xml = network('ABCDEFG', [
        link('1', 'A', 'B', 30.0), link('2', 'B', 'C', 40.0, cap='1200.0'),     # capacity differs at B
        link('3', 'C', 'D', 300.0, cap='1200.0'), link('4', 'D', 'E', 300.0, cap='1200.0'),  # C merges 2+3 (340 m); 640 m > the cap at D
        link('5', 'E', 'F', 10.0, extra=restriction), link('8', 'F', 'G', 10.0)])  # restriction on 5 names 8: E and F hold
    out, counts = mp.merge_network(xml, 500)
    nodes, links = parsed(out)
    assert nodes == list('ABDEFG') and len(links) == 5
    assert float(links['2']['fields']['length']) == 340.0
    assert counts['nodes_kept_links_differ'] == 1
    assert counts['nodes_kept_length_cap'] == 1
    assert counts['nodes_kept_turn_restriction'] == 2


def test_merge_file_round_trips_a_gzip_and_reports(tmp_path):
    src = tmp_path / 'in.xml.gz'
    dst = tmp_path / 'out.xml.gz'
    with gzip.open(src, 'wt', encoding='utf-8') as f:
        f.write(network('ABC', [link('1', 'A', 'B', 30.0), link('2', 'B', 'C', 40.0)]))
    counts = mp.merge_file(str(src), str(dst), 500)
    assert counts['links_after'] == 1 and counts['nodes_after'] == 2
    with gzip.open(dst, 'rt', encoding='utf-8') as f:
        assert '<link id="1" from="A" to="C" length="70.0"' in f.read()
    assert json.dumps(counts)
