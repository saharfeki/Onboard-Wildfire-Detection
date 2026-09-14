"""Unit tests for the raw full-frame B0 calculation."""

import unittest

from src.baseline import compute_baseline


class ComputeBaselineTests(unittest.TestCase):
    def test_lwir_640_raw_frame_matches_sensor_spec(self) -> None:
        """640 x 512 pixels x 16 bits / 8 = 655,360 bytes."""
        result = compute_baseline(
            {
                "frame_width_px": 640,
                "frame_height_px": 512,
                "bands": [{"name": "LWIR", "bit_depth": 16}],
                "compression_ratio": 1,
                "metadata_bytes_per_frame": 0,
                "frames_per_day": 1,
            }
        )

        self.assertEqual(result["pixels_per_frame"], 327_680)
        self.assertEqual(result["bits_per_pixel_total"], 16)
        self.assertEqual(result["bits_per_frame"], 5_242_880)
        self.assertEqual(result["bytes_per_frame_raw"], 655_360)
        self.assertEqual(result["bytes_per_frame_total"], 655_360)

    def test_band_bit_depths_are_summed_and_partial_byte_is_rounded_up(self) -> None:
        result = compute_baseline(
            {
                "frame_width_px": 2,
                "frame_height_px": 3,
                "bands": [{"bit_depth": 10}, {"bit_depth": 12}],
                "compression_ratio": 1,
                "metadata_bytes_per_frame": 0,
                "frames_per_day": 1,
            }
        )

        # 2 x 3 x (10 + 12) = 132 bits, which requires 17 whole bytes.
        self.assertEqual(result["bytes_per_frame_raw"], 17)


if __name__ == "__main__":
    unittest.main()
