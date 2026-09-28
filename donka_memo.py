"""
돈카 타건 연습 - 메모장 모양 버전
  겉모양은 Windows 메모장과 같습니다.
  돈(D): 왼손 f / 오른손 j
  카(K): 왼손 d / 오른손 k
  표시된 키를 정확히 쳐야 정답, 지금 칠 손(L/R)은 상태 표시줄에 표시
  モード(M) 메뉴
    ランダム: 묶음 길이 1~8타, 돈/카 랜덤
    練習: 태고의 달인 보면에 자주 나오는 배치를 난이도별로 출제
    音符を流す: 끄면 정지 모드. 맨 왼쪽 음표를 맞게 치면 사라지고 나머지가 왼쪽으로 당겨짐
                켜면 이동 모드. 음표가 BPM 에 맞춰 왼쪽으로 흘러가고 판정 원에서 타이밍 판정 (良/可/不可)
  확대/축소: 表示(V) > ズーム(Z), Ctrl + +/-/0, Ctrl + 휠
  종료: Esc 또는 q
"""
import random
import time
import tkinter as tk
import tkinter.font as tkfont
import tkinter.simpledialog as simpledialog

MIN_LEN, MAX_LEN = 1, 8   # 랜덤 모드 묶음 길이 범위
GROUPS_PER_LINE = 5
KEY = {"D": ("f", "j"), "K": ("d", "k")}  # (왼손, 오른손)
HAND_OF = {k: h for keys in KEY.values() for h, k in enumerate(keys)}  # 키 -> 손 (0=왼손, 1=오른손)
FONT_FAMILY, FONT_SIZE = "Consolas", 11
ZOOM_MIN, ZOOM_MAX, ZOOM_STEP = 10, 500, 10  # 메모장과 같은 10% 단위
# Windows 가상 키 코드. JIS 배열의 ;+ / -= 키, US 배열의 =+ / -_ 키, 텐키
ZOOM_IN_KEYS = (0xBB, 0x6B)
ZOOM_OUT_KEYS = (0xBD, 0x6D)
ZOOM_RESET_KEYS = (0x30, 0x60)
TITLE = "無題 - メモ帳"
DON_COLOR = "#E8908A"  # 파스텔 빨강
KA_COLOR = "#7FB3D5"   # 파스텔 파랑
DOT = "•"               # D/K 대신 표시할 점 (색으로 구분)
GAP = "   "

# 이동 모드. 실제 게임처럼 흐르는 속도는 BPM 에 비례하고 16분 한 칸의 간격은 BPM 과 상관없이 같음
BPM_PRESETS = (60, 80, 100, 120, 140, 160, 180, 200, 220, 240)
BPM_MIN, BPM_MAX, BPM_DEFAULT = 30, 400, 120
LEAD_IN = 2.0   # 시작하고 첫 노트가 판정 위치에 올 때까지(초)
FRAME_MS = 10   # 화면 갱신 간격
RING_COLOR, RING_FILL = "#a0a0a0", "#ececec"  # 판정 틀 테두리, 안쪽
DOT_CY = 0.545  # 점(•) 글자의 세로 가운데. 줄 높이에 대한 비율 (Consolas 로 확대 100~300% 에서 잰 값)
# 판정 폭(초): 良, 可, 不可. 太鼓の達人 譜面とかWiki「基本システム」의 표. 랜덤은 おに 기준
JUDGE = {"easy": (0.041708, 0.108442, 0.125125), "normal": (0.041708, 0.108442, 0.125125),
         "hard": (0.025025, 0.075075, 0.108442), "oni": (0.025025, 0.075075, 0.108442)}
HIT = ("良", "可")

