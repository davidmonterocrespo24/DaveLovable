"""
Test para edit_file tool
"""

import asyncio
import os

from edit_file import edit_file
from write_file import write_file


async def test_edit_file():
    """Test básico de edición de archivo"""
    print("=== Test edit_file ===\n")

    test_file = "test_edit.py"

    # Crear archivo de prueba
    initial_content = """def hello():
    print("Hello World")
    return True
"""
    await write_file(test_file, initial_content)

    # Test 1: Edición exacta
    print("Test 1: Edición exacta")
    result = await edit_file(test_file, old_string='print("Hello World")', new_string='print("Hello Universe")')
    print(f"Resultado: {result}\n")

    # Test 2: Edición con cambio de indentación (flexible)
    print("Test 2: Edición flexible (ignora espacios)")
    result = await edit_file(
        test_file,
        old_string='def hello():\n    print("Hello Universe")',
        new_string='def hello():\n    print("Goodbye World")',
    )
    print(f"Resultado: {result}\n")

    # Test 3: String no encontrado
    print("Test 3: String no encontrado")
    result = await edit_file(test_file, old_string="este texto no existe", new_string="nuevo texto")
    print(f"Resultado: {result}\n")

    # Cleanup
    try:
        os.remove(test_file)
    except:
        pass

    print("=== Tests completados ===")


if __name__ == "__main__":
    asyncio.run(test_edit_file())
