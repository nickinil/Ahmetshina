import json
import os
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

DATA_FILE = "trainings.json"

class TrainingPlanner:
    def __init__(self, root):
        self.root = root
        self.root.title("Training Planner - План тренировок")
        self.root.geometry("900x600")
        self.root.resizable(True, True)
        
        # Установка стиля
        self.setup_styles()
        
        # Загрузка данных
        self.trainings = []
        self.load_data()
        
        # Создание интерфейса
        self.create_input_frame()
        self.create_filter_frame()
        self.create_table_frame()
        self.create_stats_frame()
        
        # Обновление таблицы
        self.refresh_table()
        
        # Сохранение при закрытии
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def setup_styles(self):
        """Настройка стилей интерфейса"""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Title.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Success.TButton', foreground='green')
        style.configure('Danger.TButton', foreground='red')
    
    def create_input_frame(self):
        """Форма для добавления тренировки"""
        input_frame = ttk.LabelFrame(self.root, text="➕ Добавить новую тренировку", padding=15)
        input_frame.pack(fill="x", padx=10, pady=5)
        
        # Дата
        ttk.Label(input_frame, text="Дата:", font=('Arial', 10)).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.date_entry = ttk.Entry(input_frame, width=15, font=('Arial', 10))
        self.date_entry.grid(row=0, column=1, padx=5, pady=5)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        # Подсказка для даты
        ttk.Label(input_frame, text="(ГГГГ-ММ-ДД)", foreground="gray").grid(row=0, column=2, sticky="w", padx=5)
        
        # Тип тренировки
        ttk.Label(input_frame, text="Тип тренировки:", font=('Arial', 10)).grid(row=0, column=3, sticky="w", padx=5, pady=5)
        self.type_var = tk.StringVar()
        self.training_types = ["Бег", "Плавание", "Велосипед", "Силовая", "Йога", "Растяжка", "Кроссфит", "Танцы"]
        self.type_combo = ttk.Combobox(input_frame, textvariable=self.type_var, values=self.training_types, 
                                       width=15, font=('Arial', 10), state="readonly")
        self.type_combo.grid(row=0, column=4, padx=5, pady=5)
        self.type_combo.set("Бег")
        
        # Длительность
        ttk.Label(input_frame, text="Длительность (мин):", font=('Arial', 10)).grid(row=0, column=5, sticky="w", padx=5, pady=5)
        self.duration_entry = ttk.Entry(input_frame, width=10, font=('Arial', 10))
        self.duration_entry.grid(row=0, column=6, padx=5, pady=5)
        
        # Кнопка добавления
        add_btn = ttk.Button(input_frame, text="➕ Добавить тренировку", command=self.add_training, 
                            style='Success.TButton')
        add_btn.grid(row=0, column=7, padx=15, pady=5)
        
        # Привязка Enter к добавлению
        self.duration_entry.bind('<Return>', lambda e: self.add_training())
    
    def create_filter_frame(self):
        """Фильтрация тренировок"""
        filter_frame = ttk.LabelFrame(self.root, text="🔍 Фильтр тренировок", padding=10)
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        # Фильтр по типу
        ttk.Label(filter_frame, text="Тип тренировки:", font=('Arial', 10)).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.filter_type_var = tk.StringVar(value="Все")
        self.filter_type_combo = ttk.Combobox(filter_frame, textvariable=self.filter_type_var, 
                                              values=["Все"] + self.training_types, 
                                              width=15, state="readonly")
        self.filter_type_combo.grid(row=0, column=1, padx=5, pady=5)
        self.filter_type_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_table())
        
        # Фильтр по дате
        ttk.Label(filter_frame, text="Дата:", font=('Arial', 10)).grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.filter_date_entry = ttk.Entry(filter_frame, width=15, font=('Arial', 10))
        self.filter_date_entry.grid(row=0, column=3, padx=5, pady=5)
        self.filter_date_entry.bind("<KeyRelease>", lambda e: self.refresh_table())
        
        # Быстрые фильтры по дате
        ttk.Label(filter_frame, text="Быстрые фильтры:", font=('Arial', 10)).grid(row=0, column=4, sticky="w", padx=5, pady=5)
        
        today_btn = ttk.Button(filter_frame, text="Сегодня", command=self.filter_today, width=8)
        today_btn.grid(row=0, column=5, padx=2, pady=5)
        
        week_btn = ttk.Button(filter_frame, text="Эта неделя", command=self.filter_this_week, width=10)
        week_btn.grid(row=0, column=6, padx=2, pady=5)
        
        # Кнопка сброса фильтра
        reset_btn = ttk.Button(filter_frame, text="🔄 Сбросить фильтр", command=self.reset_filter)
        reset_btn.grid(row=0, column=7, padx=10, pady=5)
    
    def create_table_frame(self):
        """Таблица с тренировками"""
        table_frame = ttk.LabelFrame(self.root, text="📊 Список тренировок", padding=10)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Создание таблицы с прокруткой
        self.tree_frame = ttk.Frame(table_frame)
        self.tree_frame.pack(fill="both", expand=True)
        
        # Вертикальный скроллбар
        v_scrollbar = ttk.Scrollbar(self.tree_frame)
        v_scrollbar.pack(side="right", fill="y")
        
        # Горизонтальный скроллбар
        h_scrollbar = ttk.Scrollbar(self.tree_frame, orient="horizontal")
        h_scrollbar.pack(side="bottom", fill="x")
        
        # Таблица
        columns = ("date", "type", "duration")
        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show="headings", 
                                 yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Настройка заголовков
        self.tree.heading("date", text="📅 Дата")
        self.tree.heading("type", text="🏃 Тип тренировки")
        self.tree.heading("duration", text="⏱ Длительность (мин)")
        
        # Настройка ширины колонок
        self.tree.column("date", width=120, anchor="center")
        self.tree.column("type", width=150, anchor="center")
        self.tree.column("duration", width=130, anchor="center")
        
        self.tree.pack(fill="both", expand=True)
        
        # Связывание скроллбаров
        v_scrollbar.config(command=self.tree.yview)
        h_scrollbar.config(command=self.tree.xview)
        
        # Контекстное меню для таблицы
        self.create_context_menu()
        
        # Кнопка удаления
        button_frame = ttk.Frame(table_frame)
        button_frame.pack(fill="x", pady=5)
        
        delete_btn = ttk.Button(button_frame, text="🗑 Удалить выбранное", command=self.delete_selected, style='Danger.TButton')
        delete_btn.pack(side="left", padx=5)
        
        edit_btn = ttk.Button(button_frame, text="✏ Редактировать", command=self.edit_selected)
        edit_btn.pack(side="left", padx=5)
        
        export_btn = ttk.Button(button_frame, text="💾 Экспорт в JSON", command=self.export_data)
        export_btn.pack(side="right", padx=5)
    
    def create_stats_frame(self):
        """Статистика тренировок"""
        stats_frame = ttk.Frame(self.root)
        stats_frame.pack(fill="x", padx=10, pady=5)
        
        self.stats_label = ttk.Label(stats_frame, text="", font=('Arial', 10, 'italic'))
        self.stats_label.pack()
    
    def create_context_menu(self):
        """Создание контекстного меню для таблицы"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Редактировать", command=self.edit_selected)
        self.context_menu.add_command(label="Удалить", command=self.delete_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Копировать дату", command=self.copy_date)
        self.context_menu.add_command(label="Копировать тип", command=self.copy_type)
        self.context_menu.add_command(label="Копировать длительность", command=self.copy_duration)
        
        self.tree.bind("<Button-3>", self.show_context_menu)
    
    def show_context_menu(self, event):
        """Показать контекстное меню"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def add_training(self):
        """Добавление тренировки с проверкой"""
        date = self.date_entry.get().strip()
        training_type = self.type_var.get()
        duration = self.duration_entry.get().strip()
        
        # Проверка даты
        if not self.validate_date(date):
            messagebox.showerror("Ошибка ввода", 
                               "Неверный формат даты!\n\nИспользуйте формат: ГГГГ-ММ-ДД\nПример: 2026-04-28")
            return
        
        # Проверка длительности
        if not self.validate_duration(duration):
            messagebox.showerror("Ошибка ввода", 
                               "Длительность должна быть положительным числом!\n\nПример: 30, 45.5, 60")
            return
        
        # Добавление
        duration_val = float(duration)
        self.trainings.append({
            "date": date,
            "type": training_type,
            "duration": duration_val
        })
        
        # Сортировка по дате
        self.trainings.sort(key=lambda x: x["date"])
        
        self.save_data()
        self.refresh_table()
        
        # Очистка поля длительности
        self.duration_entry.delete(0, tk.END)
        
        messagebox.showinfo("Успех", f"✅ Тренировка добавлена!\n\nДата: {date}\nТип: {training_type}\nДлительность: {duration} мин")
    
    def validate_date(self, date_str):
        """Проверка корректности даты"""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False
    
    def validate_duration(self, duration_str):
        """Проверка корректности длительности"""
        try:
            duration = float(duration_str)
            return duration > 0
        except ValueError:
            return False
    
    def delete_selected(self):
        """Удаление выбранной тренировки"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Пожалуйста, выберите тренировку для удаления")
            return
        
        if messagebox.askyesno("Подтверждение", f"Вы действительно хотите удалить {len(selected)} тренировку(и)?"):
            # Получаем индексы для удаления
            indices_to_remove = []
            for item in selected:
                values = self.tree.item(item, "values")
                # Находим и удаляем из списка
                for i, training in enumerate(self.trainings):
                    if (training["date"] == values[0] and 
                        training["type"] == values[1] and 
                        float(training["duration"]) == float(values[2])):
                        indices_to_remove.append(i)
                        break
            
            # Удаляем в обратном порядке
            for i in sorted(indices_to_remove, reverse=True):
                del self.trainings[i]
            
            self.save_data()
            self.refresh_table()
            messagebox.showinfo("Успех", f"✅ {len(selected)} тренировка(и) удалена")
    
    def edit_selected(self):
        """Редактирование выбранной тренировки"""
        selected = self.tree.selection()
        if not selected or len(selected) > 1:
            messagebox.showwarning("Предупреждение", "Пожалуйста, выберите одну тренировку для редактирования")
            return
        
        # Получаем данные выбранной тренировки
        values = self.tree.item(selected[0], "values")
        
        # Создаём окно редактирования
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Редактирование тренировки")
        edit_window.geometry("400x250")
        edit_window.resizable(False, False)
        
        # Центрируем окно
        edit_window.transient(self.root)
        edit_window.grab_set()
        
        # Поля редактирования
        ttk.Label(edit_window, text="Редактирование тренировки", font=('Arial', 12, 'bold')).pack(pady=10)
        
        frame = ttk.Frame(edit_window, padding=20)
        frame.pack(fill="both", expand=True)
        
        ttk.Label(frame, text="Дата (ГГГГ-ММ-ДД):").grid(row=0, column=0, sticky="w", pady=5)
        date_entry = ttk.Entry(frame, width=15)
        date_entry.grid(row=0, column=1, pady=5, padx=5)
        date_entry.insert(0, values[0])
        
        ttk.Label(frame, text="Тип тренировки:").grid(row=1, column=0, sticky="w", pady=5)
        type_combo = ttk.Combobox(frame, values=self.training_types, width=13, state="readonly")
        type_combo.grid(row=1, column=1, pady=5, padx=5)
        type_combo.set(values[1])
        
        ttk.Label(frame, text="Длительность (мин):").grid(row=2, column=0, sticky="w", pady=5)
        duration_entry = ttk.Entry(frame, width=10)
        duration_entry.grid(row=2, column=1, pady=5, padx=5)
        duration_entry.insert(0, values[2])
        
        def save_edit():
            new_date = date_entry.get().strip()
            new_type = type_combo.get()
            new_duration = duration_entry.get().strip()
            
            if not self.validate_date(new_date):
                messagebox.showerror("Ошибка", "Неверный формат даты!")
                return
            
            if not self.validate_duration(new_duration):
                messagebox.showerror("Ошибка", "Длительность должна быть положительным числом!")
                return
            
            # Обновляем данные
            for training in self.trainings:
                if (training["date"] == values[0] and 
                    training["type"] == values[1] and 
                    float(training["duration"]) == float(values[2])):
                    training["date"] = new_date
                    training["type"] = new_type
                    training["duration"] = float(new_duration)
                    break
            
            self.trainings.sort(key=lambda x: x["date"])
            self.save_data()
            self.refresh_table()
            edit_window.destroy()
            messagebox.showinfo("Успех", "Тренировка обновлена!")
        
        button_frame = ttk.Frame(edit_window)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Сохранить", command=save_edit).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Отмена", command=edit_window.destroy).pack(side="left", padx=5)
    
    def copy_date(self):
        """Копирование даты выбранной тренировки"""
        selected = self.tree.selection()
        if selected:
            values = self.tree.item(selected[0], "values")
            self.root.clipboard_clear()
            self.root.clipboard_append(values[0])
            messagebox.showinfo("Успех", "Дата скопирована!")
    
    def copy_type(self):
        """Копирование типа выбранной тренировки"""
        selected = self.tree.selection()
        if selected:
            values = self.tree.item(selected[0], "values")
            self.root.clipboard_clear()
            self.root.clipboard_append(values[1])
            messagebox.showinfo("Успех", "Тип тренировки скопирован!")
    
    def copy_duration(self):
        """Копирование длительности выбранной тренировки"""
        selected = self.tree.selection()
        if selected:
            values = self.tree.item(selected[0], "values")
            self.root.clipboard_clear()
            self.root.clipboard_append(values[2])
            messagebox.showinfo("Успех", "Длительность скопирована!")
    
    def refresh_table(self):
        """Обновление таблицы с учетом фильтров"""
        # Очистить таблицу
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Применить фильтры
        filtered = self.trainings.copy()
        
        # Фильтр по типу
        filter_type = self.filter_type_var.get()
        if filter_type != "Все":
            filtered = [t for t in filtered if t["type"] == filter_type]
        
        # Фильтр по дате
        filter_date = self.filter_date_entry.get().strip()
        if filter_date:
            if self.validate_date(filter_date):
                filtered = [t for t in filtered if t["date"] == filter_date]
        
        # Заполнение таблицы
        for training in filtered:
            self.tree.insert("", "end", values=(training["date"], training["type"], training["duration"]))
        
        # Обновление статистики
        self.update_stats(filtered)
    
    def update_stats(self, filtered_trainings):
        """Обновление статистики"""
        if not filtered_trainings:
            self.stats_label.config(text="📊 Нет тренировок для отображения")
            return
        
        total_trainings = len(filtered_trainings)
        total_duration = sum(t["duration"] for t in filtered_trainings)
        avg_duration = total_duration / total_trainings
        
        # Подсчёт по типам
        type_count = {}
        for t in filtered_trainings:
            type_count[t["type"]] = type_count.get(t["type"], 0) + 1
        
        most_common_type = max(type_count, key=type_count.get) if type_count else "Нет"
        
        stats_text = f"📊 Всего: {total_trainings} | ⏱ Общее время: {total_duration:.0f} мин | 📊 Среднее: {avg_duration:.0f} мин | 🏆 Чаще всего: {most_common_type}"
        self.stats_label.config(text=stats_text)
    
    def filter_today(self):
        """Фильтр на сегодня"""
        today = datetime.now().strftime("%Y-%m-%d")
        self.filter_date_entry.delete(0, tk.END)
        self.filter_date_entry.insert(0, today)
        self.refresh_table()
    
    def filter_this_week(self):
        """Фильтр на текущую неделю"""
        today = datetime.now()
        start_of_week = today - datetime.timedelta(days=today.weekday())
        end_of_week = start_of_week + datetime.timedelta(days=6)
        
        filtered = [t for t in self.trainings if start_of_week.strftime("%Y-%m-%d") <= t["date"] <= end_of_week.strftime("%Y-%m-%d")]
        
        # Временная установка фильтра
        self.filter_date_entry.delete(0, tk.END)
        self.filter_date_entry.insert(0, f"Неделя {start_of_week.strftime('%d.%m')}-{end_of_week.strftime('%d.%m')}")
        
        # Обновляем таблицу вручную
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for training in filtered:
            self.tree.insert("", "end", values=(training["date"], training["type"], training["duration"]))
        
        self.update_stats(filtered)
    
    def reset_filter(self):
        """Сброс фильтрации"""
        self.filter_type_var.set("Все")
        self.filter_date_entry.delete(0, tk.END)
        self.refresh_table()
    
    def export_data(self):
        """Экспорт данных в JSON"""
        if not self.trainings:
            messagebox.showwarning("Предупреждение", "Нет данных для экспорта")
            return
        
        export_file = f"trainings_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(export_file, "w", encoding="utf-8") as f:
                json.dump(self.trainings, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Успех", f"Данные экспортированы в файл:\n{export_file}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать данные:\n{str(e)}")
    
    def load_data(self):
        """Загрузка данных из JSON"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.trainings = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                self.trainings = []
                self.create_sample_data()
        else:
            self.create_sample_data()
    
    def create_sample_data(self):
        """Создание примеров данных для демонстрации"""
        if not self.trainings:
            self.trainings = [
                {"date": "2026-04-25", "type": "Бег", "duration": 30},
                {"date": "2026-04-26", "type": "Плавание", "duration": 45},
                {"date": "2026-04-27", "type": "Силовая", "duration": 60},
                {"date": "2026-04-28", "type": "Йога", "duration": 40},
            ]
            self.save_data()
    
    def save_data(self):
        """Сохранение данных в JSON"""
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.trainings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить данные:\n{str(e)}")
    
    def on_close(self):
        """При закрытии окна"""
        self.save_data()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TrainingPlanner(root)
    root.mainloop()