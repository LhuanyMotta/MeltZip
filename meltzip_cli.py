#!/usr/bin/env python3
import pyzipper
import zipfile
import argparse
import time
import os
import sys
from datetime import timedelta
from colorama import init, Fore, Back, Style

init()  # Inicializa colorama

class MeltZipCLI:
    def __init__(self, zip_file, wordlist, verbose=False):
        self.zip_file = zip_file
        self.wordlist = wordlist
        self.verbose = verbose
        self.start_time = None
        self.last_update = 0
        self.total_words = 0
        self.tested = 0
        self.password_found = False
        self.encryption_type = "Desconhecido"

    def get_zip_info(self):
        """Obtém informações sobre o arquivo ZIP"""
        try:
            info = {
                'size': os.path.getsize(self.zip_file),
                'files': 0,
                'protected_files': 0
            }
            
            with zipfile.ZipFile(self.zip_file, 'r') as zf:
                info['files'] = len(zf.namelist())
                
                for file_info in zf.infolist():
                    if file_info.flag_bits & 0x1:  # Verifica se o arquivo está criptografado
                        info['protected_files'] += 1
            
            # Tenta determinar o tipo de criptografia
            try:
                with pyzipper.AESZipFile(self.zip_file) as azf:
                    self.encryption_type = 'AES'
            except:
                self.encryption_type = 'ZipCrypto'
                
            return info
        except Exception as e:
            print(f"{Fore.RED}[!] Erro ao obter informações do ZIP: {e}{Style.RESET_ALL}")
            return None

    def print_progress(self, password):
        current_time = time.time()
        if current_time - self.last_update >= 0.1:  # Atualiza a cada 100ms
            elapsed = timedelta(seconds=int(current_time - self.start_time))
            progress = (self.tested / self.total_words) * 100 if self.total_words > 0 else 0
            speed = self.tested / (current_time - self.start_time) if (current_time - self.start_time) > 0 else 0
            
            remaining = (elapsed.total_seconds() / self.tested) * (self.total_words - self.tested) if self.tested > 0 else 0
            
            sys.stdout.write(
                f"\r{Fore.YELLOW}[*] Progresso: {progress:.2f}% | "
                f"Testadas: {self.tested:,}/{self.total_words:,} | "
                f"Velocidade: {speed:,.0f} p/s | "
                f"Tempo: {elapsed} | "
                f"Restante: {timedelta(seconds=int(remaining))} | "
                f"Última: {Fore.CYAN}{password[:20]}{'...' if len(password) > 20 else ''}{Style.RESET_ALL}"
            )
            sys.stdout.flush()
            self.last_update = current_time

    def crack(self):
        try:
            self.start_time = time.time()
            
            # Exibe banner
            print(f"{Fore.GREEN}\n╔══════════════════════════════════════════════════╗")
            print(f"║{Fore.YELLOW}          MELTZIP - QUEBRADOR DE SENHAS ZIP         {Fore.GREEN}║")
            print(f"╚══════════════════════════════════════════════════╝{Style.RESET_ALL}")
            
            # Obtém informações do arquivo
            zip_info = self.get_zip_info()
            if zip_info:
                print(f"{Fore.BLUE}[*] Arquivo ZIP: {Fore.WHITE}{self.zip_file}")
                print(f"{Fore.BLUE}[*] Criptografia: {Fore.WHITE}{self.encryption_type}")
                print(f"{Fore.BLUE}[*] Tamanho: {Fore.WHITE}{zip_info['size']} bytes")
                print(f"{Fore.BLUE}[*] Arquivos: {Fore.WHITE}{zip_info['protected_files']} protegido(s) de {zip_info['files']} total")
            else:
                print(f"{Fore.RED}[!] Não foi possível obter informações do arquivo ZIP{Style.RESET_ALL}")
            
            print(f"{Fore.BLUE}[*] Wordlist: {Fore.WHITE}{self.wordlist}")
            
            # Conta o número de palavras na wordlist
            print(f"{Fore.YELLOW}[*] Contando palavras na wordlist...{Style.RESET_ALL}")
            with open(self.wordlist, 'r', encoding='utf-8', errors='ignore') as f:
                self.total_words = sum(1 for _ in f)
            
            print(f"{Fore.MAGENTA}[*] Iniciando ataque brute-force...{Style.RESET_ALL}")
            
            # Tenta primeiro com AES (mais comum em ZIPs modernos)
            try:
                with pyzipper.AESZipFile(self.zip_file) as zf:
                    return self.crack_zip(zf)
            except:
                # Se falhar, tenta com ZipCrypto tradicional
                with zipfile.ZipFile(self.zip_file, 'r') as zf:
                    return self.crack_zip(zf)
                    
        except FileNotFoundError as e:
            print(f"\n{Fore.RED}[!] Arquivo não encontrado: {e}{Style.RESET_ALL}")
            return None
        except Exception as e:
            print(f"\n{Fore.RED}[!] Erro inesperado: {e}{Style.RESET_ALL}")
            return None

    def crack_zip(self, zf):
        """Método genérico para quebrar senhas em ambos os tipos de ZIP"""
        with open(self.wordlist, 'r', encoding='utf-8', errors='ignore') as f:
            for password in f:
                password = password.strip()
                self.tested += 1
                
                try:
                    # Tenta extrair o primeiro arquivo (mais eficiente)
                    file_list = zf.namelist()
                    if file_list:
                        zf.read(file_list[0], pwd=password.encode())
                    
                    self.password_found = True
                    self.print_progress(password)
                    return password
                    
                except (RuntimeError, zipfile.BadZipFile, pyzipper.BadZipFile):
                    self.print_progress(password)
                    continue
                except Exception as e:
                    if self.verbose:
                        print(f"\n{Fore.RED}[!] Erro: {e}{Style.RESET_ALL}")
                    return None
        
        return None


