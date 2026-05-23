# pycrashtest/loader.py
import json
from pathlib import Path


class NHTSALoader:
    """
    Reads NHTSA test folder metadata.
    """

    def __init__(self, folder_path: str):
        self.folder = Path(folder_path)
        self.test_no = None
        self.channels = {}      # CURNO (int) → metadata dict
        self._load_metadata()

    def _load_metadata(self):
        json_files = list(self.folder.glob("*.json"))
        if not json_files:
            raise FileNotFoundError("No JSON metadata file in folder.")

        with open(json_files[0], "r") as f:
            meta = json.load(f)

        # Support both a direct metadata object and the API-wrapped
        # format that uses { ..., "results": [ { ... } ] }.
        root = meta
        if isinstance(meta, dict) and "results" in meta and isinstance(meta["results"], list) and meta["results"]:
            root = meta["results"][0]

        # Try several locations for the test number.
        self.test_no = root.get("TSTNO") or (root.get("TEST") or {}).get("TSTNO")

        for ch in root.get("INSTRUMENTATION", []):
            curno = ch["CURNO"]
            self.channels[curno] = {
                "curno":       curno,
                "location":    ch.get("SENLOCD", ""),   # e.g. LEFT FRONT SEAT
                "attached":    ch.get("SENATTD", ""),   # e.g. HEAD CG
                "axis":        ch.get("AXISD", ""),     # e.g. X - LOCAL
                "sensor":      ch.get("SENTYPD", ""),   # e.g. ACCELEROMETER
                "desc":        ch.get("INSCOM", ""),    # e.g. DRIVER HEAD X
                "x_unit":      ch.get("XUNITSD", ""),  # e.g. SECONDS
                "y_unit":      ch.get("YUNITSD", ""),  # e.g. G'S
                "sample_rate": ch.get("INSRAT", 2000.0),
                "tsv_path":    self.folder / f"*tsv.{curno:03d}",
            }

    def find_channels(self, keyword: str) -> list[dict]:
        """
        Search channels by keyword in desc or attached field.
        Returns list of metadata dicts.

        Examples:
            loader.find_channels("HEAD")
            loader.find_channels("NECK")
            loader.find_channels("CHEST")
            loader.find_channels("TIBIA")
        """
        keyword = keyword.upper()
        return [
            ch for ch in self.channels.values()
            if keyword in ch["desc"].upper()
            or keyword in ch["attached"].upper()
        ]

    def get_tsv_path(self, curno: int) -> str:
        """Resolve actual TSV file path for a given CURNO."""
        matches = list(self.folder.glob(f"*tsv.{curno:03d}"))
        if not matches:
            raise FileNotFoundError(f"No TSV file found for CURNO {curno}")
        return str(matches[0])

    def summary(self) -> None:
        """Print all channels — useful for exploring a new test."""
        print(f"Test No: {self.test_no}")
        print(f"{'CURNO':<8} {'DESC':<30} {'SENSOR':<20} {'UNIT':<10} {'FS (Hz)'}")
        print("-" * 80)
        for curno, ch in sorted(self.channels.items()):
            print(
                f"{curno:<8} {ch['desc']:<30} {ch['sensor']:<20} "
                f"{ch['y_unit']:<10} {ch['sample_rate']}"
            )