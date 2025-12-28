"""
Test para json_tools
"""

import asyncio
import os

from json_tools import format_json, read_json, validate_json, write_json


async def test_json_tools():
    """Test básico de herramientas JSON"""
    print("=== Test json_tools ===\n")

    test_file = "test_data.json"

    # Test 1: Escribir JSON
    print("Test 1: Escribir JSON")
    test_data = {"name": "Test", "version": "1.0", "items": [1, 2, 3]}
    result = await write_json(test_file, test_data)
    print(f"Resultado: {result}\n")

    # Test 2: Leer JSON
    print("Test 2: Leer JSON")
    result = await read_json(test_file)
    print(f"Resultado: {result}\n")

    # Test 3: Validar JSON
    print("Test 3: Validar JSON")
    result = await validate_json(test_file)
    print(f"Resultado: {result}\n")

    # Test 4: Formatear JSON
    print("Test 4: Formatear JSON")
    result = await format_json(test_file, indent=4)
    print(f"Resultado: {result}\n")

    # Cleanup
    try:
        os.remove(test_file)
    except:
        pass

    print("=== Tests completados ===")


if __name__ == "__main__":
    asyncio.run(test_json_tools())