def main():
    parser = argparse.ArgumentParser(description='MeltZip - Quebrador de senhas ZIP avançado')
    parser.add_argument('zip_file', help='Arquivo ZIP protegido por senha')
    parser.add_argument('wordlist', help='Arquivo de wordlist contendo senhas possíveis')
    parser.add_argument('--verbose', '-v', action='store_true', help='Modo verboso')
    parser.add_argument('--gui', action='store_true', help='Executar interface gráfica')
    
    args = parser.parse_args()
    
    # Se a opção --gui for especificada, executa a interface gráfica
    if args.gui:
        try:
            from PyQt5.QtWidgets import QApplication
            app = QApplication(sys.argv)
            from meltzip_gui import MeltZipGUI
            window = MeltZipGUI()
            window.show()
            sys.exit(app.exec_())
        except ImportError:
            print(f"{Fore.RED}[!] PyQt5 não está instalado. Instale com: pip install PyQt5{Style.RESET_ALL}")
            return
    
    # Valida se os arquivos existem
    if not os.path.exists(args.zip_file):
        print(f"{Fore.RED}[!] Arquivo ZIP não encontrado: {args.zip_file}{Style.RESET_ALL}")
        return
        
    if not os.path.exists(args.wordlist):
        print(f"{Fore.RED}[!] Wordlist não encontrada: {args.wordlist}{Style.RESET_ALL}")
        return
    
    # Executa o cracking
    cracker = MeltZipCLI(args.zip_file, args.wordlist, args.verbose)
    password = cracker.crack()
    
    if cracker.password_found:
        elapsed = timedelta(seconds=int(time.time() - cracker.start_time))
        print(f"\n\n{Fore.GREEN}╔══════════════════════════════════════════════════╗")
        print(f"║{Back.GREEN}{Fore.BLACK}          SENHA ENCONTRADA COM SUCESSO!          {Style.RESET_ALL}{Fore.GREEN}║")
        print(f"╚══════════════════════════════════════════════════╝{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[+] Senha encontrada: {Fore.WHITE}{password}")
        print(f"{Fore.GREEN}[+] Tempo total: {Fore.WHITE}{elapsed}")
        print(f"{Fore.GREEN}[+] Tentativas: {Fore.WHITE}{cracker.tested:,}/{cracker.total_words:,}")
        print(f"{Fore.GREEN}[+] Velocidade média: {Fore.WHITE}{cracker.tested/(time.time() - cracker.start_time):,.0f} senhas/segundo{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}[-] Senha não encontrada na wordlist{Style.RESET_ALL}")


if __name__ == "__main__":
    main()