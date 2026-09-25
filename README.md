# donka-typing

태고의 달인 돈/카 패턴을 키보드로 연습하는 프로그램입니다.
패턴이 끝없이 이어지고, 양손을 번갈아 치도록 키가 정해집니다.

| 노트 | 왼손 | 오른손 |
|---|---|---|
| 돈 (빨강) | `F` | `J` |
| 카 (파랑) | `D` | `K` |

- 묶음 길이는 1~8타 랜덤
- 묶음 사이를 넘어서도 손 순서가 이어짐
- 표시된 손으로 정확히 쳐야 다음으로 진행
- `Esc` 또는 `Q` 로 종료

## 다운로드 (Python 없이 실행)

[Releases](../../releases) 에서 `memo.exe` 를 받아 실행하면 됩니다.
겉모양은 Windows 메모장과 같습니다.

처음 실행할 때 Windows SmartScreen 경고가 나오면
「詳細情報」→「実行」 을 누르세요. 서명되지 않은 exe 라서 나오는 경고입니다.

## Python 으로 직접 실행

```
pythonw donka_memo.py
```

표준 라이브러리만 사용하므로 추가 설치는 필요 없습니다.

## 빌드

`v` 로 시작하는 태그를 push 하면 GitHub Actions 가 `memo.exe` 를 만들어 Releases 에 올립니다.

```
git tag v1.0.0
git push origin v1.0.0
```
