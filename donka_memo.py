"""
돈카 타건 연습 - 메모장 모양 버전
  겉모양은 Windows 메모장과 같습니다.
  돈(D): 왼손 f / 오른손 j
  카(K): 왼손 d / 오른손 k
  묶음 길이는 1~8타 랜덤, 표시된 키를 정확히 쳐야 정답
  종료: Esc 또는 q
"""
import random
import time
import tkinter as tk

MIN_LEN, MAX_LEN = 1, 8   # 묶음 길이 랜덤 범위
GROUPS_PER_LINE = 5
KEY = {"D": ("f", "j"), "K": ("d", "k")}  # (왼손, 오른손)
FONT = ("Consolas", 11)
TITLE = "無題 - メモ帳"
DON_COLOR = "#E8908A"  # 파스텔 빨강
KA_COLOR = "#7FB3D5"   # 파스텔 파랑
DOT = "•"               # D/K 대신 표시할 점 (색으로 구분)
GAP = "   "


class Game:
    """터미널 버전과 같은 로직"""
    def __init__(self, mn=MIN_LEN, mx=MAX_LEN):
        self.mn, self.mx = mn, mx
        self.hand = 0
        self.hits = self.misses = self.combo = self.best = 0
        self.times = []
        self.msg = ""
        self.new_line()

    def new_line(self):
        self.line = []
        for g in range(GROUPS_PER_LINE):
            if g:
                self.line.append(None)
            for _ in range(random.randint(self.mn, self.mx)):
                t = random.choice("DK")
                h = self.hand % 2
                self.line.append((t, KEY[t][h], h))
                self.hand += 1
        self.pos = self._next(0)

    def _next(self, i):
        while i < len(self.line) and self.line[i] is None:
            i += 1
        return i

    def press(self, k):
        t, want, _ = self.line[self.pos]
        if k == want:
            self.hits += 1
            self.combo += 1
            self.best = max(self.best, self.combo)
            self.times.append(time.time())
            self.msg = f"{self.combo} COMBO!" if self.combo % 50 == 0 else ""
            self.pos = self._next(self.pos + 1)
            if self.pos >= len(self.line):
                self.new_line()
            return True
        self.misses += 1
        self.combo = 0
        self.msg = "HAND ORDER!" if k in KEY[t] else "MISS"
        return False

    def spm(self):
        r = self.times[-20:]
        if len(r) < 2 or r[-1] == r[0]:
            return 0
        return round((len(r) - 1) / (r[-1] - r[0]) * 60)

    def acc(self):
        total = self.hits + self.misses
        return round(self.hits / total * 100) if total else 100


