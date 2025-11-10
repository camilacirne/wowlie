"""
Compila o contrato SimpleMemecoin.sol usando py-solc-x
"""
import json
from solcx import compile_standard, install_solc

def compile_memecoin():
    """Compila o contrato e retorna ABI e bytecode"""
    
    # Instala Solidity compiler
    print("📦 Instalando Solidity 0.8.20...")
    try:
        install_solc('0.8.20')
    except:
        print("⚠️  Solc 0.8.20 já instalado")
    
    # Lê o arquivo do contrato
    print("📖 Lendo contrato...")
    with open('contracts/SimpleMemecoin.sol', 'r') as file:
        contract_source_code = file.read()
    
    # Compila
    print("🔨 Compilando...")
    compiled_sol = compile_standard(
        {
            "language": "Solidity",
            "sources": {
                "SimpleMemecoin.sol": {
                    "content": contract_source_code
                }
            },
            "settings": {
                "outputSelection": {
                    "*": {
                        "*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]
                    }
                }
            }
        },
        solc_version="0.8.20"
    )
    
    # Extrai ABI e bytecode
    contract_data = compiled_sol["contracts"]["SimpleMemecoin.sol"]["SimpleMemecoin"]
    
    abi = contract_data["abi"]
    bytecode = contract_data["evm"]["bytecode"]["object"]
    
    print("✅ Compilação concluída!")
    print(f"   📏 Bytecode: {len(bytecode)} chars")
    print(f"   📋 ABI: {len(abi)} funções/eventos")
    
    # Salva em arquivo Python
    print("\n💾 Salvando em wallet/memecoin.py...")
    
    # Converte ABI para formato Python (com aspas simples e booleanos corretos)
    abi_str = json.dumps(abi, indent=4)
    abi_str = abi_str.replace('false', 'False').replace('true', 'True').replace('null', 'None')
    
    python_code = '''"""
Contrato SimpleMemecoin compilado
Gerado automaticamente por compile_memecoin.py
"""

MEMECOIN_ABI = ''' + abi_str + '''

MEMECOIN_BYTECODE = "''' + bytecode + '''"

def get_contract_info():
    """Retorna informacoes do contrato"""
    return {
        'abi': MEMECOIN_ABI,
        'bytecode': MEMECOIN_BYTECODE
    }

# Funcao de compatibilidade para codigo antigo
def get_memecoin_contract():
    """Funcao de compatibilidade - retorna informacoes do contrato"""
    return get_contract_info()
'''
    
    with open('wallet/memecoin.py', 'w', encoding='utf-8') as f:
        f.write(python_code)
    
    print("✅ Arquivo atualizado!")
    print("\n🎉 Pronto para usar!")
    
    return abi, bytecode

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 COMPILADOR DE MEMECOIN")
    print("=" * 70)
    print()
    
    try:
        abi, bytecode = compile_memecoin()
        
        print("\n" + "=" * 70)
        print("✅ SUCESSO!")
        print("=" * 70)
        print("\nAgora você pode criar memecoins com o novo contrato!")
        print("Execute: streamlit run streamlit_app.py")
        
    except Exception as e:
        print(f"\n❌ Erro ao compilar: {e}")
        print("\n💡 Certifique-se de ter py-solc-x instalado:")
        print("   pip install py-solc-x")
