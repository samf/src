#! /usr/bin/env python3

pressure_node = "HKCorrelationTypeIdentifierBloodPressure"
sys_child = "HKQuantityTypeIdentifierBloodPressureSystolic"
dia_child = "HKQuantityTypeIdentifierBloodPressureDiastolic"

import csv
import types
import xml.etree.ElementTree as ET


def handle_pressure(node):
    bp = types.SimpleNamespace(date="unknown")
    for child in node:
        if "type" in child.attrib and child.attrib["type"] == sys_child:
            bp.systolic = child.attrib["value"]
            if "endDate" in child.attrib:
                bp.date = child.attrib["endDate"]
            else:
                print("no end date", child.attrib)
        if "type" in child.attrib and child.attrib["type"] == dia_child:
            bp.diastolic = child.attrib["value"]
            if "endDate" in child.attrib:
                bp.date = child.attrib["endDate"]
            else:
                print("no end date", child.attrib)
    return bp


def get_pressures(node):
    pressures = []
    if "type" in node.attrib and node.attrib["type"] == pressure_node:
        pressures.append(handle_pressure(node))
    for child in node:
        pressures.extend(get_pressures(child))
    return pressures


def dump_csv(pressures):
    with open("pressures.csv", "w", newline="") as csvfile:
        fieldnames = ["date", "systolic", "diastolic"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for bp in pressures:
            writer.writerow(vars(bp))


def read_it():
    tree = ET.parse("export.xml")
    root = tree.getroot()
    return root


def main():
    root = read_it()
    pressures = get_pressures(root)
    for bp in pressures:
        print("date {0.date} pressure {0.systolic} / {0.diastolic}".format(bp))
    dump_csv(pressures)


if __name__ == "__main__":
    main()
