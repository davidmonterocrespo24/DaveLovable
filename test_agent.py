import asyncio
import sys
import os
sys.path.insert(0, 'backend')

# Load environment variables
from dotenv import load_dotenv
load_dotenv('backend/.env')

from backend.app.agents.orchestrator import get_orchestrator

async def test():
    orch = get_orchestrator()
    result = await orch.generate_code(
        'Create a simple Button component in React with TypeScript using Tailwind CSS'
    )
    # Save to file to avoid encoding issues
    with open('agent_response.txt', 'w', encoding='utf-8') as f:
        f.write('=== Response Text ===\n')
        f.write(result.get('response_text', 'No response'))
        f.write('\n\n=== Code Blocks Found ===\n')
        f.write(f'Count: {len(result.get("code", []))}\n')
        for i, code in enumerate(result.get('code', [])):
            f.write(f'\n Block {i+1}:\n')
            f.write(f'  Filename: {code.get("filename")}\n')
            f.write(f'  Language: {code.get("language")}\n')
            f.write(f'  Content length: {len(code.get("content", ""))} chars\n')

    print(f'Response saved to agent_response.txt')
    print(f'Code blocks found: {len(result.get("code", []))}')

asyncio.run(test())
