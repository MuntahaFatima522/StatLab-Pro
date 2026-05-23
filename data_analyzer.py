"""
Statistical Data Analyzer Pro — Enhanced Edition
Professional desktop application with modern UI and advanced analytics
"""

import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.colors import LinearSegmentedColormap
import csv
import os
import json
import math
from datetime import datetime
from matplotlib.figure import Figure
import pandas as pd
from scipy import stats
from scipy.stats import normaltest, shapiro, kstest

# ─── Color Palette ────────────────────────────────────────────────────────────
COLORS = {
    'bg':            '#0d0f14',
    'panel':         '#13161f',
    'card':          '#1a1d2b',
    'card_hover':    '#1f2336',
    'border':        '#2a2d3e',
    'border_light':  '#363a52',
    'accent':        '#5b6ef5',
    'accent2':       '#8b5cf6',
    'accent3':       '#06d6a0',
    'accent4':       '#f59e0b',
    'accent5':       '#ef4444',
    'text':          '#e8eaf6',
    'text_dim':      '#7c82a6',
    'text_bright':   '#ffffff',
    'success':       '#10b981',
    'warning':       '#f59e0b',
    'danger':        '#ef4444',
    'info':          '#3b82f6',
    'chart1':        '#5b6ef5',
    'chart2':        '#8b5cf6',
    'chart3':        '#06d6a0',
    'chart4':        '#f59e0b',
    'chart5':        '#ef4444',
    'chart6':        '#ec4899',
}

FONT_TITLE   = ('SF Pro Display', 20, 'bold')
FONT_HEADING = ('SF Pro Display', 12, 'bold')
FONT_BODY    = ('SF Pro Text', 10)
FONT_MONO    = ('JetBrains Mono', 10)
FONT_SMALL   = ('SF Pro Text', 9)

def try_fonts():
    import tkinter.font as tkfont
    available = tkfont.families()
    title   = next((f for f in ['SF Pro Display','Helvetica Neue','Segoe UI','Ubuntu'] if f in available), 'Helvetica')
    body    = next((f for f in ['SF Pro Text','Helvetica Neue','Segoe UI','Ubuntu'] if f in available), 'Helvetica')
    mono    = next((f for f in ['JetBrains Mono','Fira Code','Consolas','Courier New'] if f in available), 'Courier')
    return title, body, mono

# ─── Utility: Hex → RGB ───────────────────────────────────────────────────────
def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def lighten(hex_color, factor=1.25):
    r, g, b = hex_to_rgb(hex_color)
    return '#{:02x}{:02x}{:02x}'.format(min(int(r*factor),255), min(int(g*factor),255), min(int(b*factor),255))

# ─── Custom Widgets ───────────────────────────────────────────────────────────
class FlatButton(tk.Canvas):
    def __init__(self, parent, text, command=None, width=220, height=34,
                 color=None, text_color='white', icon='', font=None, radius=8):
        bg = parent.cget('bg') if hasattr(parent,'cget') else COLORS['panel']
        super().__init__(parent, width=width, height=height,
                         highlightthickness=0, bg=bg, cursor='hand2')
        self.command   = command
        self.color     = color or COLORS['accent']
        self.hcolor    = lighten(self.color, 1.15)
        self.text_color= text_color
        self.label_txt = (icon + '  ' + text) if icon else text
        self.fnt       = font or ('Helvetica', 9, 'bold')
        self.radius    = radius
        self.w, self.h = width, height
        self._draw(self.color)
        self.bind('<Enter>',    lambda e: self._draw(self.hcolor))
        self.bind('<Leave>',    lambda e: self._draw(self.color))
        self.bind('<Button-1>', lambda e: self.command() if self.command else None)

    def _draw(self, fill):
        self.delete('all')
        r = self.radius
        self.create_polygon(
            r, 0, self.w-r, 0, self.w, 0, self.w, r,
            self.w, self.h-r, self.w, self.h, self.w-r, self.h,
            r, self.h, 0, self.h, 0, self.h-r, 0, r, 0, 0,
            smooth=True, fill=fill, outline=fill
        )
        self.create_text(self.w//2, self.h//2, text=self.label_txt,
                         fill=self.text_color, font=self.fnt, anchor='center')


class Separator(tk.Frame):
    def __init__(self, parent, color=None, **kw):
        super().__init__(parent, height=1, bg=color or COLORS['border'], **kw)


class StatCard(tk.Frame):
    def __init__(self, parent, label, value='—', color=None):
        super().__init__(parent, bg=COLORS['card'], bd=0, relief='flat',
                         highlightthickness=1, highlightbackground=COLORS['border'])
        self.label_var = tk.StringVar(value=label)
        self.value_var = tk.StringVar(value=value)
        color = color or COLORS['accent']
        tk.Frame(self, bg=color, width=3).pack(side='left', fill='y')
        inner = tk.Frame(self, bg=COLORS['card'])
        inner.pack(fill='both', expand=True, padx=10, pady=8)
        tk.Label(inner, textvariable=self.label_var, bg=COLORS['card'],
                 fg=COLORS['text_dim'], font=('Helvetica', 8)).pack(anchor='w')
        self.val_lbl = tk.Label(inner, textvariable=self.value_var, bg=COLORS['card'],
                                fg=COLORS['text_bright'], font=('Helvetica', 15, 'bold'))
        self.val_lbl.pack(anchor='w')

    def update(self, value, color=None):
        self.value_var.set(value)
        if color:
            self.val_lbl.config(fg=color)


