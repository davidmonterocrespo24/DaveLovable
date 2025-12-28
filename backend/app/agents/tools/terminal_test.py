"""
Test para terminal tool
"""

import asyncio

from terminal import run_terminal_cmd


async def test_terminal():
    """Test básico de ejecución de comandos"""
    print("=== Test terminal ===\n")

    # Test 1: Comando simple (echo)
    print("Test 1: Comando echo")
    result = await run_terminal_cmd("echo Hello World")
    print(f"Resultado:\n{result}\n")

    # Test 2: Listar archivos (PowerShell)
    print("Test 2: Listar archivos con ls")
    result = await run_terminal_cmd("ls src/tools/*.py | Select-Object -First 5")
    print(f"Resultado:\n{result[:300]}...\n")

    # Test 3: Comando peligroso (debe pedir aprobación)
    print("Test 3: Comando peligroso (debe pedir aprobación)")
    result = await run_terminal_cmd("rm test.txt")
    print(f"Resultado:\n{result}\n")

    print("=== Tests completados ===")


if __name__ == "__main__":
    asyncio.run(test_terminal())
