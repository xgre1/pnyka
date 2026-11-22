#!/usr/bin/env python3
"""Plain-assert tests. Run: python3 -I engine/compare/test_compare.py"""
import csv
import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_compare as bc  # noqa: E402


def read(path):
    with open(path, "rb") as f:
        return f.read()


def main():
    t1 = tempfile.mkdtemp(prefix="cmp1_")
    t2 = tempfile.mkdtemp(prefix="cmp2_")
    doc = bc.write_all(t1)
    bc.write_all(t2)
    doc = json.loads(read(os.path.join(t1, "actual_vs_need.json")).decode("utf-8"))

    # deterministic rerun, byte-identical
    for fn in ("actual_vs_need.json", "actual_vs_need.csv", "SUMMARY.md"):
        assert read(os.path.join(t1, fn)) == read(os.path.join(t2, fn)), fn
    print("ok deterministic rerun byte-identical")

    # reproduction of the published figures
    rc = doc["meta"]["reproduction_check"]
    assert rc["trees_inside_neighbourhoods"] == 14232, rc
    assert rc["trees_total_register"] == 14255
    assert abs(rc["bare_share_pct_all"] - 17.0) <= 0.1
    assert abs(rc["bare_share_pct_2024"] - 22.8) <= 0.1
    assert abs(rc["bare_share_pct_2025"] - 9.4) <= 0.1
    assert abs(rc["bare_share_pct_2026"] - 19.1) <= 0.1
    assert abs(rc["bare_share_pct_all_without_2216_2218"] - 18.6) <= 0.1
    print("ok reproduces 14,232 and 17.0 / 22.8 / 9.4 / 19.1 / 18.6")

    # packages
    nb, pts, sites, pk, multi = bc.load_all()
    qty = {r["neighbourhood"]: int(float(r["quantity_central"])) for r in pk}
    assert len(qty) == len(pk)

    sc_all = doc["scenarios"]
    assert list(sc_all) == ["2024", "2025", "2026", "all"]
    for key, sc in sc_all.items():
        N = sc["n_trees"]
        for side in ("actual", "need", "need_least_cover_first"):
            by = sc[side]["by_neighbourhood"]
            assert len(by) == 144
            assert sum(by.values()) == N, (key, side)
            assert sc[side]["n_trees"] == N
        # need side never exceeds a package quantity and gives nothing outside packages
        for side in ("need", "need_least_cover_first"):
            for n, v in sc[side]["by_neighbourhood"].items():
                assert v <= qty.get(n, 0), (key, side, n)
            assert sc[side]["cost_central_eur"] > 0
        # need side: all full packages except the last, in rank order
        order = [r["neighbourhood"] for r in pk]
        got = [n for n in order if sc["need"]["by_neighbourhood"][n] > 0]
        assert got == order[:len(got)]
        for n in got[:-1]:
            assert sc["need"]["by_neighbourhood"][n] == qty[n]
        # actual-side counts equal an independent recount from the points
        recount = {}
        for q in pts:
            if q["nb"] and (key == "all" or q["year"] == key):
                recount[q["nb"]] = recount.get(q["nb"], 0) + q["trees"]
        assert {n: v for n, v in sc["actual"]["by_neighbourhood"].items() if v} == recount
        assert sc["actual"]["n_trees"] == sum(recount.values())
    # 2001 trees: out of yearly figures, in the total
    yearly = sum(sc_all[y]["n_trees"] for y in ("2024", "2025", "2026"))
    assert sc_all["all"]["n_trees"] - yearly == 4
    # need side leaves the capacity ceiling visible
    assert sc_all["all"]["n_trees"] <= doc["meta"]["capacity_trees_pavement_central_total"]
    # cost pro-rating: all-N cost is below the cost of all packages used in full
    print("ok totals, by_neighbourhood sums, package ceilings, 2001 handling")

    # point in polygon sanity: hole and ray casting
    sq = [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]
    hole = [[4, 4], [6, 4], [6, 6], [4, 6], [4, 4]]
    assert bc.polygon_contains([sq, hole], 1, 1)
    assert not bc.polygon_contains([sq, hole], 5, 5)
    assert not bc.polygon_contains([sq, hole], 11, 5)
    print("ok ray casting with hole")

    # Greek text rules
    md = read(os.path.join(t1, "SUMMARY.md")).decode("utf-8")
    greek = md.split("## Sentences in Greek")[1]
    assert "·" not in greek
    assert not re.search(r"[A-Za-z]", greek.split("The Greek sentences")[0]), "latin letters in Greek block"
    print("ok Greek block has no Latin letters and no middle dot")
    print("ALL TESTS PASSED")


if __name__ == "__main__":
    main()
