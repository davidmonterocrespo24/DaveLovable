"""
Test para glob tool
"""

import asyncio
from glob import glob_search


async def test_glob():
    """Test básico de búsqueda con glob"""
    print("=== Test glob ===\n")

    # Test 1: Buscar todos los archivos Python
    print("Test 1: Buscar **/*.py")
    result = await glob_search("**/*.py", dir_path="src/tools")
    print(f"Resultado (primeros 800 caracteres):\n{result[:800]}...\n")

    # Test 2: Buscar archivos específicos
    print("Test 2: Buscar *.py en directorio actual de tools")
    result = await glob_search("*.py", dir_path="src/tools")
    print(f"Resultado:\n{result[:500]}...\n")

    # Test 3: Patrón sin resultados
    print("Test 3: Patrón sin resultados")
    result = await glob_search("*.xyz123")
    print(f"Resultado:\n{result}\n")

    print("=== Tests completados ===")


if __name__ == "__main__":
    asyncio.run(test_glob())
