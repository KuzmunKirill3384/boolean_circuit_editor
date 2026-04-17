import xml.etree.ElementTree as ET
from frontend.core.circuit import Circuit

def export_to_xml(circuit: Circuit, filepath: str):
    """
    Сохраняет Circuit в XML файл.
    Структура XML:
    <circuit>
        <nodes>
            <node id="..." type="..." x="..." y="..." />
            ...
        </nodes>
        <connections>
            <connection from="node_id" to="node_id" />
            ...
        </connections>
    </circuit>
    """
    root = ET.Element("circuit")

    nodes_elem = ET.SubElement(root, "nodes")
    for node in circuit.nodes:
        node_elem = ET.SubElement(
            nodes_elem,
            "node",
            id=str(node["id"]),
            type=node["type"],
            x=str(node["x"]),
            y=str(node["y"])
        )

    connections_elem = ET.SubElement(root, "connections")
    for out_id, out_pin, in_id, in_pin in circuit.connections:
        ET.SubElement(
            connections_elem,
            "connection",
            from_node=str(out_id),
            from_pin=str(out_pin),
            to_node=str(in_id),
            to_pin=str(in_pin)
        )

    tree = ET.ElementTree(root)
    tree.write(filepath, encoding="utf-8", xml_declaration=True)
    print(f"Схема сохранена в {filepath}")


def import_from_xml(filepath: str) -> Circuit:
    """
    Загружает Circuit из XML файла и возвращает новый объект Circuit.
    """
    tree = ET.parse(filepath)
    root = tree.getroot()

    circuit = Circuit()

    for node_elem in root.find("nodes"):
        node = {
            "id": int(node_elem.attrib["id"]),
            "type": node_elem.attrib["type"],
            "x": float(node_elem.attrib["x"]),
            "y": float(node_elem.attrib["y"])
        }
        circuit.nodes.append(node)

    for conn_elem in root.find("connections"):
        out_id = int(conn_elem.attrib["from_node"])
        out_pin = int(conn_elem.attrib.get("from_pin", 0))
        in_id = int(conn_elem.attrib["to_node"])
        in_pin = int(conn_elem.attrib.get("to_pin", 0))
        circuit.connections.append((out_id, out_pin, in_id, in_pin))

    print(f"Схема загружена из {filepath}")
    return circuit