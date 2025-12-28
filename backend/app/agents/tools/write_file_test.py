"""
Test para write_file tool
"""

import asyncio
import os

from write_file import write_file


async def test_write_file():
    """Test básico de escritura de archivo"""
    print("=== Test write_file ===\n")

    test_file = "test_output.txt"

    # Test 1: Escribir archivo nuevo
    print("Test 1: Escribir archivo nuevo")
    content = "Este es un archivo de prueba.\nLínea 2\nLínea 3"
    result = await write_file(test_file, content)
    print(f"Resultado: {result}\n")

    # Test 2: Sobrescribir archivo existente
    print("Test 2: Sobrescribir archivo")
    new_content = "Contenido actualizado"
    result = await write_file(test_file, new_content)
    print(f"Resultado: {result}\n")

    # Test 3: Escribir código Python válido
    print("Test 3: Escribir código Python válido")
    python_code = """def hello():
    print("Hello World")
    return True
"""
    result = await write_file("test_code.py", python_code)
    print(f"Resultado: {result}\n")

    # Test 4: Intentar escribir código Python inválido
    print("Test 4: Código Python inválido (debe fallar)")
    invalid_code = """def broken(
    print("Missing closing parenthesis"
"""
    result = await write_file("test_invalid.py", invalid_code)
    print(f"Resultado: {result}\n")

    # Cleanup
    try:
        os.remove(test_file)
        os.remove("test_code.py")
    except:
        pass

    print("=== Tests completados ===")


if __name__ == "__main__":
    asyncio.run(test_write_file())