class Memo:
    def __init__(self, root):
        self.root = root
        root.title(TITLE)
        root.geometry("820x520")
        self.build_menu()
        self.build_status()
        self.build_text()
        self.reset()

    # ---------- 겉모양 ----------
    def build_menu(self):
        m = tk.Menu(self.root)
        f = tk.Menu(m, tearoff=0)
        f.add_command(label="新規(N)", accelerator="Ctrl+N", command=self.reset)
        f.add_command(label="新しいウィンドウ(W)", accelerator="Ctrl+Shift+N")
        f.add_command(label="開く(O)...", accelerator="Ctrl+O")
        f.add_command(label="上書き保存(S)", accelerator="Ctrl+S")
        f.add_command(label="名前を付けて保存(A)...", accelerator="Ctrl+Shift+S")
        f.add_separator()
        f.add_command(label="ページ設定(U)...")
        f.add_command(label="印刷(P)...", accelerator="Ctrl+P")
        f.add_separator()
        f.add_command(label="メモ帳の終了(X)", command=self.root.destroy)
        m.add_cascade(label="ファイル(F)", menu=f)

        e = tk.Menu(m, tearoff=0)
        for item in [("元に戻す(U)", "Ctrl+Z"), None, ("切り取り(T)", "Ctrl+X"),
                     ("コピー(C)", "Ctrl+C"), ("貼り付け(P)", "Ctrl+V"), ("削除(L)", "Del"),
                     None, ("検索(F)...", "Ctrl+F"), ("置換(R)...", "Ctrl+H"),
                     None, ("すべて選択(A)", "Ctrl+A"), ("日付と時刻(D)", "F5")]:
            if item is None:
                e.add_separator()
            else:
                e.add_command(label=item[0], accelerator=item[1])
        m.add_cascade(label="編集(E)", menu=e)

        o = tk.Menu(m, tearoff=0)
        o.add_checkbutton(label="右端で折り返す(W)")
        o.add_command(label="フォント(F)...")
        m.add_cascade(label="書式(O)", menu=o)

        v = tk.Menu(m, tearoff=0)
        v.add_command(label="ズーム(Z)")
        self.status_on = tk.BooleanVar(value=True)
        v.add_checkbutton(label="ステータス バー(S)", variable=self.status_on, command=self.toggle_status)
        m.add_cascade(label="表示(V)", menu=v)

        h = tk.Menu(m, tearoff=0)
        h.add_command(label="ヘルプの表示(H)")
        h.add_command(label="フィードバックの送信(F)")
        h.add_separator()
        h.add_command(label="バージョン情報(A)")
        m.add_cascade(label="ヘルプ(H)", menu=h)
        self.root.config(menu=m)

    def build_status(self):
        self.status = tk.Frame(self.root, bg="#f0f0f0", height=22)
        self.status.pack(side="bottom", fill="x")
        tk.Frame(self.status, bg="#d9d9d9", height=1).pack(side="top", fill="x")
        self.cells = {}
        for name, width in [("enc", 16), ("eol", 16), ("zoom", 7), ("pos", 20)]:
            cell = tk.Label(self.status, text="", bg="#f0f0f0", anchor="w",
                            width=width, font=("Segoe UI", 9), padx=6)
            cell.pack(side="right")
            tk.Frame(self.status, bg="#d9d9d9", width=1).pack(side="right", fill="y", pady=2)
            self.cells[name] = cell
        self.cells["enc"].config(text="UTF-8")
        self.cells["eol"].config(text="Windows (CRLF)")

    def toggle_status(self):
        if self.status_on.get():
            self.status.pack(side="bottom", fill="x", before=self.frame)
        else:
            self.status.pack_forget()

    def build_text(self):
        self.frame = tk.Frame(self.root)
        self.frame.pack(fill="both", expand=True)
        sy = tk.Scrollbar(self.frame, orient="vertical")
        sx = tk.Scrollbar(self.frame, orient="horizontal")
        self.text = tk.Text(self.frame, font=FONT, wrap="none", undo=False,
                            relief="flat", borderwidth=0, padx=4, pady=2,
                            insertwidth=1, insertofftime=530, insertontime=530,
                            selectbackground="#0078d7", selectforeground="white",
                            yscrollcommand=sy.set, xscrollcommand=sx.set)
        sy.config(command=self.text.yview)
        sx.config(command=self.text.xview)
        sy.pack(side="right", fill="y")
        sx.pack(side="bottom", fill="x")
        self.text.pack(side="left", fill="both", expand=True)

        self.text.bind("<Control-n>", lambda e: (self.reset(), "break")[1])
        self.text.bind("<Control-N>", lambda e: (self.reset(), "break")[1])
        self.text.bind("<Key>", self.on_key)
        # 클릭으로 커서가 움직이지 않게
        for ev in ("<Button-1>", "<B1-Motion>", "<Double-Button-1>", "<Triple-Button-1>"):
            self.text.bind(ev, lambda e: (self.text.focus_set(), "break")[1])
        self.text.tag_config("done", foreground="#a0a0a0")
        self.text.tag_config("D", foreground=DON_COLOR)
        self.text.tag_config("K", foreground=KA_COLOR)
        self.text.tag_raise("done")  # 지나간 노트는 회색이 우선
        self.text.focus_set()

    # ---------- 연습 로직 (터미널 버전과 동일) ----------
    def reset(self):
        self.game = Game()
        self.root.title(TITLE)
        self.draw()

    def on_key(self, e):
        # Windows 에서 0x0008 은 NumLock 이므로 보지 않음. Alt 는 0x20000
        if e.keysym in ("Alt_L", "Alt_R") or e.state & 0x20000:
            return None  # Alt 는 메뉴용으로 통과
        ks = e.keysym.lower() if len(e.keysym) == 1 else ""
        ch = ks or (e.char or "").lower()
        if e.keysym == "Escape" or ch == "q":
            self.root.destroy()
            return "break"
        if ch and ch in "fdjk":
            self.game.press(ch)
            if self.game.hits == 1:
                self.root.title("*" + TITLE)
            self.draw()
        return "break"

    def draw(self):
        g = self.game
        pat, mark = "", ""
        cur_col = 0
        for i, n in enumerate(g.line):
            if n is None:
                pat += GAP; mark += GAP
                continue
            if i == g.pos:
                cur_col = 2 + len(pat)
            pat += n[0]  # 색 지정을 위해 내부적으로는 D/K 로 기록
            mark += "^" if i == g.pos else " "
        lines = ["  " + pat, "  " + mark]
        t = self.text
        t.delete("1.0", "end")
        shown = [l.replace("D", DOT).replace("K", DOT) for l in lines]
        t.insert("1.0", "\n".join(shown))
        for i, c in enumerate(pat):
            if c in "DK":
                t.tag_add(c, f"1.{2 + i}", f"1.{3 + i}")
        t.tag_add("done", "1.2", f"1.{cur_col}")  # 지나간 노트는 회색
        t.mark_set("insert", f"1.{cur_col}")
        self.cells["pos"].config(text=f"行 1、列 {cur_col + 1}")
        self.cells["zoom"].config(text="100%")


