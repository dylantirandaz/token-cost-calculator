"""session tracking and history persistence."""

import csv
import io
import json
import os
from datetime import datetime

from .models import MODELS, calc_cost_simple

HISTORY_FILE = os.path.expanduser("~/.tokencalc_history.json")


class Session:
    def __init__(self, model: str = "sonnet-4"):
        self.model = model
        self.entries: list[dict] = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0

    def add(self, input_tokens: int, output_tokens: int, label: str = ""):
        cost, input_cost, output_cost = calc_cost_simple(input_tokens, output_tokens, self.model)

        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost += cost

        self.entries.append({
            "label": label,
            "model": self.model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost,
            "timestamp": datetime.now().isoformat(),
        })
        return cost, input_cost, output_cost

    def save(self):
        history = load_history()
        history.append({
            "session_start": self.entries[0]["timestamp"] if self.entries else datetime.now().isoformat(),
            "model": self.model,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost": self.total_cost,
            "entries": self.entries,
        })
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)

    def to_csv(self) -> str:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["timestamp", "model", "label", "input_tokens", "output_tokens", "cost"])
        for e in self.entries:
            writer.writerow([
                e["timestamp"], MODELS[e["model"]]["name"], e["label"],
                e["input_tokens"], e["output_tokens"], f"{e['cost']:.6f}",
            ])
        return buf.getvalue()


def load_history() -> list[dict]:
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def clear_history():
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
