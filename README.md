# Wildfire telemetry baseline

This reference implementation sizes the naive data volume from an editable sensor configuration. The default is the conceptual flight payload: one 640 × 512, 16-bit radiometric LWIR frame from a FLIR Boson 640-class core.

The repository follows a staged pipeline: **B0 → B1 → B2 → B3**. B0 is the baseline bytes per frame calculated here; B1, B2, and B3 will respectively represent the output after Stage 1 filtering, Stage 2 detection, and transmission packaging. This project deliberately does not estimate savings for those future stages.

Install the small analysis environment with `pip install -r requirements.txt`, then open `notebooks/00_baseline.ipynb` in Jupyter and run all cells. The notebook loads `configs/sensor_config.yaml`, prints every baseline calculation, runs sensitivity checks, and writes `results/baseline.json`. The RGB training dataset's variable dimensions are retained in the configuration for preprocessing context; they are intentionally excluded from flight-frame telemetry sizing.

This is the **REFERENCE** implementation. The on-board C/C++ port is a separate deliverable.
