import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from main import migrate_from_paths

class MigrationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CMake to Bazel Migration Tool")
        self.root.geometry("600x300")
        
        # Создаем и размещаем элементы интерфейса
        self.create_widgets()
        
    def create_widgets(self):
        # Компонент path
        comp_frame = ttk.LabelFrame(self.root, text="Путь к компоненту", padding=10)
        comp_frame.pack(fill="x", padx=10, pady=5)
        
        self.comp_path = tk.StringVar()
        comp_entry = ttk.Entry(comp_frame, textvariable=self.comp_path)
        comp_entry.pack(side="left", fill="x", expand=True)
        
        comp_btn = ttk.Button(comp_frame, text="Обзор...", 
                            command=lambda: self.browse_path(self.comp_path))
        comp_btn.pack(side="right", padx=5)

        # Asgard doc path
        doc_frame = ttk.LabelFrame(self.root, text="Путь к документации Asgard", padding=10)
        doc_frame.pack(fill="x", padx=10, pady=5)
        
        self.doc_path = tk.StringVar()
        doc_entry = ttk.Entry(doc_frame, textvariable=self.doc_path)
        doc_entry.pack(side="left", fill="x", expand=True)
        
        doc_btn = ttk.Button(doc_frame, text="Обзор...", 
                           command=lambda: self.browse_path(self.doc_path))
        doc_btn.pack(side="right", padx=5)

        # Кнопка миграции
        migrate_btn = ttk.Button(self.root, text="Выполнить миграцию", 
                               command=self.run_migration)
        migrate_btn.pack(pady=20)

        # Статус
        self.status_var = tk.StringVar(value="Готов к работе")
        status_label = ttk.Label(self.root, textvariable=self.status_var)
        status_label.pack(pady=10)

    def browse_path(self, var):
        path = filedialog.askdirectory()
        if path:
            var.set(path)

    def run_migration(self):
        comp_path = self.comp_path.get()
        doc_path = self.doc_path.get()
        
        if not comp_path or not doc_path:
            messagebox.showerror("Ошибка", "Необходимо указать оба пути")
            return

        self.status_var.set("Выполняется миграция...")
        self.root.update()
        
        success, message = migrate_from_paths(comp_path, doc_path)
        
        if success:
            messagebox.showinfo("Успех", message)
        else:
            messagebox.showerror("Ошибка", message)
        
        self.status_var.set("Готов к работе")

if __name__ == "__main__":
    root = tk.Tk()
    app = MigrationGUI(root)
    root.mainloop()