# 연습 모드에서 난이도별로 자주 나오는 배치. (배치, 가중치), 가중치가 클수록 자주 나옴
#   D=돈, K=카, 공백=한 칸 쉼. 16분을 한 칸으로 보고 붙어 있으면 16분, 한 칸 띄우면 8분,
#   묶음 사이(GAP)는 4분 간격. 출처: 太鼓の達人 譜面とかWiki 용어집·複合パターン 등 (README 참고)
PATTERNS = {
    # かんたん ★1~5: 2분·4분 음표 중심에 가끔 단색 8분. 8분 복합도 거의 없음
    "easy": [
        ("D", 10), ("K", 4),                        # ドン / カッ
        ("D D", 3), ("K K", 1), ("D D D", 1),       # 단색 8분
    ],
    # ふつう ★1~7: 8분 음표와 8분 복합이 중심. 16분은 가끔 단발로, 쉬운 배색만
    "normal": [
        ("D", 6), ("K", 3),
        ("D D", 4), ("K K", 2), ("D D D", 3),       # 단색 8분
        ("D K", 3), ("K D", 2), ("D D K", 3), ("K K D", 2), ("D K D", 2),
        ("D K K", 1), ("K D D", 1), ("D D D K", 2), ("D K D K", 1), ("D D K K", 1),  # 8분 복합
        ("DD", 1), ("DDD", 1),                      # 단발 16분 ドコ / ドコドン
    ],
    # むずかしい ★1~8: 16분(★4~)과 8분 긴 복합. 복합보다 단색 16분·쉬운 복합을 물량으로
    "hard": [
        ("D", 3), ("K", 2),
        ("D D", 2), ("D K", 2), ("D D K", 2), ("K K D", 1), ("D K D", 1),
        ("D K D K", 2), ("D D K K", 1), ("D D K D D K", 1), ("K K D K K D", 1),  # 8분 긴 복합
        ("DD", 2), ("DDD", 6), ("KKK", 2), ("DDDD", 1), ("DDDDD", 3),       # 단색 16분 ドコドン, ドコドコドン
        ("DDK", 3), ("KKD", 3), ("DKD", 1), ("DK", 1), ("KD", 1),           # 쉬운 16분 복합 (★5~)
    ],
    # おに ★1~10 (대부분 ★6~): 16분 복합이 중심, ★7~ 24분, ★9~ 긴 복합
    # 2~4타 복합의 가중치는 위키의 곡별 최다 출현 횟수를 참고
    "oni": [
        ("D", 2), ("K", 1),
        ("DK", 2), ("KD", 2),
        ("DDD", 4), ("KKK", 2), ("DDK", 5), ("KKD", 5),                     # 3연타 8종
        ("DKD", 4), ("KDD", 3), ("DKK", 3), ("KDK", 3),
        ("DDKD", 3), ("KDDK", 2), ("DDKK", 2), ("DKDD", 2), ("DKKD", 2),    # 4연타 복합
        ("KKDD", 2), ("KKDK", 2), ("KKKD", 2), ("DDDK", 3),                 # ドドドカ 는 24분에도 많음
        ("KDDD", 1), ("DKDK", 1), ("DKKK", 1), ("KDKD", 1), ("KDKK", 1),
        ("DDDDD", 3), ("DKDKD", 2), ("DDKDD", 2), ("KDKKD", 1), ("DKDDK", 1),  # 5연타
        ("DDDD", 1), ("KKKK", 1), ("DDDDDDD", 1),                           # 단색 연타
        ("KKDKKDKKD", 1), ("DDDKDDDK", 1), ("DDKKDDKK", 1),                 # 긴 복합: 3타·4타 단위, 2타형
        ("DKDKDKDK", 1), ("DKKDKKDK", 1), ("DDDKKKDDD", 1),                 # ドカドカ, ドカカ 반복, 3-3
    ],
}
LEVELS = [("easy", "かんたん(E)"), ("normal", "ふつう(N)"),
          ("hard", "むずかしい(H)"), ("oni", "おに(O)")]


