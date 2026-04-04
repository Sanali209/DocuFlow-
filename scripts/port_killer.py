#!/usr/bin/env python3
"""Port Killer - GUI utility for freeing occupied ports on Windows."""

import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import threading


def get_all_processes() -> dict[str, str]:
    """Get all running processes as {PID: name} dict. Single call optimization."""
    try:
        result = subprocess.run(
            ['tasklist', '/FO', 'CSV'],
            capture_output=True,
            text=True,
            encoding='cp866'
        )
        processes = {}
        lines = result.stdout.strip().split('\n')
        for line in lines[1:]:  # Skip header
            parts = line.split(',')
            if len(parts) >= 2:
                name = parts[0].strip('"')
                pid = parts[1].strip('"')
                processes[pid] = name
        return processes
    except Exception as e:
        print(f"Error getting processes: {e}")
        return {}


def get_listening_ports() -> list[dict]:
    """Get all listening TCP ports using netstat."""
    try:
        result = subprocess.run(
            ['netstat', '-ano', '-p', 'TCP'],
            capture_output=True,
            text=True,
            encoding='cp866'
        )
        
        ports = []
        for line in result.stdout.split('\n'):
            if 'LISTENING' in line:
                parts = line.split()
                if len(parts) >= 5:
                    addr_port = parts[1]
                    if ':' in addr_port:
                        port = addr_port.split(':')[-1]
                        pid = parts[4]
                        ports.append({
                            'port': port,
                            'pid': pid,
                            'status': 'LISTENING'
                        })
        return ports
    except Exception as e:
        print(f"Error getting ports: {e}")
        return []


def get_process_name(pid: str) -> str:
    """Get process name by PID."""
    try:
        result = subprocess.run(
            ['tasklist', '/FI', f'PID eq {pid}', '/FO', 'CSV'],
            capture_output=True,
            text=True,
            encoding='cp866'
        )
        lines = result.stdout.strip().split('\n')
        if len(lines) > 1:
            parts = lines[1].split(',')
            if len(parts) > 0:
                return parts[0].strip('"')
    except Exception:
        pass
    return "Unknown"


def kill_process(pid: str) -> bool:
    """Kill process by PID."""
    try:
        result = subprocess.run(
            ['taskkill', '/PID', pid, '/F'],
            capture_output=True,
            text=True,
            encoding='cp866'
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error killing process: {e}")
        return False


class PortKillerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Port Killer - Освобождение портов")
        self.root.geometry("700x500")
        self._loading = False
        
        # Search frame
        search_frame = ttk.Frame(root, padding="10")
        search_frame.pack(fill=tk.X)
        
        ttk.Label(search_frame, text="Порт:").pack(side=tk.LEFT)
        self.port_entry = ttk.Entry(search_frame, width=15)
        self.port_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(search_frame, text="Найти", command=self.search_port).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Убить процесс", command=self.kill_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Обновить", command=self.refresh).pack(side=tk.RIGHT)
        
        # Status label
        self.status_label = ttk.Label(root, text="", foreground="gray")
        self.status_label.pack(fill=tk.X, padx=10)
        
        # Treeview
        columns = ('port', 'pid', 'process', 'status')
        self.tree = ttk.Treeview(root, columns=columns, show='headings', height=15)
        
        self.tree.heading('port', text='Порт')
        self.tree.heading('pid', text='PID')
        self.tree.heading('process', text='Имя процесса')
        self.tree.heading('status', text='Статус')
        
        self.tree.column('port', width=80)
        self.tree.column('pid', width=80)
        self.tree.column('process', width=300)
        self.tree.column('status', width=100)
        
        scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Auto-refresh (increased to 15 seconds)
        self.auto_refresh()
        self.refresh()
    
    def refresh(self):
        """Refresh port list - optimized version."""
        if self._loading:
            return
        
        self._loading = True
        self.status_label.config(text="Загрузка...")
        
        def load_data():
            try:
                # Get ports and processes in parallel (both fast)
                ports = get_listening_ports()
                processes = get_all_processes()
                self.root.after(0, lambda: self._update_tree(ports, processes))
            except Exception as e:
                print(f"Error loading: {e}")
                self.root.after(0, lambda: self.status_label.config(text=f"Ошибка: {e}"))
            finally:
                self.root.after(0, lambda: setattr(self, '_loading', False))
        
        threading.Thread(target=load_data, daemon=True).start()
    
    def _update_tree(self, ports: list[dict], processes: dict[str, str]):
        """Update treeview with port data - uses cached process dict."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for port_info in ports:
            process_name = processes.get(port_info['pid'], "Unknown")
            self.tree.insert('', tk.END, values=(
                port_info['port'],
                port_info['pid'],
                process_name,
                port_info['status']
            ))
        
        self.status_label.config(text=f"Загружено {len(ports)} портов")
    
    def search_port(self):
        """Search for specific port."""
        port = self.port_entry.get().strip()
        if not port:
            messagebox.showwarning("Внимание", "Введите номер порта")
            return
        
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            if str(values[0]) == port:
                self.tree.selection_set(item)
                self.tree.see(item)
                return
        
        messagebox.showinfo("Информация", f"Порт {port} не найден")
    
    def kill_selected(self):
        """Kill selected process."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите процесс")
            return
        
        item = selected[0]
        values = self.tree.item(item)['values']
        pid = values[1]
        process = values[2]
        port = values[0]
        
        if messagebox.askyesno("Подтверждение", 
                               f"Завершить процесс?\n\n"
                               f"Порт: {port}\n"
                               f"PID: {pid}\n"
                               f"Процесс: {process}"):
            if kill_process(str(pid)):
                messagebox.showinfo("Успех", f"Процесс {pid} завершён")
                self.refresh()
            else:
                messagebox.showerror("Ошибка", f"Не удалось завершить процесс {pid}")
    
    def auto_refresh(self):
        """Auto refresh every 15 seconds."""
        self.refresh()
        self.root.after(15000, self.auto_refresh)


def main():
    root = tk.Tk()
    app = PortKillerApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()