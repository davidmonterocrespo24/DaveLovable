"""
Test para search_file tool
"""

import asyncio

from search_file import file_search


async def test_search_file():
    """Test básico de búsqueda de archivos"""
    print("=== Test search_file ===\n")

    # Test 1: Buscar archivos Python
    print("Test 1: Buscar archivos .py")
    result = await file_search(".py")
    print(f"Resultado (primeros 500 caracteres):\n{result[:500]}...\n")

    # Test 2: Buscar archivos específicos
    print("Test 2: Buscar 'common'")
    result = await file_search("common")
    print(f"Resultado:\n{result}\n")

    # Test 3: Búsqueda sin resultados
    print("Test 3: Búsqueda sin resultados")
    result = await file_search("archivo_imposible_xyz123")
    print(f"Resultado:\n{result}\n")

    print("=== Tests completados ===")


if __name__ == "__main__":
    asyncio.run(test_search_file())
