from __future__ import annotations

import xml.etree.ElementTree as ET

from backend.model.circuit import Circuit


def export_to_xml(circuit: Circuit, filepath: str) -> None:
    root = ET.Element("circuit")
    nodes_el = ET.SubElement(root, "nodes")
    for node in circuit.get_nodes():
        ET.SubElement(
            nodes_el,
            "node",
            {
                "id": str(node["id"]),
                "type": str(node["type"]),
                "x": str(float(node["x"])),
                "y": str(float(node["y"])),
            },
        )

    conns_el = ET.SubElement(root, "connections")
    for out_id, out_pin, in_id, in_pin in circuit.get_connections():
        ET.SubElement(
            conns_el,
            "connection",
            {
                "out_node_id": str(out_id),
                "out_pin": str(out_pin),
                "in_node_id": str(in_id),
                "in_pin": str(in_pin),
            },
        )

    tree = ET.ElementTree(root)
    tree.write(filepath, encoding="utf-8", xml_declaration=True)


def import_from_xml(filepath: str) -> Circuit:
    tree = ET.parse(filepath)
    root = tree.getroot()
    if root.tag != "circuit":
        raise ValueError("Invalid XML format: root tag must be <circuit>")

    c = Circuit()
    c.nodes = []
    c.connections = []
    c._next_node_id = 0

    nodes_el = root.find("nodes")
    if nodes_el is not None:
        for n in nodes_el.findall("node"):
            node = {
                "id": int(n.attrib["id"]),
                "type": n.attrib["type"],
                "x": float(n.attrib.get("x", "0")),
                "y": float(n.attrib.get("y", "0")),
            }
            c.add_node_with_id(node)

    conns_el = root.find("connections")
    if conns_el is not None:
        for cc in conns_el.findall("connection"):
            out_id = int(cc.attrib["out_node_id"])
            out_pin = int(cc.attrib["out_pin"])
            in_id = int(cc.attrib["in_node_id"])
            in_pin = int(cc.attrib["in_pin"])
            ok, reason = c.connect_pins(out_id, out_pin, in_id, in_pin)
            if not ok:
                raise ValueError(f"Invalid connection in XML: {reason}")

    return c
