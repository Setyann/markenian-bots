import json
import time


class EventEngine:
    def __init__(self, config_path: str):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        self.state = {
            "history": [],
            "active_flows": []
        }

    def validate_event(self, event_name: str) -> bool:
        return event_name in self.config["events"]

    def get_flow_by_event(self, event_name: str):
        for flow_name, flow in self.config["flows"].items():
            if event_name in flow:
                return flow_name
        return None

    def emit(self, event_name: str, payload=None):
        if payload is None:
            payload = {}

        if not self.validate_event(event_name):
            raise Exception(f"Unknown event: {event_name}")

        flow_name = self.get_flow_by_event(event_name)

        self.state["history"].append({
            "event": event_name,
            "payload": payload,
            "time": time.time()
        })

        print(f"[EVENT] {event_name} {payload}")

        if not flow_name:
            return

        flow_state = next(
            (f for f in self.state["active_flows"] if f["name"] == flow_name),
            None
        )

        if flow_state is None:
            flow_state = {"name": flow_name, "index": 0}
            self.state["active_flows"].append(flow_state)

        flow = self.config["flows"][flow_name]

        expected = flow[flow_state["index"]]

        if expected != event_name:
            raise Exception(
                f"Flow violation in {flow_name}: expected {expected}, got {event_name}"
            )

        flow_state["index"] += 1

        if flow_state["index"] >= len(flow):
            print(f"[FLOW COMPLETE] {flow_name}")
            self.state["active_flows"].remove(flow_state)
