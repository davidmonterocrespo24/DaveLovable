"""
Test para delete_file tool
"""

import asyncio

from delete_file import delete_file
from write_file import write_file


async def test_delete_file():
    """Test básico de eliminación de archivo"""
    print("=== Test delete_file ===\n")

    test_file = "test_delete.txt"

    # Crear archivo de prueba
    await write_file(test_file, "Contenido temporal")

    # Test 1: Eliminar archivo existente
    print("Test 1: Eliminar archivo existente")
    result = await delete_file(test_file)
    print(f"Resultado: {result}\n")

    # Test 2: Intentar eliminar archivo ya eliminado
    print("Test 2: Eliminar archivo inexistente")
    result = await delete_file(test_file)
    print(f"Resultado: {result}\n")

    print("=== Tests completados ===")


if __name__ == "__main__":
    asyncio.run(test_delete_file())