# ─── Main App ─────────────────────────────────────────────────────────────────
class StatisticsGUI:
    def __init__(self, root):
        self.root = root
        t, b, m = try_fonts()
        self.FF_TITLE   = t
        self.FF_BODY    = b
        self.FF_MONO    = m

        self.root.title("Statistical Data Analyzer Pro")
        self.root.geometry("1440x860")
        self.root.minsize(1100, 700)
        self.root.configure(bg=COLORS['bg'])

        # State
        self.data        = None
        self.df          = None
        self.column_names= []
        self.filename    = None
        self.history     = []          # undo stack
        self.theme_dark  = True

        self._setup_styles()
        self._build_ui()
        self._show_welcome()

    # ── Styles ──────────────────────────────────────────────────────────────
    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('default')

        style.configure('TNotebook', background=COLORS['panel'], borderwidth=0, tabmargins=0)
        style.configure('TNotebook.Tab', background=COLORS['card'], foreground=COLORS['text_dim'],
                        font=(self.FF_BODY, 9, 'bold'), padding=[16, 8], borderwidth=0)
        style.map('TNotebook.Tab',
                  background=[('selected', COLORS['accent']), ('active', COLORS['card_hover'])],
                  foreground=[('selected', '#ffffff'), ('active', COLORS['text'])])

        style.configure('Treeview', background=COLORS['card'], foreground=COLORS['text'],
                        fieldbackground=COLORS['card'], rowheight=28,
                        font=(self.FF_BODY, 9), borderwidth=0)
        style.configure('Treeview.Heading', background=COLORS['border'],
                        foreground=COLORS['text_dim'], relief='flat',
                        font=(self.FF_BODY, 9, 'bold'))
        style.map('Treeview', background=[('selected', COLORS['accent'])])
        style.map('Treeview.Heading', background=[('active', COLORS['border_light'])])

        style.configure('Vertical.TScrollbar', troughcolor=COLORS['panel'],
                        background=COLORS['border'], borderwidth=0, arrowsize=12)
        style.configure('Horizontal.TScrollbar', troughcolor=COLORS['panel'],
                        background=COLORS['border'], borderwidth=0, arrowsize=12)
        style.configure('TCombobox', fieldbackground=COLORS['card'],
                        background=COLORS['card'], foreground='#000000',
                        arrowcolor=COLORS['text_dim'])
        style.configure('TEntry', fieldbackground=COLORS['card'],
                        foreground='#000000')

    # ── Build UI ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ─ Title Bar ─
        titlebar = tk.Frame(self.root, bg=COLORS['panel'], height=54)
        titlebar.pack(fill='x')
        titlebar.pack_propagate(False)

        tk.Label(titlebar, text='⬡', bg=COLORS['panel'],
                 fg=COLORS['accent'], font=(self.FF_TITLE, 20)).pack(side='left', padx=(18,6), pady=8)
        tk.Label(titlebar, text='StatLab Pro', bg=COLORS['panel'],
                 fg=COLORS['text_bright'], font=(self.FF_TITLE, 14, 'bold')).pack(side='left', pady=8)
        tk.Label(titlebar, text='v3.0', bg=COLORS['accent'],
                 fg='white', font=(self.FF_BODY, 8, 'bold'),
                 padx=7, pady=2).pack(side='left', padx=10, pady=18)

        # right side of title bar
        self.time_lbl = tk.Label(titlebar, text='', bg=COLORS['panel'],
                                  fg=COLORS['text_dim'], font=(self.FF_MONO, 9))
        self.time_lbl.pack(side='right', padx=20)
        self._tick()

        # ─ Stat summary strip ─
        self.strip = tk.Frame(self.root, bg=COLORS['panel'], height=70)
        self.strip.pack(fill='x', padx=0)
        self.strip.pack_propagate(False)
        self._build_stat_strip()

        # ─ Main body ─
        body = tk.Frame(self.root, bg=COLORS['bg'])
        body.pack(fill='both', expand=True)

        # Sidebar
        self._build_sidebar(body)

        # Right panel
        right = tk.Frame(body, bg=COLORS['bg'])
        right.pack(side='left', fill='both', expand=True, padx=(0,8), pady=8)

        # Notebook
        self.notebook = ttk.Notebook(right)
        self.notebook.pack(fill='both', expand=True)

        self.tab_data    = tk.Frame(self.notebook, bg=COLORS['panel'])
        self.tab_stats   = tk.Frame(self.notebook, bg=COLORS['panel'])
        self.tab_viz     = tk.Frame(self.notebook, bg=COLORS['panel'])
        self.tab_dist    = tk.Frame(self.notebook, bg=COLORS['panel'])
        self.tab_insight = tk.Frame(self.notebook, bg=COLORS['panel'])

        self.notebook.add(self.tab_data,    text='  📋 Data  ')
        self.notebook.add(self.tab_stats,   text='  📊 Statistics  ')
        self.notebook.add(self.tab_viz,     text='  📈 Charts  ')
        self.notebook.add(self.tab_dist,    text='  🔬 Distribution  ')
        self.notebook.add(self.tab_insight, text='  💡 Insights  ')

        self._build_data_tab()
        self._build_stats_tab()
        self._build_dist_tab()
        self._build_insight_tab()

        # ─ Status bar ─
        self.statusbar = tk.Frame(self.root, bg=COLORS['panel'], height=28)
        self.statusbar.pack(fill='x', side='bottom')
        self.statusbar.pack_propagate(False)
        self.status_lbl = tk.Label(self.statusbar, text='Ready', bg=COLORS['panel'],
                                    fg=COLORS['text_dim'], font=(self.FF_BODY, 9),
                                    anchor='w', padx=14)
        self.status_lbl.pack(side='left', fill='y')

    # ── Stat Strip ──────────────────────────────────────────────────────────
    def _build_stat_strip(self):
        for w in self.strip.winfo_children():
            w.destroy()

        cards_info = [
            ('ROWS',    '—', COLORS['accent']),
            ('COLUMNS', '—', COLORS['accent2']),
            ('MISSING', '—', COLORS['warning']),
            ('NUMERIC', '—', COLORS['accent3']),
            ('MEMORY',  '—', COLORS['info']),
        ]
        self._strip_cards = {}
        inner = tk.Frame(self.strip, bg=COLORS['panel'])
        inner.pack(fill='both', expand=True, padx=12, pady=8)
        for i, (lbl, val, col) in enumerate(cards_info):
            c = StatCard(inner, lbl, val, col)
            c.pack(side='left', fill='y', padx=5, ipadx=8)
            self._strip_cards[lbl] = c

    def _update_strip(self):
        if self.df is None:
            return
        nc = len(self.df.select_dtypes(include=[np.number]).columns)
        miss = int(self.df.isnull().sum().sum())
        mem  = self.df.memory_usage(deep=True).sum()
        mem_str = f'{mem/1024:.1f} KB' if mem < 1024*1024 else f'{mem/1048576:.1f} MB'
        self._strip_cards['ROWS'].update(str(len(self.df)))
        self._strip_cards['COLUMNS'].update(str(len(self.df.columns)))
        self._strip_cards['MISSING'].update(str(miss), COLORS['danger'] if miss>0 else COLORS['success'])
        self._strip_cards['NUMERIC'].update(str(nc))
        self._strip_cards['MEMORY'].update(mem_str)

    # ── Sidebar ─────────────────────────────────────────────────────────────
    def _build_sidebar(self, parent):
        sb = tk.Frame(parent, bg=COLORS['panel'], width=240)
        sb.pack(side='left', fill='y', padx=(8,0), pady=8)
        sb.pack_propagate(False)

        canvas = tk.Canvas(sb, bg=COLORS['panel'], highlightthickness=0)
        vsb = ttk.Scrollbar(sb, orient='vertical', command=canvas.yview)
        frame = tk.Frame(canvas, bg=COLORS['panel'])
        frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=frame, anchor='nw', width=224)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')
        canvas.bind_all('<MouseWheel>', lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), 'units'))

        def section(title):
            f = tk.Frame(frame, bg=COLORS['panel'])
            f.pack(fill='x', pady=(12,2), padx=8)
            tk.Label(f, text=title.upper(), bg=COLORS['panel'], fg=COLORS['text_dim'],
                     font=(self.FF_BODY, 7, 'bold')).pack(side='left')
            Separator(f, COLORS['border']).pack(fill='x', pady=(6,0))
            return frame

        def btn(parent_f, txt, icon, cmd, color=None):
            b = FlatButton(parent_f, txt, cmd, width=220, height=32,
                           color=color or COLORS['card_hover'],
                           text_color=COLORS['text'],
                           icon=icon,
                           font=(self.FF_BODY, 9))
            b.pack(pady=2, padx=8)

        # ── File ──
        section('File')
        btn(frame, 'Sample Dataset',    '◈', self._load_sample,  COLORS['accent'])
        btn(frame, 'Load CSV / Excel',  '↑', self._load_file)
        btn(frame, 'Export Data',       '↓', self._export_data)
        btn(frame, 'Generate Report',   '✦', self._generate_report, COLORS['accent2'])

        # ── Explore ──
        section('Explore')
        btn(frame, 'Summary Statistics', '≡', self._show_summary)
        btn(frame, 'Column Detail',       '◉', self._show_column_stats)
        btn(frame, 'Correlation Matrix',  '⊞', self._show_correlation)
        btn(frame, 'Missing Values',      '∅', self._show_missing)

        # ── Analysis ──
        section('Analysis')
        btn(frame, 'Outlier Detection',   '⚡', self._show_outliers, COLORS['warning'])
        btn(frame, 'Normality Tests',     '∿', self._normality_tests, COLORS['warning'])
        btn(frame, 'Filter & Query',      '⊘', self._filter_dialog)
        btn(frame, 'Normalize Data',      '⇌', self._show_normalized)
        btn(frame, 'Hypothesis Test',     'H₀', self._hypothesis_test, COLORS['accent3'])
        btn(frame, 'Group Statistics',    '⊕', self._group_stats)

        # ── Visualize ──
        section('Visualize')
        btn(frame, 'Histogram',           '▦', self._plot_histogram,  COLORS['accent3'])
        btn(frame, 'Box Plot',            '▣', self._plot_boxplot,    COLORS['accent3'])
        btn(frame, 'Scatter Plot',        '⁘', self._plot_scatter,    COLORS['accent3'])
        btn(frame, 'Heatmap',             '▧', self._plot_heatmap,    COLORS['accent3'])
        btn(frame, 'Pair Plot',           '⊞', self._plot_pairplot,   COLORS['accent3'])
        btn(frame, 'Time Series',         '↗', self._plot_timeseries, COLORS['accent3'])

        # ── Utility ──
        section('Utility')
        btn(frame, 'Undo Last Action',    '↺', self._undo)
        btn(frame, 'Clear Display',       '✕', self._clear_display, COLORS['danger'])

    # ── Tabs ─────────────────────────────────────────────────────────────────
    def _build_data_tab(self):
        hdr = self._tab_header(self.tab_data, 'Dataset Preview', 'Browse loaded data rows')
        frame = tk.Frame(self.tab_data, bg=COLORS['panel'])
        frame.pack(fill='both', expand=True, padx=10, pady=(0,10))

        vsb = ttk.Scrollbar(frame, orient='vertical')
        hsb = ttk.Scrollbar(frame, orient='horizontal')
        self.tree = ttk.Treeview(frame, columns=[], show='headings',
                                 yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # row highlight toggle
        self.tree.tag_configure('odd',  background=COLORS['card'])
        self.tree.tag_configure('even', background=COLORS['panel'])

    def _build_stats_tab(self):
        hdr = self._tab_header(self.tab_stats, 'Statistical Analysis', 'Detailed numeric summaries')
        frame = tk.Frame(self.tab_stats, bg=COLORS['panel'])
        frame.pack(fill='both', expand=True, padx=10, pady=(0,10))
        self.stats_txt = tk.Text(frame, wrap='word', bg=COLORS['card'],
                                  fg=COLORS['text'], font=(self.FF_MONO, 10),
                                  insertbackground=COLORS['text'],
                                  padx=14, pady=14, relief='flat',
                                  selectbackground=COLORS['accent'])
        vsb = ttk.Scrollbar(frame, orient='vertical', command=self.stats_txt.yview)
        self.stats_txt.configure(yscrollcommand=vsb.set)
        self.stats_txt.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        # Text tags for coloring
        self.stats_txt.tag_configure('h1',    foreground=COLORS['accent'],   font=(self.FF_MONO, 12, 'bold'))
        self.stats_txt.tag_configure('h2',    foreground=COLORS['accent2'],  font=(self.FF_MONO, 10, 'bold'))
        self.stats_txt.tag_configure('good',  foreground=COLORS['success'])
        self.stats_txt.tag_configure('warn',  foreground=COLORS['warning'])
        self.stats_txt.tag_configure('bad',   foreground=COLORS['danger'])
        self.stats_txt.tag_configure('dim',   foreground=COLORS['text_dim'])

    def _build_dist_tab(self):
        hdr = self._tab_header(self.tab_dist, 'Distribution Testing', 'Normality & statistical tests')
        frame = tk.Frame(self.tab_dist, bg=COLORS['panel'])
        frame.pack(fill='both', expand=True, padx=10, pady=(0,10))
        self.dist_txt = tk.Text(frame, wrap='word', bg=COLORS['card'],
                                 fg=COLORS['text'], font=(self.FF_MONO, 10),
                                 padx=14, pady=14, relief='flat')
        vsb = ttk.Scrollbar(frame, orient='vertical', command=self.dist_txt.yview)
        self.dist_txt.configure(yscrollcommand=vsb.set)
        self.dist_txt.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')
        self.dist_txt.tag_configure('h1',   foreground=COLORS['accent'],  font=(self.FF_MONO, 12, 'bold'))
        self.dist_txt.tag_configure('h2',   foreground=COLORS['accent3'], font=(self.FF_MONO, 10, 'bold'))
        self.dist_txt.tag_configure('good', foreground=COLORS['success'])
        self.dist_txt.tag_configure('bad',  foreground=COLORS['danger'])
        self.dist_txt.tag_configure('dim',  foreground=COLORS['text_dim'])

    def _build_insight_tab(self):
        canvas = tk.Canvas(self.tab_insight, bg=COLORS['panel'], highlightthickness=0)
        vsb = ttk.Scrollbar(self.tab_insight, orient='vertical', command=canvas.yview)
        self.insight_frame = tk.Frame(canvas, bg=COLORS['panel'])
        self.insight_frame.bind('<Configure>',
                                lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0,0), window=self.insight_frame, anchor='nw')
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        vsb.pack(side='right', fill='y')

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _tab_header(self, parent, title, subtitle=''):
        f = tk.Frame(parent, bg=COLORS['panel'])
        f.pack(fill='x', padx=10, pady=(10,6))
        tk.Label(f, text=title, bg=COLORS['panel'], fg=COLORS['text_bright'],
                 font=(self.FF_TITLE, 13, 'bold')).pack(side='left')
        if subtitle:
            tk.Label(f, text=subtitle, bg=COLORS['panel'], fg=COLORS['text_dim'],
                     font=(self.FF_BODY, 9)).pack(side='left', padx=10, pady=2)
        return f

    def _status(self, msg):
        self.status_lbl.config(text=f'  {msg}')
        self.root.update()

    def _tick(self):
        self.time_lbl.config(text=datetime.now().strftime('%a %d %b  %H:%M:%S'))
        self.root.after(1000, self._tick)

    def _stats_write(self, text, tag=None):
        if tag:
            self.stats_txt.insert('end', text, tag)
        else:
            self.stats_txt.insert('end', text)

    def _dist_write(self, text, tag=None):
        if tag:
            self.dist_txt.insert('end', text, tag)
        else:
            self.dist_txt.insert('end', text)

    def _require_data(self):
        if self.df is None:
            self._toast('No data loaded. Use the sidebar to load a dataset.', kind='warn')
            return False
        return True

    def _toast(self, msg, kind='info'):
        colors = {'info': COLORS['info'], 'warn': COLORS['warning'],
                  'ok': COLORS['success'], 'err': COLORS['danger']}
        icons  = {'info': 'ℹ', 'warn': '⚠', 'ok': '✓', 'err': '✕'}
        bg = colors.get(kind, COLORS['info'])
        t = tk.Toplevel(self.root)
        t.overrideredirect(True)
        t.configure(bg=bg)
        t.attributes('-topmost', True)
        x = self.root.winfo_x() + self.root.winfo_width() - 340
        y = self.root.winfo_y() + 70
        t.geometry(f'320x52+{x}+{y}')
        tk.Label(t, text=f'{icons[kind]}  {msg}', bg=bg, fg='white',
                 font=(self.FF_BODY, 9), wraplength=290).pack(expand=True)
        t.after(2800, t.destroy)

    def _col_dialog(self, title, callback, multi=False):
        if not self._require_data():
            return
        num_cols = list(self.df.select_dtypes(include=[np.number]).columns)
        dlg = tk.Toplevel(self.root)
        dlg.title(title)
        dlg.configure(bg=COLORS['bg'])
        dlg.geometry('340x200')
        dlg.grab_set()
        tk.Label(dlg, text=title, bg=COLORS['bg'], fg=COLORS['text_bright'],
                 font=(self.FF_TITLE, 11, 'bold')).pack(pady=(18,8))
        var = tk.StringVar(value=num_cols[0] if num_cols else '')
        combo = ttk.Combobox(dlg, textvariable=var, values=num_cols, state='readonly', width=22)
        combo.pack(pady=6)

        def ok():
            dlg.destroy()
            callback(var.get())

        FlatButton(dlg, 'Confirm', ok, width=160, height=34,
                   color=COLORS['accent'], text_color='white').pack(pady=14)

    def _push_history(self):
        if self.df is not None:
            self.history.append(self.df.copy())
            if len(self.history) > 10:
                self.history.pop(0)

    # ── Data Loading ─────────────────────────────────────────────────────────
    def _load_sample(self):
        self._push_history()
        np.random.seed(42)
        n = 200
        dept = np.random.choice(['Engineering','Marketing','Sales','HR','Finance'], n)
        age  = np.random.randint(22, 60, n)
        exp  = np.clip(age - 22 - np.random.randint(0, 5, n), 0, 35)
        sal  = 40000 + exp*2500 + age*300 + np.random.normal(0, 8000, n)
        perf = np.clip(60 + exp*1.2 + np.random.normal(0, 12, n), 0, 100)
        sat  = np.clip(3 + perf*0.02 + np.random.normal(0, 0.8, n), 1, 5)
        self.df           = pd.DataFrame({'Department':dept,'Age':age,'Experience':exp,
                                          'Salary':sal,'Performance':perf,'Satisfaction':sat})
        self.df['Salary'] = self.df['Salary'].round(2)
        self.df['Performance'] = self.df['Performance'].round(1)
        self.df['Satisfaction']= self.df['Satisfaction'].round(2)
        # Inject some missing values
        for col in ['Salary','Performance']:
            idx = np.random.choice(self.df.index, 5, replace=False)
            self.df.loc[idx, col] = np.nan
        self.column_names = list(self.df.columns)
        self.data = self.df.values
        self.filename = 'Sample Dataset'
        self._display_data()
        self._update_strip()
        self._status('Sample dataset loaded (200 rows, 6 columns)')
        self._toast('Sample dataset loaded!', 'ok')
        self._auto_insights()

    def _load_file(self):
        fn = filedialog.askopenfilename(
            title='Open Dataset',
            filetypes=[('CSV files','*.csv'), ('Excel files','*.xlsx *.xls'), ('All files','*.*')])
        if not fn:
            return
        try:
            self._push_history()
            if fn.endswith(('.xlsx','.xls')):
                self.df = pd.read_excel(fn)
            else:
                self.df = pd.read_csv(fn)
            self.column_names = list(self.df.columns)
            self.data = self.df.values
            self.filename = os.path.basename(fn)
            self._display_data()
            self._update_strip()
            self._status(f'Loaded: {self.filename}  ({len(self.df)} rows)')
            self._toast(f'Loaded {len(self.df):,} rows', 'ok')
            self._auto_insights()
        except Exception as e:
            self._toast(f'Load error: {e}', 'err')

    def _display_data(self):
        if self.df is None:
            return
        self.tree.delete(*self.tree.get_children())
        cols = list(self.df.columns)
        self.tree['columns'] = cols
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=110, anchor='center', minwidth=60)
        for i, row in self.df.head(500).iterrows():
            tag = 'odd' if i % 2 else 'even'
            vals = []
            for v in row:
                if isinstance(v, float):
                    vals.append(f'{v:.3f}' if not math.isnan(v) else 'NaN')
                else:
                    vals.append(str(v))
            self.tree.insert('', 'end', values=vals, tags=(tag,))
        self.notebook.select(self.tab_data)

    # ── Statistics ───────────────────────────────────────────────────────────
    def _show_summary(self):
        if not self._require_data():
            return
        self.notebook.select(self.tab_stats)
        t = self.stats_txt
        t.delete('1.0', 'end')
        t.insert('end', '  DATASET SUMMARY\n', 'h1')
        t.insert('end', f'  {"─"*62}\n', 'dim')
        t.insert('end', f'  File      : {self.filename or "Sample Data"}\n')
        t.insert('end', f'  Timestamp : {datetime.now().strftime("%Y-%m-%d  %H:%M:%S")}\n')
        t.insert('end', f'  Rows      : {len(self.df):,}\n')
        t.insert('end', f'  Columns   : {len(self.df.columns)}\n')
        miss = int(self.df.isnull().sum().sum())
        tag = 'bad' if miss > 0 else 'good'
        t.insert('end', f'  Missing   : ')
        t.insert('end', f'{miss} values\n', tag)
        t.insert('end', '\n')

        num = self.df.select_dtypes(include=[np.number])
        if not num.empty:
            t.insert('end', '  NUMERIC COLUMNS\n', 'h2')
            t.insert('end', f'  {"─"*62}\n', 'dim')
            header = f'  {"Column":<16} {"Count":>7} {"Mean":>12} {"Std":>12} {"Min":>10} {"Max":>10} {"Skew":>8}\n'
            t.insert('end', header, 'dim')
            for col in num.columns:
                d = num[col].dropna()
                skew = stats.skew(d)
                t.insert('end',
                    f'  {col:<16} {len(d):>7,} {d.mean():>12.3f} {d.std():>12.3f} '
                    f'{d.min():>10.3f} {d.max():>10.3f} {skew:>8.3f}\n')
            t.insert('end', '\n')

        cat = self.df.select_dtypes(exclude=[np.number])
        if not cat.empty:
            t.insert('end', '  CATEGORICAL COLUMNS\n', 'h2')
            t.insert('end', f'  {"─"*62}\n', 'dim')
            for col in cat.columns:
                t.insert('end', f'  {col:<16}  unique={self.df[col].nunique()}'
                                 f'  top={str(self.df[col].mode()[0]) if not self.df[col].mode().empty else "?"}\n')
        self._status('Summary displayed')

    def _show_column_stats(self):
        self._col_dialog('Column Detail Statistics', self._display_col_stats)

    def _display_col_stats(self, col):
        self.notebook.select(self.tab_stats)
        t = self.stats_txt
        t.delete('1.0', 'end')
        d = self.df[col].dropna()
        t.insert('end', f'  COLUMN: {col}\n', 'h1')
        t.insert('end', f'  {"─"*50}\n', 'dim')
        if pd.api.types.is_numeric_dtype(self.df[col]):
            for label, val in [
                ('Count', f'{len(d):,}'), ('Mean', f'{d.mean():.6f}'),
                ('Median', f'{d.median():.6f}'), ('Std Dev', f'{d.std():.6f}'),
                ('Variance', f'{d.var():.6f}'), ('Min', f'{d.min():.6f}'),
                ('Max', f'{d.max():.6f}'), ('Range', f'{d.max()-d.min():.6f}'),
                ('IQR', f'{d.quantile(.75)-d.quantile(.25):.6f}'),
                ('Skewness', f'{stats.skew(d):.6f}'),
                ('Kurtosis', f'{stats.kurtosis(d):.6f}'),
                ('CV %', f'{(d.std()/d.mean()*100) if d.mean()!=0 else float("nan"):.2f}'),
            ]:
                t.insert('end', f'  {label:<16}: {val}\n')
            t.insert('end', '\n  PERCENTILES\n', 'h2')
            for p in [1,5,10,25,50,75,90,95,99]:
                t.insert('end', f'  p{p:<4}: {np.percentile(d, p):.4f}\n')
        else:
            vc = self.df[col].value_counts()
            t.insert('end', f'  Count    : {self.df[col].count():,}\n')
            t.insert('end', f'  Unique   : {self.df[col].nunique()}\n')
            t.insert('end', '\n  VALUE COUNTS (top 10)\n', 'h2')
            for v, c in vc.head(10).items():
                t.insert('end', f'  {str(v):<20}: {c:>6,}  ({c/len(self.df)*100:.1f}%)\n')

        miss = self.df[col].isnull().sum()
        t.insert('end', f'\n  Missing  : ')
        t.insert('end', f'{miss} ({miss/len(self.df)*100:.1f}%)\n', 'bad' if miss>0 else 'good')
        self._status(f'Column stats: {col}')

    def _show_correlation(self):
        if not self._require_data():
            return
        self.notebook.select(self.tab_stats)
        num = self.df.select_dtypes(include=[np.number])
        if num.shape[1] < 2:
            self._toast('Need at least 2 numeric columns', 'warn')
            return
        corr = num.corr()
        t = self.stats_txt
        t.delete('1.0', 'end')
        t.insert('end', '  PEARSON CORRELATION MATRIX\n', 'h1')
        t.insert('end', f'  {"─"*60}\n', 'dim')
        cols = list(corr.columns)
        # header
        hdr = f'  {"":16}' + ''.join(f'{c:>10}' for c in cols) + '\n'
        t.insert('end', hdr, 'dim')
        for i, r in enumerate(cols):
            row_str = f'  {r:<16}'
            for j, c in enumerate(cols):
                v = corr.iloc[i, j]
                row_str += f'{v:>10.3f}'
            t.insert('end', row_str + '\n')
        t.insert('end', '\n  NOTABLE CORRELATIONS (|r| > 0.5)\n', 'h2')
        for i in range(len(cols)):
            for j in range(i+1, len(cols)):
                v = corr.iloc[i,j]
                if abs(v) > 0.5:
                    strength = 'strong' if abs(v)>0.7 else 'moderate'
                    direction = 'positive' if v>0 else 'negative'
                    tag = 'good' if v>0 else 'bad'
                    t.insert('end', f'  {cols[i]} ↔ {cols[j]}: ')
                    t.insert('end', f'{v:+.3f}  ({strength} {direction})\n', tag)
        self._status('Correlation matrix displayed')

    def _show_missing(self):
        if not self._require_data():
            return
        self.notebook.select(self.tab_stats)
        t = self.stats_txt
        t.delete('1.0', 'end')
        t.insert('end', '  MISSING VALUE ANALYSIS\n', 'h1')
        t.insert('end', f'  {"─"*50}\n', 'dim')
        total = len(self.df)
        t.insert('end', f'  {"Column":<20} {"Missing":>10} {"Pct":>10} {"Bar"}\n', 'dim')
        for col in self.df.columns:
            m = self.df[col].isnull().sum()
            pct = m/total*100
            bar = '█' * int(pct/5) + '░' * (20 - int(pct/5))
            tag = 'bad' if pct > 5 else ('warn' if pct > 0 else 'good')
            t.insert('end', f'  {col:<20} {m:>10,} {pct:>9.1f}%  ')
            t.insert('end', f'{bar}\n', tag)
        t.insert('end', f'\n  Total missing: ', 'dim')
        tm = self.df.isnull().sum().sum()
        t.insert('end', f'{tm} ({tm/(total*len(self.df.columns))*100:.2f}% of all cells)\n',
                 'bad' if tm>0 else 'good')

    def _show_outliers(self):
        if not self._require_data():
            return
        self.notebook.select(self.tab_stats)
        t = self.stats_txt
        t.delete('1.0', 'end')
        t.insert('end', '  OUTLIER DETECTION  (IQR Method, 1.5×)\n', 'h1')
        t.insert('end', f'  {"─"*60}\n', 'dim')
        num = self.df.select_dtypes(include=[np.number])
        for col in num.columns:
            d = num[col].dropna()
            Q1, Q3 = d.quantile(.25), d.quantile(.75)
            IQR = Q3 - Q1
            lo, hi = Q1 - 1.5*IQR, Q3 + 1.5*IQR
            outs = d[(d < lo) | (d > hi)]
            pct = len(outs)/len(d)*100
            t.insert('end', f'\n  {col}\n', 'h2')
            t.insert('end', f'    Range  : [{lo:.3f}, {hi:.3f}]\n')
            t.insert('end', f'    Outliers: ')
            t.insert('end', f'{len(outs)} ({pct:.1f}%)\n', 'bad' if pct>5 else ('warn' if pct>0 else 'good'))
            if len(outs):
                vals = ', '.join(f'{v:.2f}' for v in sorted(outs.values)[:8])
                t.insert('end', f'    Values : {vals}{"…" if len(outs)>8 else ""}\n', 'dim')
        self._status('Outlier analysis complete')

    def _show_normalized(self):
        if not self._require_data():
            return
        self._push_history()
        ndf = self.df.copy()
        num = ndf.select_dtypes(include=[np.number]).columns
        for c in num:
            mn, mx = ndf[c].min(), ndf[c].max()
            if mx > mn:
                ndf[c] = (ndf[c] - mn) / (mx - mn)
        self.df = ndf
        self.data = ndf.values
        self._display_data()
        self._update_strip()
        self._toast('Numeric columns normalized to [0, 1]', 'ok')
        self._status('Normalized data shown')

    # ── Normality Tests ──────────────────────────────────────────────────────
    def _normality_tests(self):
        if not self._require_data():
            return
        self.notebook.select(self.tab_dist)
        t = self.dist_txt
        t.delete('1.0', 'end')
        t.insert('end', '  NORMALITY TESTS\n', 'h1')
        t.insert('end', f'  {"─"*70}\n', 'dim')
        t.insert('end', '  Tests: Shapiro-Wilk (n≤5000), D\'Agostino-Pearson, Kolmogorov-Smirnov\n\n', 'dim')
        t.insert('end', f'  {"Column":<18} {"Shapiro p":>12} {"D\'Agostino p":>14} {"KS p":>12} {"Normal?"}\n', 'dim')
        t.insert('end', f'  {"─"*70}\n', 'dim')
        num = self.df.select_dtypes(include=[np.number])
        for col in num.columns:
            d = num[col].dropna().values
            try:
                _, sw_p  = shapiro(d[:5000])
            except:
                sw_p = float('nan')
            try:
                _, da_p  = normaltest(d)
            except:
                da_p = float('nan')
            try:
                _, ks_p  = kstest(d, 'norm', args=(d.mean(), d.std()))
            except:
                ks_p = float('nan')
            is_normal = (sw_p > 0.05) and (da_p > 0.05)
            verdict = '✓ Yes' if is_normal else '✕ No'
            tag = 'good' if is_normal else 'bad'
            t.insert('end',
                f'  {col:<18} {sw_p:>12.4f} {da_p:>14.4f} {ks_p:>12.4f}  ')
            t.insert('end', f'{verdict}\n', tag)
        t.insert('end', '\n  α = 0.05. p > 0.05 → fail to reject normality.\n', 'dim')
        self._status('Normality tests run')

    # ── Hypothesis Test ──────────────────────────────────────────────────────
    def _hypothesis_test(self):
        if not self._require_data():
            return
        num_cols = list(self.df.select_dtypes(include=[np.number]).columns)
        if len(num_cols) < 2:
            self._toast('Need ≥ 2 numeric columns', 'warn')
            return

        dlg = tk.Toplevel(self.root)
        dlg.title('Hypothesis Test')
        dlg.configure(bg=COLORS['bg'])
        dlg.geometry('380x280')
        dlg.grab_set()

        tk.Label(dlg, text='Hypothesis Test', bg=COLORS['bg'],
                 fg=COLORS['text_bright'], font=(self.FF_TITLE, 12, 'bold')).pack(pady=(18,8))

        f = tk.Frame(dlg, bg=COLORS['bg'])
        f.pack()
        tk.Label(f, text='Column A:', bg=COLORS['bg'], fg=COLORS['text']).grid(row=0, column=0, padx=8, pady=6, sticky='w')
        v1 = tk.StringVar(value=num_cols[0])
        ttk.Combobox(f, textvariable=v1, values=num_cols, state='readonly', width=18).grid(row=0, column=1)
        tk.Label(f, text='Column B:', bg=COLORS['bg'], fg=COLORS['text']).grid(row=1, column=0, padx=8, pady=6, sticky='w')
        v2 = tk.StringVar(value=num_cols[1] if len(num_cols)>1 else num_cols[0])
        ttk.Combobox(f, textvariable=v2, values=num_cols, state='readonly', width=18).grid(row=1, column=1)
        tk.Label(f, text='Test:', bg=COLORS['bg'], fg=COLORS['text']).grid(row=2, column=0, padx=8, pady=6, sticky='w')
        vt = tk.StringVar(value='t-test (independent)')
        ttk.Combobox(f, textvariable=vt,
                     values=['t-test (independent)', 'Mann-Whitney U', 'Welch t-test'],
                     state='readonly', width=22).grid(row=2, column=1)

        def run():
            a = self.df[v1.get()].dropna().values
            b = self.df[v2.get()].dropna().values
            test = vt.get()
            if test == 't-test (independent)':
                stat, p = stats.ttest_ind(a, b)
                name = "Independent Samples t-test"
            elif test == 'Welch t-test':
                stat, p = stats.ttest_ind(a, b, equal_var=False)
                name = "Welch t-test"
            else:
                stat, p = stats.mannwhitneyu(a, b, alternative='two-sided')
                name = "Mann-Whitney U test"
            dlg.destroy()
            self.notebook.select(self.tab_dist)
            t = self.dist_txt
            t.delete('1.0', 'end')
            t.insert('end', f'  {name.upper()}\n', 'h1')
            t.insert('end', f'  {"─"*50}\n', 'dim')
            t.insert('end', f'  Column A : {v1.get()}  (n={len(a)}, μ={a.mean():.3f})\n')
            t.insert('end', f'  Column B : {v2.get()}  (n={len(b)}, μ={b.mean():.3f})\n\n')
            t.insert('end', f'  Statistic: {stat:.4f}\n')
            t.insert('end', f'  p-value  : {p:.6f}\n\n')
            if p < 0.001:
                sig = '★★★ Highly significant (p < 0.001)'
                tag = 'bad'
            elif p < 0.01:
                sig = '★★ Significant (p < 0.01)'
                tag = 'bad'
            elif p < 0.05:
                sig = '★ Significant (p < 0.05)'
                tag = 'bad'
            else:
                sig = 'Not significant (p ≥ 0.05)'
                tag = 'good'
            t.insert('end', f'  Result   : ', 'dim')
            t.insert('end', f'{sig}\n', tag)
            t.insert('end', f'\n  H₀: No difference between group means\n', 'dim')
            verdict = 'Reject H₀' if p < 0.05 else 'Fail to reject H₀'
            t.insert('end', f'  Decision : {verdict} at α = 0.05\n')
            self._status(f'Hypothesis test: {name}')

        FlatButton(dlg, 'Run Test', run, width=160, height=34,
                   color=COLORS['accent3'], text_color='white',
                   font=(self.FF_BODY, 9, 'bold')).pack(pady=14)

    # ── Group Stats ──────────────────────────────────────────────────────────
    def _group_stats(self):
        if not self._require_data():
            return
        cat_cols = list(self.df.select_dtypes(exclude=[np.number]).columns)
        num_cols = list(self.df.select_dtypes(include=[np.number]).columns)
        if not cat_cols or not num_cols:
            self._toast('Need at least 1 categorical and 1 numeric column', 'warn')
            return

        dlg = tk.Toplevel(self.root)
        dlg.title('Group Statistics')
        dlg.configure(bg=COLORS['bg'])
        dlg.geometry('360x240')
        dlg.grab_set()
        tk.Label(dlg, text='Group By Statistics', bg=COLORS['bg'],
                 fg=COLORS['text_bright'], font=(self.FF_TITLE, 12, 'bold')).pack(pady=(18,8))
        f = tk.Frame(dlg, bg=COLORS['bg'])
        f.pack()
        tk.Label(f, text='Group by:', bg=COLORS['bg'], fg=COLORS['text']).grid(row=0, column=0, padx=8, pady=6, sticky='w')
        vg = tk.StringVar(value=cat_cols[0])
        ttk.Combobox(f, textvariable=vg, values=cat_cols, state='readonly', width=18).grid(row=0, column=1)
        tk.Label(f, text='Metric:', bg=COLORS['bg'], fg=COLORS['text']).grid(row=1, column=0, padx=8, pady=6, sticky='w')
        vm = tk.StringVar(value=num_cols[0])
        ttk.Combobox(f, textvariable=vm, values=num_cols, state='readonly', width=18).grid(row=1, column=1)

        def run():
            grp  = self.df.groupby(vg.get())[vm.get()]
            dlg.destroy()
            self.notebook.select(self.tab_stats)
            t = self.stats_txt
            t.delete('1.0', 'end')
            t.insert('end', f'  GROUP STATISTICS: {vm.get()} by {vg.get()}\n', 'h1')
            t.insert('end', f'  {"─"*60}\n', 'dim')
            t.insert('end', f'  {"Group":<22} {"N":>6} {"Mean":>12} {"Std":>12} {"Median":>12}\n', 'dim')
            for name, g in grp:
                t.insert('end',
                    f'  {str(name):<22} {len(g):>6,} {g.mean():>12.3f} {g.std():>12.3f} {g.median():>12.3f}\n')
            self._status(f'Group stats: {vm.get()} by {vg.get()}')

        FlatButton(dlg, 'Compute', run, width=160, height=34,
                   color=COLORS['accent2'], text_color='white').pack(pady=14)

    # ── Filter ───────────────────────────────────────────────────────────────
    def _filter_dialog(self):
        if not self._require_data():
            return
        dlg = tk.Toplevel(self.root)
        dlg.title('Filter & Query')
        dlg.configure(bg=COLORS['bg'])
        dlg.geometry('480x360')
        dlg.grab_set()
        tk.Label(dlg, text='Filter Data', bg=COLORS['bg'],
                 fg=COLORS['text_bright'], font=(self.FF_TITLE, 12, 'bold')).pack(pady=(18,8))

        # Query mode
        qf = tk.Frame(dlg, bg=COLORS['card'], padx=14, pady=10)
        qf.pack(fill='x', padx=18, pady=4)
        tk.Label(qf, text='Pandas query expression:', bg=COLORS['card'],
                 fg=COLORS['text_dim'], font=(self.FF_BODY, 9)).pack(anchor='w')
        qvar = tk.StringVar()
        ttk.Entry(qf, textvariable=qvar, font=(self.FF_MONO, 10), width=44).pack(fill='x', pady=4)
        tk.Label(qf, text='e.g.  Age > 30  |  Salary >= 60000 & Department == "Sales"',
                 bg=COLORS['card'], fg=COLORS['text_dim'], font=(self.FF_BODY, 8)).pack(anchor='w')

        preview = tk.Label(dlg, text='', bg=COLORS['bg'], fg=COLORS['text_dim'],
                           font=(self.FF_BODY, 9))
        preview.pack(pady=4)

        def check(*_):
            q = qvar.get().strip()
            if q:
                try:
                    r = self.df.query(q)
                    preview.config(text=f'✓  {len(r):,} rows match', fg=COLORS['success'])
                except Exception as e:
                    preview.config(text=f'✕  {e}', fg=COLORS['danger'])
        qvar.trace('w', check)

        def apply():
            try:
                result = self.df.query(qvar.get().strip())
                dlg.destroy()
                self._push_history()
                self.df = result.reset_index(drop=True)
                self.data = self.df.values
                self.column_names = list(self.df.columns)
                self._display_data()
                self._update_strip()
                self._toast(f'{len(result):,} rows after filter', 'ok')
            except Exception as e:
                preview.config(text=f'Error: {e}', fg=COLORS['danger'])

        FlatButton(dlg, 'Apply Filter', apply, width=180, height=34,
                   color=COLORS['accent'], text_color='white').pack(pady=14)

    # ── Undo ─────────────────────────────────────────────────────────────────
    def _undo(self):
        if not self.history:
            self._toast('Nothing to undo', 'warn')
            return
        self.df = self.history.pop()
        self.data = self.df.values
        self.column_names = list(self.df.columns)
        self._display_data()
        self._update_strip()
        self._toast('Undo successful', 'ok')

    # ── Charts ───────────────────────────────────────────────────────────────
    def _clear_viz(self):
        for w in self.tab_viz.winfo_children():
            w.destroy()

    def _embed_fig(self, fig):
        self._clear_viz()
        self.notebook.select(self.tab_viz)
        tf = tk.Frame(self.tab_viz, bg=COLORS['panel'])
        tf.pack(fill='x', padx=6, pady=(6,0))
        toolbar = NavigationToolbar2Tk(FigureCanvasTkAgg(fig, self.tab_viz), tf)
        toolbar.update()

        canvas = FigureCanvasTkAgg(fig, self.tab_viz)
        canvas.draw()

        # Rebuild with toolbar first
        self._clear_viz()
        self.notebook.select(self.tab_viz)
        canvas2 = FigureCanvasTkAgg(fig, self.tab_viz)
        canvas2.draw()
        toolbar2 = NavigationToolbar2Tk(canvas2, self.tab_viz)
        toolbar2.update()
        canvas2.get_tk_widget().pack(fill='both', expand=True)

    def _mpl_style(self, ax, title='', xlabel='', ylabel=''):
        ax.set_facecolor(COLORS['card'])
        ax.set_title(title, color=COLORS['text'], fontsize=11, fontweight='bold', pad=10)
        ax.set_xlabel(xlabel, color=COLORS['text_dim'], fontsize=9)
        ax.set_ylabel(ylabel, color=COLORS['text_dim'], fontsize=9)
        ax.tick_params(colors=COLORS['text_dim'], labelsize=8)
        ax.spines[:].set_color(COLORS['border'])
        ax.grid(True, color=COLORS['border'], alpha=0.5, linewidth=0.6)

    def _plot_histogram(self):
        self._col_dialog('Histogram Column', self._do_histogram)

    def _do_histogram(self, col):
        d = self.df[col].dropna()
        fig, axes = plt.subplots(1, 2, figsize=(11, 5))
        fig.patch.set_facecolor(COLORS['panel'])
        fig.subplots_adjust(wspace=0.35, left=0.08, right=0.96, top=0.88, bottom=0.12)

        ax1, ax2 = axes
        n, bins, patches = ax1.hist(d, bins=25, color=COLORS['chart1'], edgecolor='none', alpha=0.85)
        # color by frequency
        max_n = max(n)
        for patch, height in zip(patches, n):
            patch.set_facecolor(plt.cm.plasma(height/max_n))
        self._mpl_style(ax1, f'Distribution — {col}', col, 'Count')

        # Overlay KDE
        from scipy.stats import gaussian_kde
        kde = gaussian_kde(d)
        xs = np.linspace(d.min(), d.max(), 300)
        ax1_twin = ax1.twinx()
        ax1_twin.plot(xs, kde(xs), color=COLORS['accent4'], linewidth=2, label='KDE')
        ax1_twin.set_ylabel('Density', color=COLORS['text_dim'], fontsize=8)
        ax1_twin.tick_params(colors=COLORS['text_dim'], labelsize=8)
        ax1_twin.set_facecolor(COLORS['card'])
        ax1_twin.spines[:].set_color(COLORS['border'])

        # Box plot
        bp = ax2.boxplot(d, patch_artist=True, vert=True, widths=0.4,
                         boxprops=dict(facecolor=COLORS['chart2'], alpha=0.7, color=COLORS['border_light']),
                         whiskerprops=dict(color=COLORS['text_dim'], linewidth=1.2),
                         capprops=dict(color=COLORS['text_dim']),
                         medianprops=dict(color=COLORS['accent4'], linewidth=2),
                         flierprops=dict(marker='o', markerfacecolor=COLORS['danger'], markersize=4, alpha=0.6))
        self._mpl_style(ax2, f'Box Plot — {col}', '', col)
        ax2.set_xticks([])

        # Stats annotation
        stats_str = (f'n = {len(d):,}\nμ = {d.mean():.3f}\nσ = {d.std():.3f}\n'
                     f'skew = {stats.skew(d):.3f}\nkurt = {stats.kurtosis(d):.3f}')
        ax2.text(0.97, 0.97, stats_str, transform=ax2.transAxes, va='top', ha='right',
                 color=COLORS['text'], fontsize=8, family='monospace',
                 bbox=dict(facecolor=COLORS['bg'], edgecolor=COLORS['border'], alpha=0.8, boxstyle='round,pad=0.5'))

        self._embed_fig(fig)
        self._status(f'Histogram: {col}')

    def _plot_boxplot(self):
        if not self._require_data():
            return
        num = self.df.select_dtypes(include=[np.number])
        if num.empty:
            self._toast('No numeric columns', 'warn')
            return
        n = len(num.columns)
        fig, ax = plt.subplots(figsize=(max(8, n*1.4), 5))
        fig.patch.set_facecolor(COLORS['panel'])
        data = [num[c].dropna().values for c in num.columns]
        palette = [COLORS['chart1'],COLORS['chart2'],COLORS['chart3'],
                   COLORS['chart4'],COLORS['chart5'],COLORS['chart6']]
        bp = ax.boxplot(data, patch_artist=True, labels=num.columns, widths=0.5,
                        whiskerprops=dict(color=COLORS['text_dim']),
                        capprops=dict(color=COLORS['text_dim']),
                        medianprops=dict(color='white', linewidth=2),
                        flierprops=dict(marker='o', markersize=4, alpha=0.5,
                                        markerfacecolor=COLORS['danger']))
        for patch, color in zip(bp['boxes'], palette * (n//len(palette)+1)):
            patch.set_facecolor(color)
            patch.set_alpha(0.75)
        self._mpl_style(ax, 'Box Plot — All Numeric Columns', '', 'Value')
        plt.xticks(rotation=30, ha='right')
        fig.tight_layout()
        self._embed_fig(fig)
        self._status('Box plot displayed')

    def _plot_scatter(self):
        if not self._require_data():
            return
        num_cols = list(self.df.select_dtypes(include=[np.number]).columns)
        if len(num_cols) < 2:
            self._toast('Need ≥ 2 numeric columns', 'warn')
            return
        dlg = tk.Toplevel(self.root)
        dlg.title('Scatter Plot')
        dlg.configure(bg=COLORS['bg'])
        dlg.geometry('360x240')
        dlg.grab_set()
        tk.Label(dlg, text='Scatter Plot', bg=COLORS['bg'],
                 fg=COLORS['text_bright'], font=(self.FF_TITLE, 12, 'bold')).pack(pady=(16,8))
        f = tk.Frame(dlg, bg=COLORS['bg'])
        f.pack()
        vx = tk.StringVar(value=num_cols[0])
        vy = tk.StringVar(value=num_cols[1] if len(num_cols)>1 else num_cols[0])
        tk.Label(f, text='X axis:', bg=COLORS['bg'], fg=COLORS['text']).grid(row=0,column=0,padx=8,pady=6,sticky='w')
        ttk.Combobox(f, textvariable=vx, values=num_cols, state='readonly', width=18).grid(row=0,column=1)
        tk.Label(f, text='Y axis:', bg=COLORS['bg'], fg=COLORS['text']).grid(row=1,column=0,padx=8,pady=6,sticky='w')
        ttk.Combobox(f, textvariable=vy, values=num_cols, state='readonly', width=18).grid(row=1,column=1)

        # Color by categorical?
        cat_cols = ['(none)'] + list(self.df.select_dtypes(exclude=[np.number]).columns)
        vc = tk.StringVar(value='(none)')
        tk.Label(f, text='Color by:', bg=COLORS['bg'], fg=COLORS['text']).grid(row=2,column=0,padx=8,pady=6,sticky='w')
        ttk.Combobox(f, textvariable=vc, values=cat_cols, state='readonly', width=18).grid(row=2,column=1)

        def plot():
            xc, yc = vx.get(), vy.get()
            cc = vc.get()
            dlg.destroy()
            x = self.df[xc].dropna()
            y = self.df[yc][x.index].dropna()
            x = x[y.index]
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            fig.patch.set_facecolor(COLORS['panel'])

            if cc != '(none)' and cc in self.df.columns:
                cats = self.df[cc].unique()
                pal = [COLORS['chart1'],COLORS['chart2'],COLORS['chart3'],
                       COLORS['chart4'],COLORS['chart5'],COLORS['chart6']]
                for i, cat in enumerate(cats):
                    mask = self.df.loc[x.index, cc] == cat
                    ax1.scatter(x[mask], y[mask], color=pal[i%6], alpha=0.65,
                                s=30, label=str(cat), edgecolors='none')
                ax1.legend(fontsize=8, facecolor=COLORS['card'], edgecolor=COLORS['border'],
                           labelcolor=COLORS['text'])
            else:
                corr = np.corrcoef(x, y)[0,1]
                sc = ax1.scatter(x, y, c=np.abs(x - x.mean())/x.std(),
                                 cmap='plasma', alpha=0.65, s=30, edgecolors='none')
                plt.colorbar(sc, ax=ax1, label='Z-score (X)')

            if len(x) > 1:
                z = np.polyfit(x, y, 1)
                xs = np.linspace(x.min(), x.max(), 200)
                ax1.plot(xs, np.poly1d(z)(xs), color=COLORS['accent4'], lw=2, label='Regression')
                ax1.legend(fontsize=8, facecolor=COLORS['card'], edgecolor=COLORS['border'],
                           labelcolor=COLORS['text'])
            self._mpl_style(ax1, f'{yc} vs {xc}', xc, yc)
            corr = self.df[xc].corr(self.df[yc])
            ax1.text(0.04, 0.96, f'r = {corr:.3f}', transform=ax1.transAxes,
                     va='top', color=COLORS['text'], fontsize=9,
                     bbox=dict(facecolor=COLORS['bg'], edgecolor=COLORS['border'], alpha=0.8, boxstyle='round,pad=0.4'))

            # Residual plot
            if len(x) > 1:
                slope, intercept, *_ = stats.linregress(x, y)
                res = y - (slope*x + intercept)
                ax2.scatter(x, res, color=COLORS['chart3'], alpha=0.6, s=25, edgecolors='none')
                ax2.axhline(0, color=COLORS['accent4'], lw=1.5, ls='--')
                self._mpl_style(ax2, 'Residuals', xc, 'Residual')
            fig.tight_layout(pad=1.5)
            self._embed_fig(fig)
            self._status(f'Scatter: {yc} vs {xc}')

        FlatButton(dlg, 'Plot', plot, width=160, height=34,
                   color=COLORS['accent3'], text_color='white').pack(pady=14)

    def _plot_heatmap(self):
        if not self._require_data():
            return
        num = self.df.select_dtypes(include=[np.number])
        if num.shape[1] < 2:
            self._toast('Need ≥ 2 numeric columns', 'warn')
            return
        corr = num.corr().values
        cols = list(num.columns)
        n = len(cols)
        fig, ax = plt.subplots(figsize=(max(6, n*0.8+1), max(5, n*0.7+1)))
        fig.patch.set_facecolor(COLORS['panel'])
        cmap = LinearSegmentedColormap.from_list('custom',
               [COLORS['danger'], COLORS['panel'], COLORS['accent']], N=256)
        im = ax.imshow(corr, cmap=cmap, vmin=-1, vmax=1, aspect='auto')
        plt.colorbar(im, ax=ax, fraction=0.04, pad=0.03, label='Pearson r')
        ax.set_xticks(range(n)); ax.set_xticklabels(cols, rotation=40, ha='right',
                                                      color=COLORS['text'], fontsize=8)
        ax.set_yticks(range(n)); ax.set_yticklabels(cols, color=COLORS['text'], fontsize=8)
        for i in range(n):
            for j in range(n):
                ax.text(j, i, f'{corr[i,j]:.2f}', ha='center', va='center',
                        color='white' if abs(corr[i,j])>0.4 else COLORS['text_dim'], fontsize=7)
        ax.set_facecolor(COLORS['card'])
        ax.set_title('Correlation Heatmap', color=COLORS['text'], fontsize=12, fontweight='bold', pad=12)
        ax.tick_params(colors=COLORS['text_dim'])
        ax.spines[:].set_color(COLORS['border'])
        fig.tight_layout()
        self._embed_fig(fig)
        self._status('Heatmap displayed')

    def _plot_pairplot(self):
        if not self._require_data():
            return
        num = self.df.select_dtypes(include=[np.number])
        if num.shape[1] < 2:
            self._toast('Need ≥ 2 numeric columns', 'warn')
            return
        cols = list(num.columns)[:5]  # cap at 5
        n = len(cols)
        fig, axes = plt.subplots(n, n, figsize=(n*2.5, n*2.2))
        fig.patch.set_facecolor(COLORS['panel'])
        palette = [COLORS['chart1'],COLORS['chart2'],COLORS['chart3'],
                   COLORS['chart4'],COLORS['chart5']]
        for i, c1 in enumerate(cols):
            for j, c2 in enumerate(cols):
                ax = axes[i][j] if n > 1 else axes
                ax.set_facecolor(COLORS['card'])
                ax.tick_params(labelsize=6, colors=COLORS['text_dim'])
                ax.spines[:].set_color(COLORS['border'])
                if i == j:
                    d = num[c1].dropna()
                    ax.hist(d, bins=18, color=palette[i%5], alpha=0.8, edgecolor='none')
                    ax.set_title(c1, fontsize=7, color=COLORS['text'], pad=3)
                else:
                    x = num[c2].dropna()
                    y = num[c1][x.index].dropna()
                    x = x[y.index]
                    ax.scatter(x, y, s=6, alpha=0.5, color=palette[j%5], edgecolors='none')
                if i < n-1: ax.set_xticks([])
                if j > 0:   ax.set_yticks([])
        fig.suptitle('Pair Plot', color=COLORS['text'], fontsize=12, fontweight='bold', y=1.01)
        fig.tight_layout(pad=0.4)
        self._embed_fig(fig)
        self._status('Pair plot displayed')

    def _plot_timeseries(self):
        if not self._require_data():
            return
        num_cols = list(self.df.select_dtypes(include=[np.number]).columns)
        if not num_cols:
            self._toast('No numeric columns', 'warn')
            return
        dlg = tk.Toplevel(self.root)
        dlg.title('Time Series / Line Chart')
        dlg.configure(bg=COLORS['bg'])
        dlg.geometry('360x200')
        dlg.grab_set()
        tk.Label(dlg, text='Line / Time Series', bg=COLORS['bg'],
                 fg=COLORS['text_bright'], font=(self.FF_TITLE, 12, 'bold')).pack(pady=(16,8))
        f = tk.Frame(dlg, bg=COLORS['bg'])
        f.pack()
        tk.Label(f, text='Column:', bg=COLORS['bg'], fg=COLORS['text']).grid(row=0,column=0,padx=8,pady=6,sticky='w')
        v = tk.StringVar(value=num_cols[0])
        ttk.Combobox(f, textvariable=v, values=num_cols, state='readonly', width=18).grid(row=0,column=1)

        def plot():
            col = v.get()
            dlg.destroy()
            d = self.df[col].values
            fig, ax = plt.subplots(figsize=(11, 4))
            fig.patch.set_facecolor(COLORS['panel'])
            ax.plot(d, color=COLORS['chart1'], lw=1.5, alpha=0.9)
            ax.fill_between(range(len(d)), d, alpha=0.12, color=COLORS['chart1'])
            # Rolling mean
            rm = pd.Series(d).rolling(max(2, len(d)//20)).mean()
            ax.plot(rm, color=COLORS['accent4'], lw=2, ls='--', label=f'Rolling avg ({len(d)//20})')
            ax.legend(fontsize=8, facecolor=COLORS['card'], edgecolor=COLORS['border'],
                      labelcolor=COLORS['text'])
            self._mpl_style(ax, f'Time Series — {col}', 'Index', col)
            fig.tight_layout()
            self._embed_fig(fig)
            self._status(f'Time series: {col}')

        FlatButton(dlg, 'Plot', plot, width=160, height=34,
                   color=COLORS['accent3'], text_color='white').pack(pady=14)

    # ── Auto Insights ────────────────────────────────────────────────────────
    def _auto_insights(self):
        for w in self.insight_frame.winfo_children():
            w.destroy()
        if self.df is None:
            return
        self.notebook.select(self.tab_insight)

        def card(title, body, color):
            f = tk.Frame(self.insight_frame, bg=COLORS['card'],
                         highlightthickness=1, highlightbackground=color)
            f.pack(fill='x', padx=14, pady=6)
            hdr = tk.Frame(f, bg=color)
            hdr.pack(fill='x')
            tk.Label(hdr, text=title, bg=color, fg='white',
                     font=(self.FF_BODY, 9, 'bold'), padx=12, pady=5).pack(anchor='w')
            tk.Label(f, text=body, bg=COLORS['card'], fg=COLORS['text'],
                     font=(self.FF_BODY, 9), anchor='w', justify='left',
                     wraplength=700, padx=12, pady=8).pack(anchor='w', fill='x')

        card('📋 Dataset Overview',
             f'Loaded "{self.filename}" — {len(self.df):,} rows × {len(self.df.columns)} columns  |  '
             f'{self.df.memory_usage(deep=True).sum()//1024} KB in memory.',
             COLORS['accent'])

        miss = self.df.isnull().sum()
        if miss.sum() > 0:
            msg = '  '.join(f'{c}: {v}' for c, v in miss[miss>0].items())
            card('⚠  Missing Values Detected', msg, COLORS['warning'])
        else:
            card('✓  No Missing Values', 'Dataset is complete — no null entries found.', COLORS['success'])

        num = self.df.select_dtypes(include=[np.number])
        if num.shape[1] >= 2:
            corr = num.corr()
            pairs = []
            cols = list(corr.columns)
            for i in range(len(cols)):
                for j in range(i+1, len(cols)):
                    pairs.append((abs(corr.iloc[i,j]), cols[i], cols[j], corr.iloc[i,j]))
            pairs.sort(reverse=True)
            if pairs:
                top = pairs[:3]
                msg = '\n'.join(f'  • {a} ↔ {b}: r = {v:+.3f}' for _, a, b, v in top)
                card('🔗  Strongest Correlations', msg, COLORS['accent2'])

        # Skewness warnings
        skewed = []
        for col in num.columns:
            s = stats.skew(num[col].dropna())
            if abs(s) > 1:
                skewed.append(f'{col} (skew={s:.2f})')
        if skewed:
            card('📐  Skewed Distributions',
                 'The following columns show high skewness (|skew| > 1):\n  ' + ',  '.join(skewed),
                 COLORS['warning'])

        # Outliers
        out_info = []
        for col in num.columns:
            d = num[col].dropna()
            Q1, Q3 = d.quantile(.25), d.quantile(.75)
            IQR = Q3 - Q1
            n_out = len(d[(d < Q1-1.5*IQR) | (d > Q3+1.5*IQR)])
            if n_out > 0:
                out_info.append(f'{col}: {n_out} outlier(s)')
        if out_info:
            card('⚡  Outliers Detected', '\n  '.join([''] + out_info), COLORS['danger'])

        card('💡  Recommended Actions',
             '  1. Review missing values and consider imputation or removal.\n'
             '  2. Check skewed columns — consider log/sqrt transforms.\n'
             '  3. Investigate high-correlation pairs for multicollinearity.\n'
             '  4. Run Normality Tests before applying parametric methods.',
             COLORS['info'])

    # ── Export / Report ──────────────────────────────────────────────────────
    def _export_data(self):
        if not self._require_data():
            return
        fn = filedialog.asksaveasfilename(title='Export Data',
             defaultextension='.csv',
             filetypes=[('CSV','*.csv'),('Excel','*.xlsx'),('All','*.*')])
        if not fn:
            return
        try:
            if fn.endswith('.xlsx'):
                self.df.to_excel(fn, index=False)
            else:
                self.df.to_csv(fn, index=False)
            self._toast(f'Exported to {os.path.basename(fn)}', 'ok')
            self._status(f'Data exported: {fn}')
        except Exception as e:
            self._toast(f'Export error: {e}', 'err')

    def _generate_report(self):
        if not self._require_data():
            return
        fn = filedialog.asksaveasfilename(title='Save Report',
             defaultextension='.txt',
             filetypes=[('Text','*.txt'),('All','*.*')])
        if not fn:
            return
        try:
            with open(fn, 'w') as f:
                sep = '═'*72
                f.write(sep + '\n')
                f.write('  STATISTICAL ANALYSIS REPORT — StatLab Pro v3.0\n')
                f.write(sep + '\n\n')
                f.write(f'  Generated : {datetime.now().strftime("%Y-%m-%d  %H:%M:%S")}\n')
                f.write(f'  Dataset   : {self.filename or "Sample Data"}\n')
                f.write(f'  Rows      : {len(self.df):,}\n')
                f.write(f'  Columns   : {len(self.df.columns)}\n')
                f.write(f'  Missing   : {int(self.df.isnull().sum().sum())}\n\n')
                f.write('─'*72 + '\n')
                f.write('  COLUMN SUMMARY\n')
                f.write('─'*72 + '\n')
                num = self.df.select_dtypes(include=[np.number])
                for col in num.columns:
                    d = num[col].dropna()
                    f.write(f'\n  {col}:\n')
                    f.write(f'    n={len(d):,}  mean={d.mean():.4f}  std={d.std():.4f}'
                            f'  min={d.min():.4f}  max={d.max():.4f}\n')
                    f.write(f'    skew={stats.skew(d):.4f}  kurt={stats.kurtosis(d):.4f}\n')
                f.write('\n' + '─'*72 + '\n')
                f.write('  CORRELATION MATRIX\n')
                f.write('─'*72 + '\n')
                if num.shape[1] >= 2:
                    corr = num.corr()
                    cols = list(corr.columns)
                    f.write('  ' + ''.join(f'{c:>14}' for c in [''] + cols) + '\n')
                    for row in cols:
                        f.write('  ' + f'{row:<14}' + ''.join(f'{corr.loc[row,c]:>14.4f}' for c in cols) + '\n')
                f.write('\n' + sep + '\n')
                f.write('  END OF REPORT\n')
                f.write(sep + '\n')
            self._toast(f'Report saved: {os.path.basename(fn)}', 'ok')
            self._status(f'Report saved: {fn}')
        except Exception as e:
            self._toast(f'Report error: {e}', 'err')

    # ── Welcome ──────────────────────────────────────────────────────────────
    def _show_welcome(self):
        for w in self.insight_frame.winfo_children():
            w.destroy()

        hero = tk.Frame(self.insight_frame, bg=COLORS['panel'])
        hero.pack(fill='x', padx=14, pady=20)
        tk.Label(hero, text='StatLab Pro', bg=COLORS['panel'],
                 fg=COLORS['accent'], font=(self.FF_TITLE, 28, 'bold')).pack()
        tk.Label(hero, text='Professional Statistical Data Analyzer  ·  v3.0',
                 bg=COLORS['panel'], fg=COLORS['text_dim'],
                 font=(self.FF_BODY, 10)).pack(pady=4)

        grid = tk.Frame(self.insight_frame, bg=COLORS['panel'])
        grid.pack(fill='x', padx=14, pady=8)
        features = [
            ('📁', 'CSV & Excel Import', 'Load datasets with automatic type detection'),
            ('📊', 'Full Statistics',     'Summaries, correlations, percentiles, CV'),
            ('🔬', 'Distribution Tests',  'Shapiro-Wilk, D\'Agostino, KS normality'),
            ('H₀', 'Hypothesis Testing',  't-test, Welch, Mann-Whitney U'),
            ('📈', '6 Chart Types',       'Histogram, Box, Scatter, Heatmap, Pair, Time Series'),
            ('⊕', 'Group Analysis',       'Statistics segmented by categorical columns'),
            ('⚡', 'Outlier Detection',    'IQR-based outlier identification & reporting'),
            ('↺', 'Undo Stack',           'Revert any transformation or filter'),
        ]
        for i, (icon, title, desc) in enumerate(features):
            c = tk.Frame(grid, bg=COLORS['card'],
                         highlightthickness=1, highlightbackground=COLORS['border'])
            c.grid(row=i//2, column=i%2, padx=6, pady=6, sticky='nsew')
            tk.Label(c, text=icon, bg=COLORS['card'], fg=COLORS['accent'],
                     font=(self.FF_TITLE, 18)).pack(anchor='w', padx=14, pady=(12,0))
            tk.Label(c, text=title, bg=COLORS['card'], fg=COLORS['text_bright'],
                     font=(self.FF_BODY, 10, 'bold')).pack(anchor='w', padx=14)
            tk.Label(c, text=desc, bg=COLORS['card'], fg=COLORS['text_dim'],
                     font=(self.FF_BODY, 9), wraplength=280).pack(anchor='w', padx=14, pady=(2,12))
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        tip = tk.Label(self.insight_frame,
                       text='→  Click "Sample Dataset" in the sidebar to get started instantly.',
                       bg=COLORS['panel'], fg=COLORS['accent3'],
                       font=(self.FF_BODY, 10, 'italic'))
        tip.pack(pady=(16,0))
        self.notebook.select(self.tab_insight)

    # ── Clear ─────────────────────────────────────────────────────────────────
    def _clear_display(self):
        self.tree.delete(*self.tree.get_children())
        self.stats_txt.delete('1.0', 'end')
        self.dist_txt.delete('1.0', 'end')
        self._clear_viz()
        for w in self.insight_frame.winfo_children():
            w.destroy()
        self._show_welcome()
        self._status('Display cleared')


# ─── Entry Point ──────────────────────────────────────────────────────────────
def main():
    root = tk.Tk()
    root.title('StatLab')
    try:
        root.tk.call('tk', 'scaling', 1.3)
    except:
        pass
    app = StatisticsGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()