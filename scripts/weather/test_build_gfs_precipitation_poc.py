from __future__ import annotations

import unittest

import build_gfs_precipitation_poc as builder


def record(start: int, end: int, offset: int = 0) -> builder.InventoryRecord:
    return builder.InventoryRecord(
        offset=offset,
        end_offset=offset + 99,
        description=f"APCP surface {start}-{end} hour acc fcst",
        start_step=start,
        end_step=end,
    )


class InventoryPlanningTests(unittest.TestCase):
    def test_inventory_parser_keeps_every_apcp_interval(self) -> None:
        inventory = "\n".join(
            [
                "1:0:d=2026083012:APCP:surface:6-8 hour acc fcst:",
                "2:100:d=2026083012:APCP:surface:0-8 hour acc fcst:",
                "3:200:d=2026083012:TMP:2 m above ground:8 hour fcst:",
            ]
        )

        records = builder.parse_inventory(inventory)

        self.assertEqual([(item.start_step, item.end_step) for item in records], [(6, 8), (0, 8)])
        self.assertEqual([(item.offset, item.end_offset) for item in records], [(0, 99), (100, 199)])

    def test_planner_uses_shortest_valid_six_hour_bucket(self) -> None:
        inventories = {
            hour: [record(0, hour)] for hour in range(1, 7)
        }
        inventories[7] = [record(6, 7), record(0, 7)]
        inventories[8] = [record(6, 8), record(0, 8)]

        plan = builder.plan_timesteps(inventories, list(range(1, 9)))

        self.assertEqual(
            [step.derivation_start_step for step in plan],
            [0, 0, 0, 0, 0, 0, 6, 6],
        )

    def test_planner_rejects_an_interval_without_a_prior_baseline(self) -> None:
        inventories = {
            1: [record(0, 1)],
            2: [record(1, 3)],
        }

        with self.assertRaisesRegex(ValueError, "honest one-hour interval"):
            builder.plan_timesteps(inventories, [1, 2])


if __name__ == "__main__":
    unittest.main()
