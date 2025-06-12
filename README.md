PC Builder Pro

Multi agent demo featuring three agents: triage, sales, support. Simulates a PC building firms callflow, offering assistance with purchasing or support for existing systems. 

All agents are written out in pc_builder_service.py and are accessible on port 3001 at their various routes '/' '/sales' '/support'.

Uses the search feature to create a RAG stack locally for each agents knowledgebase.

'Transferring' the call in this demo is more conceptual, it stays within the same call SID passing the reins to any configured agents. It uses the SWML 'transfer' method in a tool to switch active SWML to one of your other agents by referencing your proxyURL/agentroute.

Shared state manager that passes context from triage to the destination agent (broken)

## Setup Instructions

1. run setup.py which installs dependencies and sets up a virtual environment

2. start the script in the venv with run.bat or manually with:
venv\Scripts\activate
python pc_builder_service.py

3. Create and configure your .env using the template. Start a proxy listening on your configured port (default 3001) and set it as your SWML_PROXY_URL_BASE in the env

4. Create a SignalWire resource with your proxy URL as the script URL and assign it to a phone number or endpoint's inbound call handler. 