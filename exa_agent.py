import os
from dotenv import load_dotenv
from exa_py import Exa

load_dotenv()

exa = Exa(api_key=os.environ.get("EXA_API_KEY"))

print("Starting Exa Agent run (streaming mode)...")

events = exa.agent.runs.create(
    query="Find AI infrastructure companies hiring founding designers",
    output_schema={"type": "object"},
    stream=True,
)

for event in events:
    print(f"Event: {event.event}")

    # When the agent finishes, safely parse the dictionary payload
    if event.event == "agent_run.completed":
        print("\nFinal Output:")
        # event.data is a dict in streaming mode, so use .get() safely
        data = event.data if isinstance(event.data, dict) else getattr(event.data, "model_dump", lambda: {})()
        output = data.get("output", {})
        print(output.get("structured") if output else None)
