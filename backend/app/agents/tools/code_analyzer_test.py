"""
Test para code_analyzer tool
"""

import asyncio

from code_analyzer import analyze_python_file, find_function_definition, list_all_functions


async def test_code_analyzer():
    """Test básico de análisis de código"""
    print("=== Test code_analyzer ===\n")

    # Test 1: Analizar archivo Python
    print("Test 1: Analizar common.py")
    result = await analyze_python_file("src/tools/common.py")
    print(f"Resultado:\n{result}\n")

    # Test 2: Listar funciones
    print("Test 2: Listar funciones en read_file.py")
    result = await list_all_functions("src/tools/read_file.py")
    print(f"Resultado:\n{result[:500]}...\n")

    # Test 3: Encontrar definición de función
    print("Test 3: Encontrar función 'get_workspace'")
    result = await find_function_definition("src/tools/common.py", "get_workspace")
    print(f"Resultado:\n{result}\n")

    # Test 4: Archivo inexistente
    print("Test 4: Archivo inexistente")
    result = await analyze_python_file("archivo_que_no_existe.py")
    print(f"Resultado: {result}\n")

    print("=== Tests completados ===")


if __name__ == "__main__":
    asyncio.run(test_code_analyzer())