class Game:
    """정지 모드. level 이 None 이면 랜덤, 아니면 PATTERNS 의 난이도로 출제
    line 은 지금 칠 노트로 시작하는 끝없는 줄. 친 노트는 앞에서 빠지고 뒤에 새 묶음이 붙음"""
    def __init__(self, level=None, mn=MIN_LEN, mx=MAX_LEN):
        self.level = level
        self.mn, self.mx = mn, mx
        self.hand = 0
        self.hits = self.misses = self.combo = self.best = 0
        self.times = []
        self.msg = ""
        self.line = self.make_line()

    def make_line(self):
        # 노트 (종류, 키, 손) 와 간격 문자열이 섞인 GROUPS_PER_LINE 묶음
        line = []
        for g in range(GROUPS_PER_LINE):
            if g:
                line.append(GAP)
            for t in self.group():
                if t == " ":  # 묶음 안의 한 칸 쉼. 손 순서는 그대로 이어짐
                    line.append(t)
                    continue
                h = self.hand % 2
                line.append((t, KEY[t][h], h))
                self.hand += 1
        return line

    def fill(self, cells):
        """줄이 cells 칸 이상이 되도록 뒤에 이어 붙임. 이어지는 곳도 묶음 사이처럼 GAP 만큼 띄움"""
        while sum(len(n) if isinstance(n, str) else 1 for n in self.line) < cells:
            self.line += [GAP] + self.make_line()

    def group(self):
        if self.level is None:
            return [random.choice("DK") for _ in range(random.randint(self.mn, self.mx))]
        pats, weights = zip(*PATTERNS[self.level])
        return random.choices(pats, weights)[0]

    def _next(self, i):
        while i < len(self.line) and isinstance(self.line[i], str):
            i += 1
        return i

    def press(self, k):
        t, want, _ = self.line[0]
        if k == want:
            self.hits += 1
            self.combo += 1
            self.best = max(self.best, self.combo)
            self.times.append(time.time())
            self.msg = f"{self.combo} COMBO!" if self.combo % 50 == 0 else ""
            if self._next(1) >= len(self.line):  # 뒤에 노트가 없으면 먼저 이어 붙임
                self.line += [GAP] + self.make_line()
            del self.line[:self._next(1)]  # 친 노트와 그 뒤 간격을 빼서 다음 노트가 맨 앞으로
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


class Note:
    """이동 모드의 노트 하나"""
    def __init__(self, at, t):
        self.at, self.t = at, t  # 판정 위치에 오는 시각(초), 종류(D/K)
        self.res = None   # 판정. 아직이면 None
        self.item = None  # 캔버스 아이템


class Flow:
    """이동 모드. 정지 모드와 같은 방법으로 만든 배치를 16분 = 한 칸 간격으로 흘려보내고 타이밍으로 판정
    손은 노트마다 미리 정하지 않고, 판정과 상관없이 방금 누른 손의 반대가 다음 손.
    누르지 않고 흘려보낸 노트로는 바뀌지 않으므로 가만히 있으면 처음의 왼손 그대로"""
    def __init__(self, level=None, bpm=BPM_DEFAULT):
        self.src = Game(level)      # 배치는 정지 모드와 똑같이 만듦
        self.step = 60 / bpm / 4    # 16분 한 칸의 시간(초)
        self.good, self.ok, self.bad = JUDGE.get(level, JUDGE["oni"])
        self.notes = []             # 아직 화면에 있는 노트 (시각 순)
        self.next = 0               # 아직 판정 안 된 첫 노트의 번호
        self.end = LEAD_IN          # 다음 칸의 시각
        self.hand = 0               # 다음에 칠 손 (0=왼손, 1=오른손)
        self.hits = self.misses = self.combo = self.best = 0

    def fill(self, until):
        """until 초까지 올 노트를 만든다. 이어지는 곳도 묶음 사이처럼 GAP 만큼 띄움"""
        while self.end < until:
            for n in self.src.make_line():
                if isinstance(n, str):
                    self.end += len(n) * self.step
                else:
                    self.notes.append(Note(self.end, n[0]))
                    self.end += self.step
            self.end += len(GAP) * self.step

    def prune(self, before):
        """판정이 끝났고 before 초보다 앞선 노트를 빼서 돌려준다"""
        i = 0
        while i < self.next and self.notes[i].at < before:
            i += 1
        gone, self.notes = self.notes[:i], self.notes[i:]
        self.next -= i
        return gone

    def upcoming(self):
        return self.notes[self.next] if self.next < len(self.notes) else None

    def expire(self, now):
        """판정 폭을 지나친 노트는 不可"""
        while self.next < len(self.notes) and now > self.notes[self.next].at + self.bad:
            self.judge("不可")

    def press(self, k, now):
        want, self.hand = self.hand, 1 - HAND_OF[k]  # L 을 누르면 다음은 판정과 상관없이 R
        self.expire(now)
        n = self.upcoming()
        if n is None or now < n.at - self.bad:
            return None  # 칠 노트가 아직 판정 폭 밖이면 헛치기로 보고 판정하지 않음
        if k != KEY[n.t][want]:
            return self.judge("手順ミス" if k in KEY[n.t] else "不可")
        dt = abs(now - n.at)
        return self.judge("良" if dt <= self.good else "可" if dt <= self.ok else "不可")

    def judge(self, res):
        self.notes[self.next].res = res
        self.next += 1
        if res in HIT:
            self.hits += 1
            self.combo += 1
            self.best = max(self.best, self.combo)
        else:
            self.misses += 1
            self.combo = 0
        return res


