"""
Test para directory_ops tool
"""

import asyncio

from directory_ops import list_dir


async def test_directory_ops():
    """Test básico de listado de directorios"""
    print("=== Test directory_ops ===\n")

    # Test 1: Listar directorio actual
    print("Test 1: Listar directorio de tools")
    result = await list_dir("src/tools")
    print(f"Resultado:\n{result[:500]}...\n")

    # Test 2: Listar directorio raíz
    print("Test 2: Listar directorio raíz")
    result = await list_dir(".")
    print(f"Resultado (primeras 500 caracteres):\n{result[:500]}...\n")

    # Test 3: Directorio inexistente
    print("Test 3: Directorio inexistente")
    result = await list_dir("directorio_que_no_existe")
    print(f"Resultado: {result}\n")

    print("=== Tests completados ===")


if __name__ == "__main__":
    asyncio.run(test_directory_ops())
