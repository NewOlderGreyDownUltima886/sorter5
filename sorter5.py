import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD

import codecs
import sys
import os

class DragDropFrame(tk.Frame):
    def __init__(self, parent, text="Перетащите файл сюда", command=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.command = command
        self.default_bg = self.cget('bg')
        self.default_text = text
        self.configure(relief='solid', bd=2, bg='#f0f0f0', height=100, width=250)
        self.pack_propagate(False)
        self.text_frame = tk.Frame(self, bg='#f0f0f0', width=250)
        self.text_frame.pack_propagate(False)
        self.text_frame.pack(expand=True, fill=tk.BOTH)
        self.label = tk.Label(self.text_frame, text=text, bg='#f0f0f0', fg='#666666', 
                             font=('Arial', 12), cursor='hand2', wraplength=340,
                             width=40, height=3)
        self.label.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        self.bind_events()
        
    def bind_events(self):
        self.bind('<Button-1>', self.on_click)
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<DropEnter>>', self.on_drag_enter)
        self.dnd_bind('<<DropLeave>>', self.on_drag_leave)
        self.dnd_bind('<<Drop>>', self.on_drop)
        self.label.bind('<Button-1>', self.on_click)
        self.label.bind('<Enter>', self.on_enter)
        self.label.bind('<Leave>', self.on_leave)
        self.text_frame.bind('<Button-1>', self.on_click)
        self.text_frame.bind('<Enter>', self.on_enter)
        self.text_frame.bind('<Leave>', self.on_leave)
    
    def on_click(self, event):
        if self.command:
            filename = filedialog.askopenfilename(
                title="Выберите файл с вопросами",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if filename:
                self.command(filename)
    
    def on_enter(self, event):
        self.configure(bg='#e0e0e0')
        self.text_frame.configure(bg='#e0e0e0')
        self.label.configure(bg='#e0e0e0')
    
    def on_leave(self, event):
        self.configure(bg=self.default_bg)
        self.text_frame.configure(bg=self.default_bg)
        self.label.configure(bg=self.default_bg)
    
    def on_drag_enter(self, event):
        self.configure(bg='#d0f0d0')
        self.text_frame.configure(bg='#d0f0d0')
        self.label.configure(bg='#d0f0d0', text="Отпустите файл для загрузки")
        return 'copy'
    
    def on_drag_leave(self, event):
        self.configure(bg=self.default_bg)
        self.text_frame.configure(bg=self.default_bg)
        self.label.configure(bg=self.default_bg, text=self.default_text)
    
    def on_drop(self, event):
        file_path = event.data
        if file_path.startswith('{') and file_path.endswith('}'):
            file_path = file_path[1:-1]
        if self.command:
            self.command(file_path)

class DuplicatesWindow:
    def __init__(self, parent, duplicates, restore_callback=None):
        self.parent = parent
        self.duplicates = duplicates
        self.restore_callback = restore_callback
        self.selected_duplicate = None
        
        self.window = tk.Toplevel(parent)
        self.window.title("Просмотр удаленных повторов")
        self.window.geometry("800x600")
        self.window.minsize(600, 400)
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        title_label = ttk.Label(main_frame, text="Сравнение похожих вопросов", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 15))
        self.info_label = ttk.Label(main_frame, 
                              text=f"Найдено пар похожих вопросов: {len(duplicates)}",
                              font=('Arial', 12))
        self.info_label.pack(pady=(0, 10))
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        left_frame = ttk.Frame(content_frame, width=200)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False)
        self.right_frame = ttk.Frame(content_frame)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        list_label = ttk.Label(left_frame, text="Пары вопросов:", font=('Arial', 10, 'bold'))
        list_label.pack(anchor=tk.W, pady=(0, 5))
        
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        self.list_canvas = tk.Canvas(list_frame, highlightthickness=0)
        self.list_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.list_canvas.yview)
        self.list_scrollable_frame = ttk.Frame(self.list_canvas)
        
        self.list_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.list_canvas.configure(scrollregion=self.list_canvas.bbox("all"))
        )
        
        self.list_canvas.create_window((0, 0), window=self.list_scrollable_frame, anchor="nw")
        self.list_canvas.configure(yscrollcommand=self.list_scrollbar.set)
        
        self.list_canvas.pack(side="left", fill="both", expand=True)
        self.list_scrollbar.pack(side="right", fill="y")
        self.create_duplicates_list(self.list_scrollable_frame)
        if self.duplicates:
            self.select_duplicate(0)
        def on_list_mousewheel(event):
            self.list_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        self.list_canvas.bind_all("<MouseWheel>", on_list_mousewheel)


    def create_duplicates_list(self, parent):
        for i, duplicate in enumerate(self.duplicates):
            card_bg = '#d4edda' if self.selected_duplicate is not None and i == self.selected_duplicate else '#f5f5f5'
            card = tk.Frame(parent, bg=card_bg, relief='solid', bd=1, cursor='hand2')
            card.pack(fill=tk.X, pady=(0, 5), padx=2)
            card.bind('<Button-1>', lambda e, idx=i: self.select_duplicate(idx))
            number_label = tk.Label(card, text=f"Пара #{i+1}", 
                                bg='#e0e0e0', font=('Arial', 9, 'bold'),
                                cursor='hand2')
            number_label.pack(fill=tk.X, padx=1, pady=(1, 0))
            number_label.bind('<Button-1>', lambda e, idx=i: self.select_duplicate(idx))
            question_short = duplicate['question2'][:60] + "..." if len(duplicate['question2']) > 60 else duplicate['question2']
            
            desc_label = tk.Label(card, text=question_short, 
                                bg=card_bg, font=('Arial', 8), justify=tk.LEFT,
                                cursor='hand2', wraplength=180)
            desc_label.pack(fill=tk.X, padx=5, pady=5)
            desc_label.bind('<Button-1>', lambda e, idx=i: self.select_duplicate(idx))
            def on_enter(event, c=card, idx=i):
                if self.selected_duplicate != idx:
                    c.configure(bg='#e8f4f8')
            def on_leave(event, c=card, idx=i):
                if self.selected_duplicate != idx:
                    c.configure(bg='#f5f5f5')
            
            card.bind('<Enter>', on_enter)
            card.bind('<Leave>', on_leave)
            number_label.bind('<Enter>', on_enter)
            number_label.bind('<Leave>', on_leave)
            desc_label.bind('<Enter>', on_enter)
            desc_label.bind('<Leave>', on_leave)


    def select_duplicate(self, index):
        if self.selected_duplicate is not None and self.selected_duplicate < len(self.list_scrollable_frame.winfo_children()):
            prev_card = self.list_scrollable_frame.winfo_children()[self.selected_duplicate]
            prev_card.configure(bg='#f5f5f5')
        selected_card = self.list_scrollable_frame.winfo_children()[index]
        selected_card.configure(bg='#d4edda')
        
        self.selected_duplicate = index
        self.show_comparison(index)
        self.scroll_to_selected(index)

    def scroll_to_selected(self, index):
        if not self.list_scrollable_frame.winfo_children():
            return
        
        selected_card = self.list_scrollable_frame.winfo_children()[index]
        card_y = selected_card.winfo_y()
        card_height = selected_card.winfo_height()
        canvas_height = self.list_canvas.winfo_height()
        card_top = card_y
        card_bottom = card_y + card_height
        current_top = self.list_canvas.yview()[0] * self.list_scrollable_frame.winfo_height()
        current_bottom = current_top + canvas_height
        if card_top < current_top:
            relative_pos = card_top / self.list_scrollable_frame.winfo_height()
            self.list_canvas.yview_moveto(relative_pos)
        elif card_bottom > current_bottom:
            relative_pos = (card_bottom - canvas_height) / self.list_scrollable_frame.winfo_height()
            self.list_canvas.yview_moveto(relative_pos)


    def show_comparison(self, index):
        for widget in self.right_frame.winfo_children():
            widget.destroy()
        
        duplicate = self.duplicates[index]
        comp_label = ttk.Label(self.right_frame, 
                            text=f"Сравнение вопросов - Пара #{index + 1}", 
                            font=('Arial', 14, 'bold'))
        comp_label.pack(anchor=tk.W, pady=(0, 15))
        columns_frame = ttk.Frame(self.right_frame)
        columns_frame.pack(fill=tk.BOTH, expand=True)
        left_col = ttk.Frame(columns_frame)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        left_label = ttk.Label(left_col, text="Первый вопрос (оставлен):", 
                              font=('Arial', 11, 'bold'))
        left_label.pack(anchor=tk.W, pady=(0, 10))
        left_text = tk.Text(left_col, wrap=tk.WORD, width=35, height=15,
                           font=('Arial', 10), bg='#f8f9fa', relief='solid', bd=1)
        left_scroll = ttk.Scrollbar(left_col, orient="vertical", command=left_text.yview)
        left_text.configure(yscrollcommand=left_scroll.set)
        
        left_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        left_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        left_text.insert('1.0', "Вопрос:\n" + duplicate['question1'] + "\n\n")
        left_text.insert('end', "Ответы:\n")
        for answer in duplicate['answers1']:
            left_text.insert('end', f"{answer}\n")
        left_text.config(state='disabled')
        right_col = ttk.Frame(columns_frame)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        right_label = ttk.Label(right_col, text="Второй вопрос (удален):", 
                               font=('Arial', 11, 'bold'))
        right_label.pack(anchor=tk.W, pady=(0, 10))
        right_text = tk.Text(right_col, wrap=tk.WORD, width=35, height=15,
                            font=('Arial', 10), bg='#fff3cd', relief='solid', bd=1)
        right_scroll = ttk.Scrollbar(right_col, orient="vertical", command=right_text.yview)
        right_text.configure(yscrollcommand=right_scroll.set)
        
        right_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        right_text.insert('1.0', "Вопрос:\n" + duplicate['question2'] + "\n\n")
        right_text.insert('end', "Ответы:\n")
        for answer in duplicate['answers2']:
            right_text.insert('end', f"{answer}\n")
        right_text.config(state='disabled')
        buttons_frame = ttk.Frame(self.right_frame)
        buttons_frame.pack(fill=tk.X, pady=(15, 0))
        next_index = (index + 1) % len(self.duplicates)
        skip_text = "Пропустить" if index < len(self.duplicates) - 1 else "К первой паре"
        self.skip_button = ttk.Button(buttons_frame, text=skip_text,
                                    command=lambda: self.select_duplicate(next_index))
        self.skip_button.pack(side=tk.LEFT, padx=(0, 10))
        self.restore_button = ttk.Button(buttons_frame, text="Вернуть вопрос",
                                       command=lambda: self.restore_question(index))
        self.restore_button.pack(side=tk.LEFT)


    def restore_question(self, index):
        if self.restore_callback:
            success = self.restore_callback(index)
            if not success:
                return
            scroll_position = self.list_canvas.yview()
            self.duplicates.pop(index)
            self.selected_duplicate = None
            
            if len(self.duplicates) == 0:
                self.window.destroy()
                return
            self.info_label.config(text=f"Найдено пар похожих вопросов: {len(self.duplicates)}")
            for widget in self.list_scrollable_frame.winfo_children():
                widget.destroy()
                
            self.create_duplicates_list(self.list_scrollable_frame)
            self.list_canvas.update_idletasks()
            self.list_canvas.yview_moveto(scroll_position[0])
            if index < len(self.duplicates):
                next_index = index
            else:
                next_index = 0
            self.select_duplicate(next_index)


    def update_interface(self):
        pass


class SorterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sorter5")
        self.root.geometry("275x750")
        self.root.minsize(275, 750)
        self.kof_var = tk.StringVar(value="70")
        self.file_path_var = tk.StringVar()
        self.initial_questions_var = tk.StringVar(value="0")
        self.duplicates_var = tk.StringVar(value="0")
        self.final_questions_var = tk.StringVar(value="0")
        self.last_result = None
        self.duplicates_list = []
        self.all_questions_data = {}
        self.removed_questions = {}
        
        self.setup_ui()
    
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(main_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        title_label = ttk.Label(self.scrollable_frame, text="Фильтрация вопросов", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20), fill=tk.X)
        self.drag_drop_frame = DragDropFrame(self.scrollable_frame, 
                                           text="Перетащите файл\nили кликните для выбора",
                                           command=self.on_file_selected)
        self.drag_drop_frame.pack(fill=tk.X, pady=(0, 15))
        file_info_frame = ttk.Frame(self.scrollable_frame)
        file_info_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(file_info_frame, text="Выбранный файл:").pack(anchor=tk.W)
        file_display_frame = ttk.Frame(file_info_frame)
        file_display_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.file_display = ttk.Label(file_display_frame, text="Файл не выбран", 
                                     foreground="gray", wraplength=350)
        self.file_display.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(file_display_frame, text="✕", width=3,
                  command=self.clear_file).pack(side=tk.RIGHT, padx=(5, 0))
        kof_frame = ttk.Frame(self.scrollable_frame)
        kof_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(kof_frame, text="Коэффициент сходства (%):").pack(anchor=tk.W)
        
        kof_input_frame = ttk.Frame(kof_frame)
        kof_input_frame.pack(fill=tk.X, pady=(5, 0))
        
        kof_entry = ttk.Entry(kof_input_frame, textvariable=self.kof_var, width=10, 
                             font=('Arial', 12), justify='center')
        kof_entry.pack(side=tk.LEFT)
        
        ttk.Label(kof_input_frame, text="(от 1 до 100)").pack(side=tk.LEFT, padx=(10, 0))
        self.run_button = ttk.Button(self.scrollable_frame, text="Запустить фильтрацию",
                                   command=self.run_filter, state="disabled")
        self.run_button.pack(fill=tk.X, pady=(0, 20))
        separator = ttk.Separator(self.scrollable_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=(0, 15))
        results_label = ttk.Label(self.scrollable_frame, text="Результаты", 
                                 font=('Arial', 14, 'bold'))
        results_label.pack(anchor=tk.W, pady=(0, 10))
        results_frame = ttk.Frame(self.scrollable_frame)
        results_frame.pack(fill=tk.X, pady=(0, 15))
        card1 = self.create_result_card(results_frame, "Вопросов до", 
                                       self.initial_questions_var, "#e3f2fd")
        card1.pack(fill=tk.X, pady=(0, 8))
        card2 = self.create_result_card(results_frame, "Найдено совпадений", 
                                       self.duplicates_var, "#fff3e0")
        card2.pack(fill=tk.X, pady=(0, 8))
        card3 = self.create_result_card(results_frame, "Вопросов после", 
                                       self.final_questions_var, "#e8f5e8")
        card3.pack(fill=tk.X, pady=(0, 8))
        self.duplicates_button = ttk.Button(self.scrollable_frame, 
                                          text="Посмотреть повторы",
                                          command=self.show_duplicates, 
                                          state="disabled")
        self.duplicates_button.pack(fill=tk.X, pady=(10, 0))
        self.save_button = ttk.Button(self.scrollable_frame, text="Сохранить результат",
                                    command=self.save_result, state="disabled")
        self.save_button.pack(fill=tk.X, pady=(10, 0))
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        self.scrollable_frame.bind("<Configure>", on_frame_configure)
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        self.scrollable_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
    
    def create_result_card(self, parent, title, variable, color):
        card = tk.Frame(parent, bg=color, relief='solid', bd=1, height=60)
        card.pack_propagate(False)
        
        title_label = tk.Label(card, text=title, bg=color, font=('Arial', 9),
                              foreground='#666666')
        title_label.pack(anchor=tk.W, padx=10, pady=(6, 0))
        
        value_label = tk.Label(card, textvariable=variable, bg=color, 
                              font=('Arial', 16, 'bold'), foreground='#333333')
        value_label.pack(anchor=tk.W, padx=10, pady=(0, 6))
        
        return card
    
    def on_file_selected(self, filename):
        self.file_path_var.set(filename)
        short_name = os.path.basename(filename)
        if len(short_name) > 25:
            short_name = short_name[:23] + "..."
    
        too_short_name = os.path.basename(filename)
        if len(too_short_name) > 20:
            too_short_name = too_short_name[:17] + "..."
    
    
        self.file_display.config(text=short_name, foreground="black")
        self.drag_drop_frame.label.config(text=f"Загружен:\n{too_short_name}")
        self.run_button.config(state="normal")
        self.clear_results()
    
    def clear_file(self):
        self.file_path_var.set("")
        self.file_display.config(text="Файл не выбран", foreground="gray")
        self.drag_drop_frame.label.config(text="Перетащите файл\nили кликните для выбора")
        self.drag_drop_frame.configure(bg='#f0f0f0')
        self.run_button.config(state="disabled")
        self.save_button.config(state="disabled")
        self.duplicates_button.config(state="disabled")
        self.clear_results()
    
    def clear_results(self):
        self.initial_questions_var.set("0")
        self.duplicates_var.set("0")
        self.final_questions_var.set("0")
        self.last_result = None
        self.duplicates_list = []
        self.all_questions_data = {}
        self.removed_questions = {}
    
    def run_filter(self):
        try:
            kof = int(self.kof_var.get())
            if kof < 1 or kof > 100:
                messagebox.showerror("Ошибка", "Коэффициент сходства должен быть от 1 до 100")
                return
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректный коэффициент")
            return
        
        file_path = self.file_path_var.get()
        if not file_path:
            messagebox.showerror("Ошибка", "Выберите файл с вопросами")
            return
        
        if not os.path.exists(file_path):
            messagebox.showerror("Ошибка", "Файл не существует")
            return
        
        try:
            result = self.run_sorter_logic(kof, file_path)
            self.display_results(result)
            self.save_button.config(state="normal")
            if result['duplicates_found'] > 0:
                self.duplicates_button.config(state="normal")
            else:
                self.duplicates_button.config(state="disabled")
            
        except Exception as e:
            error_msg = f"Ошибка при выполнении: {str(e)}"
            messagebox.showerror("Ошибка", error_msg)
    
    def run_sorter_logic(self, kof, file_source):
        
        try:
            fileObj = codecs.open(file_source, "r", "utf_8_sig")
        except Exception:
            raise Exception("Ошибка открытия файла")
        
        lines = fileObj.readlines()
        def isit(str1, str2):
            kof_local = 100/kof
            num_of_need_sovpad = int(len(str1)/kof_local)
            
            res1 = str1[0:num_of_need_sovpad-1]
            res2 = str2
            
            res1 = res1.split(' ')
            res1 = ''.join(res1)
            
            res2 = res2.split(' ')
            res2 = ''.join(res2)
            
            if res1 in res2 or res2 in res1:
                return True
            
            return False
        new_kof = 100/kof
        num_of_sovpad = 0
        new_result_dict = {}
        new_elements_to_append = {}
        all_questions = {}
        duplicates_pairs = []
        removed_questions = {}
        
        def append_new_element_to_result_dict(question, new_answers, dop_num=1, new_question='') -> None:
            nonlocal num_of_sovpad
            
            if new_question == '':
                new_question = question
            
            if new_question in new_result_dict:
                dop_num += 1
                new_question = question + f" {dop_num}"
                return append_new_element_to_result_dict(question, new_answers, dop_num, new_question)
            elif new_question in new_elements_to_append:
                dop_num += 1
                new_question = question + f" {dop_num}"
                return append_new_element_to_result_dict(question, new_answers, dop_num, new_question)
            
            new_elements_to_append[new_question] = new_answers.copy()
            new_result_dict.update(new_elements_to_append)
            new_elements_to_append.clear()
            return None
        
        def is_it_really_new_check(now_question, now_answers):
            nonlocal num_of_sovpad
            dict_repeat = {}
            for saved_question in new_result_dict:
                if isit(now_question, saved_question):
                    dict_repeat.update({saved_question: new_result_dict[saved_question]})
            
            if len(dict_repeat) == 0:
                return True
            
            is_it_really_new = True
            for saved_question in dict_repeat:
                num_of_sovpad += 1
                saved_answers = new_result_dict[saved_question]
                
                if len(saved_answers) == len(now_answers):
                    sovpads = [0 for i in range(len(saved_answers))]
                    
                    for i, var1 in enumerate(saved_answers):
                        for var2 in now_answers:
                            if isit(var1, var2):
                                sovpads[i] = 1
                                break
                    if 0 not in sovpads:
                        is_it_really_new = False
                        duplicates_pairs.append({
                            'question1': saved_question,
                            'question2': now_question,
                            'answers1': saved_answers,
                            'answers2': now_answers
                        })
                        removed_questions[now_question] = now_answers.copy()
            
            return is_it_really_new
        num_of_all_questions = 0
        tmp_answer_list = []
        tmp_now_question = ''
        for line in lines:
            line = line.strip()
            if len(line) != 0:
                if line[0] in ['+', '-']:
                    tmp_answer_list.append(line)
                elif line[0] == '?':
                    if tmp_now_question != '':
                        all_questions[tmp_now_question] = tmp_answer_list.copy()
                    
                    line = line[1:]
                    tmp_now_question = line
                    tmp_answer_list.clear()
                    num_of_all_questions += 1
        if tmp_now_question:
            all_questions[tmp_now_question] = tmp_answer_list.copy()
        fileObj.seek(0)
        lines = fileObj.readlines()
        
        tmp_answer_list = []
        tmp_now_question = ''
        
        for line in lines:
            line = line.strip()
            if len(line) != 0:
                if line[0] in ['+', '-']:
                    tmp_answer_list.append(line)
                elif line[0] == '?':
                    if tmp_now_question != '':
                        now_question = tmp_now_question
                        now_answers = tmp_answer_list.copy()
                        
                        is_it_really_new = is_it_really_new_check(now_question, now_answers)
                        if is_it_really_new:
                            append_new_element_to_result_dict(now_question, tmp_answer_list)
                    
                    line = line[1:]
                    tmp_now_question = line
                    tmp_answer_list.clear()
        if tmp_now_question:
            is_it_really_new = is_it_really_new_check(tmp_now_question, tmp_answer_list)
            if is_it_really_new:
                append_new_element_to_result_dict(tmp_now_question, tmp_answer_list)
        
        fileObj.close()
        result = {
            'initial_questions': num_of_all_questions,
            'final_questions': len(new_result_dict),
            'duplicates_found': num_of_all_questions - len(new_result_dict),
            'result_dict': new_result_dict,
            'duplicates_pairs': duplicates_pairs,
            'removed_questions': removed_questions,
            'all_questions': all_questions,
            'output_file': None
        }
        
        return result
    
    def get_output_filename(self, original_path, count):
        file_res = original_path.split('.')
        tmp = "".join(file_res[:-1])
        return f"{tmp}_filtered_{count}.{file_res[-1]}"
    
    def display_results(self, result):
        self.initial_questions_var.set(str(result['initial_questions']))
        self.duplicates_var.set(str(result['duplicates_found']))
        self.final_questions_var.set(str(result['final_questions']))
        self.last_result = result
        self.duplicates_list = result['duplicates_pairs']
        self.all_questions_data = result['all_questions']
        self.removed_questions = result['removed_questions']
    
    def show_duplicates(self):
        if not self.duplicates_list:
            messagebox.showinfo("Информация", "Нет пар похожих вопросов для отображения")
            return
        
        DuplicatesWindow(self.root, self.duplicates_list, self.restore_duplicate)
    
    def restore_duplicate(self, index):
        try:
            duplicate = self.duplicates_list[index]
            question_to_restore = duplicate['question2']
            answers_to_restore = duplicate['answers2']
            self.last_result['result_dict'][question_to_restore] = answers_to_restore
            self.last_result['final_questions'] += 1
            self.last_result['duplicates_found'] -= 1
            if question_to_restore in self.removed_questions:
                del self.removed_questions[question_to_restore]
            self.display_results(self.last_result)
            if self.last_result['duplicates_found'] == 0:
                self.duplicates_button.config(state="disabled")
            
            return True
            
        except Exception as e:
            print(f"Ошибка при восстановлении: {e}")
            return False
    
    def save_result(self):
        file_path = self.file_path_var.get()
        if not file_path:
            messagebox.showwarning("Внимание", "Сначала выберите файл!")
            return
        
        try:
            if self.last_result is None:
                kof = int(self.kof_var.get())
                result = self.run_sorter_logic(kof, file_path)
            else:
                result = self.last_result
                
            count = result['final_questions']
            output_filename = self.get_output_filename(file_path, count)


            output_file = filedialog.asksaveasfilename(
                title="Сохранить результат",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialfile=os.path.basename(output_filename)
            )
            
            if output_file:
                new_file = codecs.open(output_file, "w", "utf_8_sig")
                for i, (k, v) in enumerate(result['result_dict'].items()):
                    res_str = f'?{i+1}. {k}'
                    for answer in v:
                        res_str += f"\n{answer}"
                    res_str += '\n\n'
                    new_file.write(res_str)
                new_file.close()
                messagebox.showinfo("Успех", f"Результат сохранен в файл:\n{output_file}")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при сохранении файла: {str(e)}")

def main():
    root = TkinterDnD.Tk()
    app = SorterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