def disable_ime(root, widget):
    try:
        import ctypes
        imm = ctypes.windll.imm32
        user = ctypes.windll.user32
        imm.ImmAssociateContext.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        imm.ImmAssociateContext.restype = ctypes.c_void_p
        user.GetParent.argtypes = [ctypes.c_void_p]
        user.GetParent.restype = ctypes.c_void_p
        for hwnd in (widget.winfo_id(), root.winfo_id(), user.GetParent(root.winfo_id())):
            if hwnd:
                imm.ImmAssociateContext(hwnd, None)
    except Exception:
        pass  # Windows 가 아니면 무시


def set_app_id():
    # 작업 표시줄에서 Python 과 따로 묶이게 해서 창 아이콘이 그대로 보이도록 함
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Memo.Notepad.Text")
    except Exception:
        pass


def set_notepad_icon(root):
    # Windows 의 notepad.exe 에서 아이콘을 꺼내 제목 표시줄과 작업 표시줄에 적용
    try:
        import ctypes
        import os
        shell32, user32 = ctypes.windll.shell32, ctypes.windll.user32
        shell32.ExtractIconExW.argtypes = [ctypes.c_wchar_p, ctypes.c_int,
                                           ctypes.POINTER(ctypes.c_void_p),
                                           ctypes.POINTER(ctypes.c_void_p), ctypes.c_uint]
        user32.SendMessageW.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p]
        user32.SendMessageW.restype = ctypes.c_void_p
        win = os.environ.get("SystemRoot", r"C:\Windows")
        for path in (os.path.join(win, "System32", "notepad.exe"), os.path.join(win, "notepad.exe")):
            if not os.path.exists(path):
                continue
            big, small = ctypes.c_void_p(), ctypes.c_void_p()
            if shell32.ExtractIconExW(path, 0, ctypes.byref(big), ctypes.byref(small), 1) and big.value:
                hwnd = int(root.wm_frame(), 16)
                user32.SendMessageW(hwnd, 0x0080, 0, small.value or big.value)  # WM_SETICON, ICON_SMALL
                user32.SendMessageW(hwnd, 0x0080, 1, big.value)                 # WM_SETICON, ICON_BIG
                root._notepad_icons = (big, small)  # 핸들 유지
                return
    except Exception:
        pass


if __name__ == "__main__":
    set_app_id()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)  # 고해상도 화면에서 흐릿하지 않게
    except Exception:
        pass
    root = tk.Tk()
    app = Memo(root)
    root.update()
    set_notepad_icon(root)
    disable_ime(root, app.text)  # 일본어 IME 가 켜져 있어도 f/d/j/k 가 바로 입력되도록
    root.mainloop()