class Memo:
    def __init__(self, root):
        self.root = root
        self.game = None      # 정지 모드일 때의 Game
        self.flow = None      # 이동 모드일 때의 Flow
        self.after_id = None  # 이동 모드 화면 갱신 예약
        root.title(TITLE)
        root.geometry("820x520")
        self.build_menu()
        self.build_status()
        self.build_text()
        self.set_zoom(100)
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
        z = tk.Menu(v, tearoff=0)
        z.add_command(label="拡大(I)", accelerator="Ctrl+プラス",
                      command=lambda: self.set_zoom(self.zoom + ZOOM_STEP))
        z.add_command(label="縮小(O)", accelerator="Ctrl+マイナス",
                      command=lambda: self.set_zoom(self.zoom - ZOOM_STEP))
        z.add_command(label="既定の倍率に戻す(R)", accelerator="Ctrl+0",
                      command=lambda: self.set_zoom(100))
        v.add_cascade(label="ズーム(Z)", menu=z)
        self.status_on = tk.BooleanVar(value=True)
        v.add_checkbutton(label="ステータス バー(S)", variable=self.status_on, command=self.toggle_status)
        m.add_cascade(label="表示(V)", menu=v)

        # 모드: "random" 또는 PATTERNS 의 난이도 키
        self.mode = tk.StringVar(value="random")
        md = tk.Menu(m, tearoff=0)
        md.add_radiobutton(label="ランダム(R)", variable=self.mode, value="random", command=self.reset)
        p = tk.Menu(md, tearoff=0)
        for level, label in LEVELS:
            p.add_radiobutton(label=label, variable=self.mode, value=level, command=self.reset)
        md.add_cascade(label="練習(P)", menu=p)
        md.add_separator()
        # 켜면 이동 모드, 끄면 정지 모드. 위의 어느 모드와도 함께 쓸 수 있음
        self.flow_on = tk.BooleanVar(value=False)
        md.add_checkbutton(label="音符を流す(S)", variable=self.flow_on, command=self.reset)
        self.bpm = tk.IntVar(value=BPM_DEFAULT)
        b = tk.Menu(md, tearoff=0)
        for v in BPM_PRESETS:
            b.add_radiobutton(label=str(v), variable=self.bpm, value=v, command=self.on_bpm)
        b.add_separator()
        b.add_command(label="その他(O)...", command=self.ask_bpm)
        md.add_cascade(label="BPM(B)", menu=b)
        m.add_cascade(label="モード(M)", menu=md)

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
        # 오른쪽부터 쌓으므로 화면에는 hand | pos | zoom | eol | enc 순서
        for name, width in [("enc", 16), ("eol", 16), ("zoom", 7), ("pos", 20), ("hand", 5)]:
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
        self.font = tkfont.Font(family=FONT_FAMILY, size=FONT_SIZE)  # 줌은 이 글꼴 크기를 바꿈
        self.text = tk.Text(self.frame, font=self.font, wrap="none", undo=False,
                            relief="flat", borderwidth=0, padx=4, pady=2,
                            selectbackground="#0078d7", selectforeground="white",
                            yscrollcommand=sy.set, xscrollcommand=sx.set)
        self.text.config(insertbackground=self.text.cget("bg"))  # 커서는 배경색으로 그려서 안 보이게
        sy.config(command=self.text.yview)
        sx.config(command=self.text.xview)
        sy.pack(side="right", fill="y")
        sx.pack(side="bottom", fill="x")
        self.text.pack(side="left", fill="both", expand=True)
        # 이동 모드는 부드럽게 움직이도록 캔버스에 그림. 겉모양은 Text 와 같고 모드에 따라 바꿔 끼움
        self.canvas = tk.Canvas(self.frame, bg=self.text.cget("bg"), highlightthickness=0, bd=0)

        for w in (self.text, self.canvas):
            w.bind("<Control-n>", lambda e: (self.reset(), "break")[1])
            w.bind("<Control-N>", lambda e: (self.reset(), "break")[1])
            w.bind("<Key>", self.on_key)
            w.bind("<Control-MouseWheel>", self.on_wheel)
            # 클릭으로 커서가 움직이지 않게
            for ev in ("<Button-1>", "<B1-Motion>", "<Double-Button-1>", "<Triple-Button-1>"):
                w.bind(ev, lambda e: (e.widget.focus_set(), "break")[1])
        self.text.bind("<Configure>", lambda e: self.redraw())  # 창 폭이 바뀌면 줄을 끝까지 다시 채움
        self.text.tag_config("D", foreground=DON_COLOR)
        self.text.tag_config("K", foreground=KA_COLOR)
        self.text.focus_set()

    # ---------- 연습 로직 ----------
    def reset(self):
        mode = self.mode.get()
        level = None if mode == "random" else mode
        self.stop_flow()
        self.root.title(TITLE)
        if self.flow_on.get():
            self.flow = Flow(level, self.bpm.get())
            self.show(self.canvas)
            self.start_flow()
        else:
            self.game = Game(level)
            self.show(self.text)
            self.draw()

    def show(self, w):
        other = self.canvas if w is self.text else self.text
        other.pack_forget()
        w.pack(side="left", fill="both", expand=True)
        w.focus_set()

    def on_bpm(self):
        if self.flow_on.get():  # 정지 모드에서는 값만 기억
            self.reset()

    def ask_bpm(self):
        v = simpledialog.askinteger("BPM", f"BPM ({BPM_MIN}〜{BPM_MAX})", parent=self.root,
                                    initialvalue=self.bpm.get(), minvalue=BPM_MIN, maxvalue=BPM_MAX)
        if v:
            self.bpm.set(v)
            self.on_bpm()

    def on_key(self, e):
        # Windows 에서 0x0008 은 NumLock 이므로 보지 않음. Alt 는 0x20000
        if e.keysym in ("Alt_L", "Alt_R") or e.state & 0x20000:
            return None  # Alt 는 메뉴용으로 통과
        ks = e.keysym.lower() if len(e.keysym) == 1 else ""
        ch = ks or (e.char or "").lower()
        if e.keysym == "Escape" or ch == "q":
            self.root.destroy()
            return "break"
        if e.state & 0x0004:  # Ctrl 조합은 타건으로 세지 않고 메모장 줌 단축키만 처리
            if e.keycode in ZOOM_IN_KEYS:
                self.set_zoom(self.zoom + ZOOM_STEP)
            elif e.keycode in ZOOM_OUT_KEYS:
                self.set_zoom(self.zoom - ZOOM_STEP)
            elif e.keycode in ZOOM_RESET_KEYS:
                self.set_zoom(100)
            return "break"
        if ch and ch in "fdjk":
            if self.flow:
                now = time.perf_counter() - self.t0
                res = self.flow.press(ch, now)
                if res:
                    self.show_judge(res, now)
                g = self.flow
            else:
                self.game.press(ch)
                self.draw()
                g = self.game
            if g.hits == 1:
                self.root.title("*" + TITLE)
        return "break"

    def on_wheel(self, e):
        self.set_zoom(self.zoom + (ZOOM_STEP if e.delta > 0 else -ZOOM_STEP))
        return "break"

    def set_zoom(self, pct):
        self.zoom = max(ZOOM_MIN, min(ZOOM_MAX, pct))
        self.font.configure(size=max(1, round(FONT_SIZE * self.zoom / 100)))
        self.cells["zoom"].config(text=f"{self.zoom}%")
        self.redraw()  # 정지 모드는 창에 들어가는 칸 수가 바뀌므로 다시 채움

    def redraw(self):
        if self.game and not self.flow:
            self.draw()

    def draw(self):
        # 칠 노트는 항상 맨 왼쪽(3번째 칸). 친 노트는 줄에서 빠지므로 나머지가 왼쪽으로 당겨짐
        g, t = self.game, self.text
        g.fill(t.winfo_width() // max(1, self.font.measure("0")))  # 창 오른쪽 끝까지 채움
        pat = "".join(n if isinstance(n, str) else n[0] for n in g.line)  # 색 지정을 위해 내부적으로는 D/K
        t.delete("1.0", "end")
        t.insert("1.0", "  " + pat.replace("D", DOT).replace("K", DOT))
        for i, c in enumerate(pat):
            if c in "DK":
                t.tag_add(c, f"1.{2 + i}", f"1.{3 + i}")
        t.mark_set("insert", "1.0")
        t.xview_moveto(0)
        self.cells["pos"].config(text="行 1, 列 3")
        self.cells["hand"].config(text="LR"[g.line[0][2]])

    # ---------- 이동 모드 ----------
    def start_flow(self):
        c = self.canvas
        # 판정 틀: 실제 게임처럼 원 두 개. 먼저 만들어서 노트가 그 위를 지나가게 함
        self.ring_in = c.create_oval(0, 0, 0, 0, fill=RING_FILL, outline="")
        self.ring_out = c.create_oval(0, 0, 0, 0, outline=RING_COLOR, width=1)
        self.judge_text = c.create_text(0, 0, text="", anchor="nw", font=self.font)
        self.judge_until = 0
        self.shown_hand = None
        self.cells["pos"].config(text="行 1, 列 3")
        self.t0 = time.perf_counter()
        self.tick()

    def stop_flow(self):
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        self.flow = None
        self.canvas.delete("all")

    def tick(self):
        f, c = self.flow, self.canvas
        now = time.perf_counter() - self.t0
        f.expire(now)
        cw, lh = self.font.measure("0"), self.font.metrics("linespace")
        x0, y0 = 4 + 2 * cw, 2  # 판정 위치 = 정지 모드에서 첫 노트가 있는 칸 (Text 의 padx, pady 와 맞춤)
        speed = cw / f.step     # 1초에 움직이는 픽셀. 16분 한 칸이 글자 한 칸
        right = c.winfo_width()
        f.fill(now + (right - x0) / speed + f.step)
        for n in f.prune(now - (x0 + cw) / speed):  # 왼쪽 밖으로 나간 노트
            if n.item:
                c.delete(n.item)
        for n in f.notes:
            x = x0 + (n.at - now) * speed
            if x > right:  # 아직 화면 밖. 확대해서 밀려난 노트는 지웠다가 다시 들어올 때 그림
                if n.item is None:
                    break
                c.delete(n.item)
                n.item = None
                continue
            if n.res in HIT:  # 친 노트는 실제 게임처럼 사라짐
                if n.item:
                    c.delete(n.item)
                    n.item = None
                continue
            if n.item is None:  # 놓친 노트도 원래 색 그대로 흘러감
                n.item = c.create_text(x, y0, text=DOT, anchor="nw", font=self.font,
                                       fill=DON_COLOR if n.t == "D" else KA_COLOR)
            else:
                c.coords(n.item, x, y0)
        cx, cy = x0 + cw / 2, y0 + lh * DOT_CY  # 판정 위치에 온 노트(점)의 가운데
        for ring, r in ((self.ring_in, lh * 0.25), (self.ring_out, lh * 0.45)):
            c.coords(ring, cx - r, cy - r, cx + r, cy + r)
        c.coords(self.judge_text, x0, y0 + lh)  # 판정 원 바로 아래
        if now > self.judge_until:
            c.itemconfig(self.judge_text, text="")
        hand = "LR"[f.hand]
        if hand != self.shown_hand:
            self.cells["hand"].config(text=hand)
            self.shown_hand = hand
        self.after_id = self.root.after(FRAME_MS, self.tick)

    def show_judge(self, res, now):
        # 실제 게임처럼 콤보는 10부터 표시. 흘려보낸 노트는 판정을 표시하지 않음
        combo = self.flow.combo
        self.canvas.itemconfig(self.judge_text, text=res + (f"  {combo}" if combo >= 10 else ""))
        self.judge_until = now + 0.5


def disable_ime(root, *widgets):
    try:
        import ctypes
        imm = ctypes.windll.imm32
        user = ctypes.windll.user32
        imm.ImmAssociateContext.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        imm.ImmAssociateContext.restype = ctypes.c_void_p
        user.GetParent.argtypes = [ctypes.c_void_p]
        user.GetParent.restype = ctypes.c_void_p
        for hwnd in [w.winfo_id() for w in widgets] + [root.winfo_id(), user.GetParent(root.winfo_id())]:
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
    disable_ime(root, app.text, app.canvas)  # 일본어 IME 가 켜져 있어도 f/d/j/k 가 바로 입력되도록
    root.mainloop()
