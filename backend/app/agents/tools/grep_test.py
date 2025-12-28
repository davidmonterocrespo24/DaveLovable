"""
Test para grep tool
"""

import asyncio

from grep import grep_search


async def test_grep():
    """Test básico de búsqueda con grep"""
    print("=== Test grep ===\n")

    # Test 1: Buscar patrón simple
    print("Test 1: Buscar 'async def'")
    result = await grep_search("async def", include_pattern="*.py")
    print(f"Resultado (primeras 500 caracteres):\n{result[:500]}...\n")

    # Test 2: Búsqueda case-sensitive
    print("Test 2: Buscar 'Test' (case-sensitive)")
    result = await grep_search("Test", case_sensitive=True, include_pattern="*.py")
    print(f"Resultado (primeras 300 caracteres):\n{result[:300]}...\n")

    # Test 3: Patrón no encontrado
    print("Test 3: Patrón no encontrado")
    result = await grep_search("patron_imposible_xyz123456")
    print(f"Resultado:\n{result}\n")

    print("=== Tests completados ===")


if __name__ == "__main__":
    asyncio.run(test_grep())
