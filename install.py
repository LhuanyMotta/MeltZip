#!/usr/bin/env python3
import sys
import subprocess
import os
import platform

def run_command(command):
    """Executa um comando e retorna True se bem-sucedido"""
    try:
        print(f"Executando: {command}")
        result = subprocess.run(command, shell=True, check=True, 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                              text=True, timeout=120)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar: {command}")
        if e.stderr:
            print(f"Erro: {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        print(f"Tempo limite excedido para: {command}")
        return False

def check_pip():
    """Verifica se o pip está instalado"""
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("✓ Pip encontrado e funcionando.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ Pip não está instalado ou não está funcionando.")
        return False

def install_pip():
    """Tenta instalar o pip se não estiver disponível"""
    print("Tentando instalar o pip...")
    
    if platform.system() == "Windows":
        print("No Windows, o pip geralmente é instalado com o Python.")
        print("Se não estiver instalado, baixe e execute: https://bootstrap.pypa.io/get-pip.py")
        return False
    else:
        # Linux/macOS
        commands = [
            "sudo apt-get install -y python3-pip",
            "sudo yum install -y python3-pip", 
            "sudo pacman -S --noconfirm python-pip"
        ]
        
        for cmd in commands:
            if run_command(cmd):
                return True
        
        print("Não foi possível instalar o pip automaticamente.")
        print("Por favor, instale o pip manualmente e execute este script novamente.")
        return False

def install_requirements():
    """Instala os requisitos do projeto"""
    print("\nInstalando dependências do MeltZip...")
    
    requirements = [
        "pyzipper>=0.3.5",
        "PyQt5>=5.15.0", 
        "colorama>=0.4.4"
    ]
    
    success = True
    for package in requirements:
        print(f"\nInstalando {package}...")
        if not run_command(f"{sys.executable} -m pip install {package}"):
            print(f"✗ Falha ao instalar {package}")
            success = False
        else:
            print(f"✓ {package} instalado com sucesso")
    
    return success

def main():
    print("=" * 50)
    print("INSTALADOR DO MELTZIP")
    print("=" * 50)
    
    # Verificar se pip está instalado
    if not check_pip():
        if not install_pip():
            print("\n✗ Instalação interrompida: pip é necessário")
            return False
    
    # Instalar requisitos
    if install_requirements():
        print("\n" + "=" * 50)
        print("✓ INSTALAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 50)
        print("\nCOMO USAR:")
        print("Interface gráfica: python meltzip_gui.py")
        print("Linha de comando: python meltzip_cli.py arquivo.zip wordlist.txt") 
        print("Interface via CLI: python meltzip_cli.py --gui")
        print("\nArquivos de teste disponíveis:")
        print("- Arquivo_Secreto.zip (protegido com senha)")
        print("- TOP500.txt (wordlist com senhas comuns)")
        return True
    else:
        print("\n✗ Algumas dependências não puderam ser instaladas.")
        print("Tente instalar manualmente: pip install -r requirements.txt")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)