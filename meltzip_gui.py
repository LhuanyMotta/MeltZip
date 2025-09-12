#!/usr/bin/env python3
import sys
import pyzipper
import time
import zipfile
import os
from datetime import timedelta
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QLabel, QLineEdit, QPushButton, QFileDialog,
                            QProgressBar, QMessageBox, QTextEdit, QHBoxLayout,
                            QGroupBox, QGridLayout, QFrame, QSizePolicy)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QUrl
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon, QDesktopServices

class ZipCrackerThread(QThread):
    update_signal = pyqtSignal(str, int, int, float)
    result_signal = pyqtSignal(str, bool)
    info_signal = pyqtSignal(dict)

    def __init__(self, zip_file, wordlist):
        super().__init__()
        self.zip_file = zip_file
        self.wordlist = wordlist
        self.running = True
        self.start_time = None

    def get_zip_info(self):
        """Obtém informações sobre o arquivo ZIP"""
        info = {
            'encryption': 'Desconhecido',
            'size': 0,
            'files': 0,
            'protected_files': 0
        }
        
        try:
            info['size'] = os.path.getsize(self.zip_file)
            
            with zipfile.ZipFile(self.zip_file, 'r') as zf:
                info['files'] = len(zf.namelist())
                
                for file_info in zf.infolist():
                    if file_info.flag_bits & 0x1:  # Verifica se o arquivo está criptografado
                        info['protected_files'] += 1
                
                # Tenta determinar o tipo de criptografia
                try:
                    with pyzipper.AESZipFile(self.zip_file) as azf:
                        info['encryption'] = 'AES'
                except:
                    info['encryption'] = 'ZipCrypto'
                        
        except Exception as e:
            print(f"Erro ao obter informações do ZIP: {e}")
            
        return info

    def run(self):
        try:
            # Obtém informações do arquivo ZIP
            zip_info = self.get_zip_info()
            self.info_signal.emit(zip_info)
            
            self.start_time = time.time()
            
            # Tenta primeiro com AES (mais comum em ZIPs modernos)
            try:
                with pyzipper.AESZipFile(self.zip_file) as zf:
                    self.crack_zip(zf)
            except:
                # Se falhar, tenta com ZipCrypto tradicional
                with zipfile.ZipFile(self.zip_file, 'r') as zf:
                    self.crack_zip(zf)
                    
        except Exception as e:
            self.result_signal.emit(f"Erro: {e}", False)

    def crack_zip(self, zf):
        """Método genérico para quebrar senhas em ambos os tipos de ZIP"""
        with open(self.wordlist, 'r', encoding='utf-8', errors='ignore') as f:
            total_words = sum(1 for _ in f)
            f.seek(0)
            
            for i, word in enumerate(f, 1):
                if not self.running:
                    return
                
                password = word.strip()
                try:
                    # Tenta extrair o primeiro arquivo (mais eficiente)
                    file_list = zf.namelist()
                    if file_list:
                        zf.read(file_list[0], pwd=password.encode())
                    
                    elapsed = time.time() - self.start_time
                    speed = i / elapsed if elapsed > 0 else 0
                    self.update_signal.emit(password, i, total_words, speed)
                    self.result_signal.emit(password, True)
                    return
                    
                except (RuntimeError, zipfile.BadZipFile, pyzipper.BadZipFile):
                    if i % 10 == 0:  # Atualiza a cada 10 tentativas para melhor performance
                        elapsed = time.time() - self.start_time
                        speed = i / elapsed if elapsed > 0 else 0
                        self.update_signal.emit(password, i, total_words, speed)
                    continue
                except Exception as e:
                    self.result_signal.emit(f"Erro: {e}", False)
                    return
        
        self.result_signal.emit("Senha não encontrada na wordlist", False)

    def stop(self):
        self.running = False


class MeltZipGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MeltZip - Quebrador de Senhas ZIP")
        self.setGeometry(100, 100, 900, 700)
        self.thread = None
        self.initUI()
    
    def initUI(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Configuração do tema moderno
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
            QGroupBox {
                color: #2c3e50;
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #3498db;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 15px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #2c3e50;
            }
            QLabel {
                color: #2c3e50;
                font-size: 12px;
            }
            QLabel#titleLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
            }
            QLabel#infoLabel {
                color: #7f8c8d;
                font-size: 11px;
                background-color: #f8f9fa;
                padding: 6px;
                border-radius: 4px;
                border: 1px solid #e9ecef;
            }
            QLineEdit {
                background-color: white;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                padding: 8px;
                border-radius: 4px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 15px;
                font-weight: bold;
                min-width: 100px;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
            QPushButton#browseButton {
                background-color: #95a5a6;
            }
            QPushButton#browseButton:hover {
                background-color: #7f8c8d;
            }
            QPushButton#startButton {
                background-color: #27ae60;
            }
            QPushButton#startButton:hover {
                background-color: #229954;
            }
            QPushButton#pauseButton {
                background-color: #f39c12;
            }
            QPushButton#pauseButton:hover {
                background-color: #e67e22;
            }
            QPushButton#cancelButton {
                background-color: #e74c3c;
            }
            QPushButton#cancelButton:hover {
                background-color: #c0392b;
            }
            QPushButton#githubButton {
                background-color: transparent;
                color: #3498db;
                text-decoration: underline;
                border: none;
                padding: 5px;
                font-size: 11px;
            }
            QPushButton#githubButton:hover {
                color: #2980b9;
            }
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                text-align: center;
                height: 25px;
                font-size: 12px;
                color: #2c3e50;
            }
            QProgressBar::chunk {
                background-color: #27ae60;
                border-radius: 4px;
            }
            QTextEdit {
                background-color: white;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
            }
            QTextEdit:focus {
                border: 2px solid #3498db;
            }
        """)

        # Título
        title_frame = QFrame()
        title_layout = QVBoxLayout()
        title_label = QLabel("MeltZip - Quebrador de Senhas ZIP")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        
        subtitle_label = QLabel("Ferramenta para quebra de senhas de arquivos ZIP")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #7f8c8d; font-size: 14px;")
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        title_frame.setLayout(title_layout)
        main_layout.addWidget(title_frame)

        # Painel de configuração
        config_frame = QFrame()
        config_layout = QGridLayout()
        config_layout.setSpacing(12)
        
        # Arquivo ZIP
        zip_label = QLabel("Arquivo ZIP:")
        zip_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        self.zip_line = QLineEdit()
        self.zip_line.setPlaceholderText("Selecione um arquivo ZIP")
        self.browse_zip_btn = QPushButton("Procurar...")
        self.browse_zip_btn.setObjectName("browseButton")
        self.browse_zip_btn.clicked.connect(self.browse_zip)
        
        # Info do ZIP
        self.zip_info = QLabel("Selecione um arquivo ZIP")
        self.zip_info.setObjectName("infoLabel")
        
        # Wordlist
        wordlist_label = QLabel("Wordlist:")
        wordlist_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        self.wordlist_line = QLineEdit()
        self.wordlist_line.setPlaceholderText("Selecione uma wordlist")
        self.browse_wordlist_btn = QPushButton("Procurar...")
        self.browse_wordlist_btn.setObjectName("browseButton")
        self.browse_wordlist_btn.clicked.connect(self.browse_wordlist)
        
        # Info da Wordlist
        self.wordlist_info = QLabel("Selecione uma wordlist")
        self.wordlist_info.setObjectName("infoLabel")
        
        config_layout.addWidget(zip_label, 0, 0)
        config_layout.addWidget(self.zip_line, 0, 1)
        config_layout.addWidget(self.browse_zip_btn, 0, 2)
        config_layout.addWidget(self.zip_info, 1, 0, 1, 3)
        
        config_layout.addWidget(wordlist_label, 2, 0)
        config_layout.addWidget(self.wordlist_line, 2, 1)
        config_layout.addWidget(self.browse_wordlist_btn, 2, 2)
        config_layout.addWidget(self.wordlist_info, 3, 0, 1, 3)
        
        config_frame.setLayout(config_layout)
        main_layout.addWidget(config_frame)
        
        # Barra de progresso
        self.progress = QProgressBar()
        self.progress.setFormat("%p%")
        main_layout.addWidget(self.progress)
        
        # Status
        self.status_label = QLabel("Pronto para iniciar")
        self.status_label.setStyleSheet("font-size: 14px; color: #27ae60; font-weight: bold; padding: 8px; background-color: #ecf0f1; border-radius: 6px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        # Estatísticas
        stats_frame = QFrame()
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)
        
        speed_group = QGroupBox("Velocidade")
        speed_layout = QVBoxLayout()
        self.speed_label = QLabel("0.0 senhas/s")
        self.speed_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        self.speed_label.setAlignment(Qt.AlignCenter)
        speed_layout.addWidget(self.speed_label)
        speed_group.setLayout(speed_layout)
        
        time_group = QGroupBox("Tempo restante")
        time_layout = QVBoxLayout()
        self.time_label = QLabel("--:--:--")
        self.time_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        self.time_label.setAlignment(Qt.AlignCenter)
        time_layout.addWidget(self.time_label)
        time_group.setLayout(time_layout)
        
        progress_group = QGroupBox("Progresso")
        progress_layout = QVBoxLayout()
        self.progress_label = QLabel("0/0 (0%)")
        self.progress_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        self.progress_label.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.progress_label)
        progress_group.setLayout(progress_layout)
        
        attempts_group = QGroupBox("Tentativas")
        attempts_layout = QVBoxLayout()
        self.attempts_label = QLabel("0")
        self.attempts_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        self.attempts_label.setAlignment(Qt.AlignCenter)
        attempts_layout.addWidget(self.attempts_label)
        attempts_group.setLayout(attempts_layout)
        
        stats_layout.addWidget(speed_group)
        stats_layout.addWidget(time_group)
        stats_layout.addWidget(progress_group)
        stats_layout.addWidget(attempts_group)
        stats_frame.setLayout(stats_layout)
        main_layout.addWidget(stats_frame)
        
        # Log
        log_group = QGroupBox("Log de Execução")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
        
        # Botões
        buttons_frame = QFrame()
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        
        self.start_btn = QPushButton("Iniciar")
        self.start_btn.setObjectName("startButton")
        self.start_btn.clicked.connect(self.start_cracking)
        
        self.pause_btn = QPushButton("Pausar")
        self.pause_btn.setObjectName("pauseButton")
        self.pause_btn.clicked.connect(self.pause_cracking)
        self.pause_btn.setEnabled(False)
        
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.setObjectName("cancelButton")
        self.cancel_btn.clicked.connect(self.cancel_cracking)
        self.cancel_btn.setEnabled(False)
        
        buttons_layout.addWidget(self.start_btn)
        buttons_layout.addWidget(self.pause_btn)
        buttons_layout.addWidget(self.cancel_btn)
        buttons_frame.setLayout(buttons_layout)
        main_layout.addWidget(buttons_frame)
        
        # Footer com informações do desenvolvedor
        footer_frame = QFrame()
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(10, 5, 10, 5)
        
        # Informações de autoria
        author_label = QLabel("Desenvolvido por: Lhuany Motta  |  Versão: 1.0  |  ")
        author_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        
        # Link do GitHub (como botão estilizado para parecer um link)
        self.github_btn = QPushButton("GitHub: LhuanyMotta")
        self.github_btn.setObjectName("githubButton")
        self.github_btn.setCursor(Qt.PointingHandCursor)
        self.github_btn.clicked.connect(self.open_github)
        
        footer_layout.addWidget(author_label)
        footer_layout.addWidget(self.github_btn)
        footer_layout.addStretch()
        
        footer_frame.setLayout(footer_layout)
        footer_frame.setStyleSheet("background-color: #ecf0f1; border-radius: 6px;")
        main_layout.addWidget(footer_frame)
        
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
    
    def browse_zip(self):
        file, _ = QFileDialog.getOpenFileName(self, "Selecione o arquivo ZIP", "", "ZIP Files (*.zip)")
        if file:
            self.zip_line.setText(file)
            # Atualiza informações do ZIP
            try:
                size = os.path.getsize(file)
                size_kb = size / 1024
                self.zip_info.setText(f"Tamanho: {size} bytes ({size_kb:.1f} KB)")
            except:
                self.zip_info.setText("Não foi possível obter informações")
    
    def browse_wordlist(self):
        file, _ = QFileDialog.getOpenFileName(self, "Selecione a wordlist", "", "Text Files (*.txt);;All Files (*)")
        if file:
            self.wordlist_line.setText(file)
            # Atualiza informações da wordlist
            try:
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    line_count = sum(1 for _ in f)
                size = os.path.getsize(file)
                size_kb = size / 1024
                self.wordlist_info.setText(f"Senhas: {line_count}, Tamanho: {size} bytes ({size_kb:.1f} KB)")
            except:
                self.wordlist_info.setText("Não foi possível obter informações")
    
    def open_github(self):
        """Abre o perfil do GitHub no navegador padrão"""
        github_url = QUrl("https://github.com/LhuanyMotta")
        QDesktopServices.openUrl(github_url)
    
    def start_cracking(self):
        zip_file = self.zip_line.text()
        wordlist = self.wordlist_line.text()
        
        if not zip_file or not wordlist:
            QMessageBox.warning(self, "Aviso", "Selecione o arquivo ZIP e a wordlist!")
            return
        
        if not os.path.exists(zip_file):
            QMessageBox.warning(self, "Aviso", "O arquivo ZIP não existe!")
            return
            
        if not os.path.exists(wordlist):
            QMessageBox.warning(self, "Aviso", "A wordlist não existe!")
            return
        
        self.log_text.clear()
        self.thread = ZipCrackerThread(zip_file, wordlist)
        self.thread.update_signal.connect(self.update_progress)
        self.thread.result_signal.connect(self.show_result)
        self.thread.info_signal.connect(self.update_zip_info)
        self.thread.start()
        
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        self.status_label.setText("Processando...")
        self.status_label.setStyleSheet("font-size: 14px; color: #f39c12; font-weight: bold; padding: 8px; background-color: #fef5e7; border-radius: 6px;")
        self.log_text.append("[INFO] Iniciando ataque ao arquivo: " + zip_file)
        self.log_text.append("[INFO] Usando wordlist: " + wordlist)
    
    def pause_cracking(self):
        if self.thread and self.thread.isRunning():
            if self.pause_btn.text() == "Pausar":
                self.thread.stop()
                self.pause_btn.setText("Continuar")
                self.status_label.setText("Pausado")
                self.status_label.setStyleSheet("font-size: 14px; color: #f39c12; font-weight: bold; padding: 8px; background-color: #fef5e7; border-radius: 6px;")
                self.log_text.append("[INFO] Processo pausado")
            else:
                self.thread.start()
                self.pause_btn.setText("Pausar")
                self.status_label.setText("Processando...")
                self.status_label.setStyleSheet("font-size: 14px; color: #f39c12; font-weight: bold; padding: 8px; background-color: #fef5e7; border-radius: 6px;")
                self.log_text.append("[INFO] Processo continuado")
    
    def cancel_cracking(self):
        if self.thread:
            self.thread.stop()
            self.thread.wait()
            self.status_label.setText("Interrompido pelo usuário")
            self.status_label.setStyleSheet("font-size: 14px; color: #e74c3c; font-weight: bold; padding: 8px; background-color: #fdedec; border-radius: 6px;")
            self.log_text.append("[INFO] Processo cancelado pelo usuário")
            self.start_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.pause_btn.setText("Pausar")
            self.cancel_btn.setEnabled(False)
    
    def update_progress(self, password, current, total, speed):
        percent = int((current / total) * 100) if total > 0 else 0
        elapsed = time.time() - self.thread.start_time
        remaining = (elapsed / current) * (total - current) if current > 0 else 0
        
        self.progress.setValue(percent)
        self.status_label.setText(
            f"Testando... {current}/{total} ({percent}%) | "
            f"Velocidade: {speed:.1f} p/s | "
            f"Última tentativa: {password[:20]}{'...' if len(password) > 20 else ''}"
        )
        
        # Atualiza estatísticas
        self.speed_label.setText(f"{speed:.1f} senhas/s")
        self.progress_label.setText(f"{current}/{total} ({percent}%)")
        self.time_label.setText(f"{timedelta(seconds=int(remaining))}")
        self.attempts_label.setText(f"{current}")
        
        # Log a cada 10 tentativas
        if current % 10 == 0:
            self.log_text.append(f"[TESTE] Testando: {password} ({current}/{total})")
    
    def update_zip_info(self, info):
        encryption_text = info.get('encryption', 'Desconhecido')
        size_text = info.get('size', 0)
        files_text = info.get('files', 0)
        protected_text = info.get('protected_files', 0)
        
        encryption_display = "AES (Avançada)" if encryption_text == "AES" else "ZipCrypto"
        size_kb = size_text / 1024
        
        self.zip_info.setText(
            f"Criptografia: {encryption_display} | "
            f"Tamanho: {size_text} bytes ({size_kb:.1f} KB) | "
            f"Arquivos: {protected_text} protegido(s) de {files_text} total"
        )
    
    def show_result(self, message, success):
        if success:
            elapsed = time.time() - self.thread.start_time
            self.log_text.append(f"\n[SUCESSO] Senha encontrada: {message}")
            self.log_text.append(f"[INFO] Tempo total: {timedelta(seconds=int(elapsed))}")
            self.log_text.append(f"[INFO] Tentativas realizadas: {self.attempts_label.text()}")
            
            # Caixa de mensagem personalizada
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Sucesso!")
            msg.setText("Senha encontrada com sucesso!")
            msg.setInformativeText(f"Senha: {message}\nTempo: {timedelta(seconds=int(elapsed))}\nTentativas: {self.attempts_label.text()}")
            
            # Padronizar botões
            ok_button = msg.addButton("OK", QMessageBox.AcceptRole)
            ok_button.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    font-weight: bold;
                    min-width: 80px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #229954;
                }
            """)
            
            msg.exec_()
            
            self.status_label.setText("Senha encontrada!")
            self.status_label.setStyleSheet("font-size: 14px; color: #27ae60; font-weight: bold; padding: 8px; background-color: #eafaf1; border-radius: 6px;")
        else:
            self.log_text.append(f"\n[FALHA] {message}")
            self.log_text.append(f"[INFO] Tentativas realizadas: {self.attempts_label.text()}")
            
            if "Erro" not in message:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Resultado")
                msg.setText("Senha não encontrada")
                msg.setInformativeText(f"{message}\n\nTentativas realizadas: {self.attempts_label.text()}")
                
                # Padronizar botões
                ok_button = msg.addButton("OK", QMessageBox.AcceptRole)
                ok_button.setStyleSheet("""
                    QPushButton {
                        background-color: #f39c12;
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        font-weight: bold;
                        min-width: 80px;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: #e67e22;
                    }
                """)
                
                msg.exec_()
            else:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setWindowTitle("Erro")
                msg.setText("Ocorreu um erro")
                msg.setInformativeText(f"{message}\n\nTentativas realizadas: {self.attempts_label.text()}")
                
                # Padronizar botões
                ok_button = msg.addButton("OK", QMessageBox.AcceptRole)
                ok_button.setStyleSheet("""
                    QPushButton {
                        background-color: #e74c3c;
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        font-weight: bold;
                        min-width: 80px;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: #c0392b;
                    }
                """)
                
                msg.exec_()
            
            self.status_label.setText("Falha - Senha não encontrada")
            self.status_label.setStyleSheet("font-size: 14px; color: #e74c3c; font-weight: bold; padding: 8px; background-color: #fdedec; border-radius: 6px;")
        
        self.progress.setValue(100)
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Definir o ícone da aplicação
    icon_paths = ["lock.png", "lock_icon.png", "cadeado.png", "icon.png"]
    icon = None
    
    for path in icon_paths:
        if os.path.exists(path):
            icon = QIcon(path)
            break
    
    if icon:
        app.setWindowIcon(icon)
    
    window = MeltZipGUI()
    
    if icon:
        window.setWindowIcon(icon)
    
    window.show()
    sys.exit(app.exec_())