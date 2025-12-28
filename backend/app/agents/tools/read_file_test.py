"""
Test para read_file tool
"""

import asyncio

from read_file import read_file


async def test_read_file():
    """Test básico de lectura de archivo"""
    print("=== Test read_file ===\n")

    # Test 1: Leer archivo completo
    print("Test 1: Leer archivo completo")
    result = await read_file("src/tools/common.py")
    print(f"Resultado: {result[:200]}...\n")

    # Test 2: Leer rango específico de líneas
    print("Test 2: Leer líneas 1-3")
    result = await read_file(
        "src/tools/common.py",
        should_read_entire_file=False,
        start_line_one_indexed=1,
        end_line_one_indexed_inclusive=3,
    )
    print(f"Resultado:\n{result}\n")

    # Test 3: Archivo inexistente
    print("Test 3: Archivo inexistente")
    result = await read_file("archivo_que_no_existe.py")
    print(f"Resultado: {result}\n")

    print("=== Tests completados ===")


if __name__ == "__main__":
    asyncio.run(test_read_file())
