# 데스로드 투 캐나다 한글패치 (비공식)

스팀판 Death Road to Canada 대사랑 메뉴 한글로 나오게 해주는 팬패치임 ㅇㅇ

컴맹이어도 밑에 있는 거 위에서부터 순서대로만 하면 됨. 중간에 하나 건너뛰면 높은 확률로 안 되니까 천천히 ㄱㄱ

**어떻게 돌아가는 거냐면**
여기엔 번역문이랑 설치 프로그램만 있음. 게임 파일은 저작권 때문에 못 올림.
설치 돌리면 님 컴에 깔린 영어판 읽어다가 그 자리에서 한글판 뽑아서 깔아주는 식임. 그래서 무조건 스팀 정품 있어야 됨.
깔기 전에 게임 폴더 통째로 백업 떠놓으니까 맘에 안 들면 원래대로 되돌릴 수 있음. 걱정 ㄴㄴ

---

## 0. 시작 전에 체크

- **윈도우**만 됨. 맥, 리눅스, 스팀덱은 안 됨 ㅈㅅ
- **스팀 정품**이어야 됨
- 게임 **최신 버전**이고 **다른 모드 안 깔려 있어야** 됨
  - 지원 빌드는 `24936165` 딱 하나임
  - 버전 다르거나 다른 모드가 파일 건드려놨으면 설치 프로그램이 알아서 멈춤. 게임 터지는 일은 없으니까 쫄지 마셈
- 예전에 이 패치 깐 적 있으면 [6번 삭제](#6-삭제하는-법)부터 하고 와라

---

## 1. 파이썬 깔기

설치 프로그램이 파이썬으로 돌아감. 한 번만 깔면 끝.

1. [python.org](https://www.python.org/downloads/windows/) 가서 3.10 이상 아무거나 받음 (그냥 젤 최신 받으면 됨)
2. 설치 파일 켜면 첫 화면 밑에 **`Add python.exe to PATH`** 체크박스 있음
   - **이거 체크 안 하면 뒤에서 100% 막힘. 꼭 체크해라 ㄹㅇ**
3. `Install Now` 누르고 기다리면 끝

이미 깔려 있는지 모르겠으면 그냥 또 깔아도 됨 상관없음

---

## 2. 한글패치 받기

1. 이 페이지 위에 초록색 **`<> Code`** 버튼 → **`Download ZIP`**
2. 받은 zip 오른쪽 클릭 → **압축 풀기**
3. 풀린 폴더는 찾기 쉬운 데 둬라. `C:\DRTC-KO` 이런 데
   - **게임 폴더 안에 넣지 마셈**

이게 앞으로 말하는 **패치 폴더**임. 열었을 때 `install.py` 같은 파일 보이면 맞음

---

## 3. 모드 로더 받기

한글 띄우려면 **모드 로더**가 따로 필요함. 이건 일본어 패치 만든 분 배포본인데 재배포 금지라 여기 못 넣었음. 직접 받아와야 됨

1. [ハム님 일본어 패치 배포 페이지](https://arkwright1.blog.fc2.com/blog-entry-1576.html) 가서 **V202.0** 받음
2. **게임 폴더 말고 딴 데** 풀어라. `C:\DRTC-Loader` 이런 데
   - 실행하면 압축 풀리는 파일이면 그냥 실행해서 풀 위치만 게임 폴더 밖으로 잡으면 됨
3. 풀린 거 중에 **`1.MOD LOADER`** 폴더 찾음
   - 열었을 때 `dr2c-gadget.dll`이랑 `mods` 폴더가 **바로** 보여야 됨
   - 이게 **로더 폴더**임

**배포본 안에 있는 `prog_Patch.exe`는 절대 실행하지 마라.** 그건 이 설치 프로그램이 알아서 해줌. 실행하면 설치 안 됨
로더 폴더 안 파일도 건드리지 말고 받은 그대로 둬라. 하나라도 바뀌면 설치 멈춤

---

## 4. 게임 폴더 찾기

1. 스팀 → 라이브러리
2. Death Road to Canada 오른쪽 클릭 → **관리** → **로컬 파일 보기**
3. 열린 폴더에 `prog.exe` 있으면 그게 **게임 폴더**임

보통 이런 경로임

```
C:\Program Files (x86)\Steam\steamapps\common\Death Road to Canada
```

### 경로 복사하는 법 (중요)

경로 손으로 치면 오타 나니까 복사해서 써라

- 폴더를 **Shift 누른 채로 오른쪽 클릭** → **`경로로 복사`**
- 이러면 `"C:\...\Death Road to Canada"` 처럼 **큰따옴표까지 같이 복사됨.** 그대로 붙여넣으면 됨

메모장 하나 켜서 게임 폴더랑 로더 폴더 경로 미리 붙여놓으면 편함

---

## 5. 설치

**게임 꺼라.** 켜져 있으면 안 깔림

### 5-1. 명령창 열기

1. 탐색기로 **패치 폴더** 들어감
2. 위에 주소창(경로 나오는 데) 클릭해서 지우고 `powershell` 치고 엔터
3. 파란 창 뜨면 됨. 여기다 밑에 명령어 하나씩 붙여넣고 엔터 치면 됨

붙여넣기는 Ctrl+V나 마우스 오른쪽 클릭

### 5-2. 필요한 거 설치 (처음 한 번만)

```powershell
python -m pip install -r requirements.txt
```

글자 쭉 올라가다가 `Successfully installed` 어쩌고 뜨면 됨
`Requirement already satisfied` 떠도 이미 깔려 있다는 뜻이니까 ㄱㅊ

### 5-3. 테스트 설치 (게임 안 건드림)

진짜 깔기 전에 문제 없나 미리 돌려보는 거임. **게임 파일 하나도 안 바뀌니까** 맘 편히 돌려라

밑에 명령어 메모장에 복붙하고 `"게임 폴더"`, `"로더 폴더"` 부분을 4번에서 복사한 경로로 **따옴표째로** 바꿔치기 해라

```powershell
python install.py --game-root "게임 폴더" --loader-root "로더 폴더" --check
```

바꾸면 대충 이렇게 됨

```powershell
python install.py --game-root "C:\Program Files (x86)\Steam\steamapps\common\Death Road to Canada" --loader-root "C:\DRTC-Loader\1.MOD LOADER" --check
```

이거 통째로 명령창에 붙여넣고 엔터. 좀 걸릴 수 있음

- `{ "mode": "install", ... }` 이런 거 쭉 뜨면 **성공**. 다음 거 ㄱㄱ
- 빨간 글씨로 `ERROR: ...` 뜨면 **실패**. [7번 오류 모음](#7-오류-뜨면) 봐라

### 5-4. 진짜 설치

방금 거에서 **맨 끝 `--check`만 `--apply`로 바꿔서** 다시 돌리면 끝

```powershell
python install.py --game-root "C:\Program Files (x86)\Steam\steamapps\common\Death Road to Canada" --loader-root "C:\DRTC-Loader\1.MOD LOADER" --apply
```

- 깔기 전에 게임 폴더 통째로 **백업**함. 게임 폴더 옆에 `Death Road to Canada_KO_backup_날짜` 이런 이름으로 생김
- 통째로 복사하는 거라 **시간 좀 걸리고 용량도 그만큼 먹음**
- 다 끝나고 `ERROR` 없으면 설치 완료

이제 스팀에서 평소처럼 켜면 한글로 나옴 ㅅㄱ

백업 위치 직접 정하고 싶으면 `--apply` 앞에 `--backup-root "새 폴더 경로"` 넣으면 됨. 근데 **아직 없는 새 폴더**여야 됨

**백업 폴더 지우지 마라.** 나중에 패치 지울 때 이걸로 되돌림

---

## 6. 삭제하는 법

영어판으로 돌아가고 싶으면 **게임 끄고** 5-1처럼 패치 폴더에서 명령창 열고

먼저 검사 (아무것도 안 바뀜)

```powershell
python uninstall.py --game-root "게임 폴더" --check
```

문제 없으면 진짜 삭제

```powershell
python uninstall.py --game-root "게임 폴더" --apply
```

- 패치가 바꾼 파일은 백업에서 원래대로 돌려놓고, 패치가 추가한 파일만 지움
- 다 끝나도 백업 폴더는 남아 있음. 영어로 잘 나오는 거 확인하고 지우고 싶으면 지워도 됨
- 패치 파일 직접 건드렸거나 백업 깨져 있으면 안전하게 중간에 멈춤

---

## 7. 오류 뜨면

| 이거 뜨면 | 이렇게 해라 |
|---|---|
| `python`은(는) 인식할 수 없는... / MS 스토어가 열림 | 파이썬 깔 때 `Add python.exe to PATH` 체크 안 한 거임. 설치 파일 다시 켜서 Modify/Repair 하든가 지우고 체크해서 다시 깔아라. 그래도 안 되면 명령어 앞 `python`을 `py`로 바꿔서 해봐라 |
| `No module named 'polib'` 또는 `'PIL'` | 5-2 안 했거나 실패한 거임. 다시 해라 |
| `The target game is running` / `close it first` | 게임 켜져 있음. 완전히 끄고 다시 |
| `Game root must be the folder containing prog.exe` | 게임 폴더 경로 틀림. `prog.exe` 바로 들어 있는 폴더 맞는지 확인 (4번) |
| `Unsupported prog.exe SHA-256` | 게임 버전이 다르거나, `prog_Patch.exe` 이미 실행했거나, 다른 모드가 건드린 거임. 스팀에서 게임 오른쪽 클릭 → 속성 → 설치된 파일 → **게임 파일 무결성 검사** 하고 다시 해봐라. 그래도 안 되면 스팀 업데이트로 버전 바뀐 거라 패치 업뎃 기다려야 됨 |
| `Unsupported/modified English script` | 게임 파일이 원래 상태가 아님. 위처럼 무결성 검사 ㄱㄱ |
| `Loader SHA-256 mismatch or missing file` | 로더 폴더 잘못 잡았거나 버전 다름. `dr2c-gadget.dll` **바로** 들어 있는 `1.MOD LOADER` 폴더 맞는지, V202.0 맞는지 확인 (3번) |
| `Download the loader into a separate folder outside the game` | 로더 폴더가 게임 폴더 안에 있음. 밖으로 빼라 |
| `Remove the existing Korean patch...` / `An installation record ... already exists` | 이미 깔려 있음. 6번으로 지우고 다시 깔아라 |
| `Backup root must be a new, nonexistent folder` | `--backup-root`로 잡은 폴더가 이미 있음. 없는 이름으로 바꿔라 |
| `No Korean patch installation record` (삭제할 때) | 이 게임 폴더엔 패치 안 깔려 있음. 경로 맞는지 확인 |
| `This installer requires Windows` | 윈도우에서만 됨 ㅈㅅ |

여기 없는 거 뜨면 [Issues](../../issues)에 빨간 `ERROR:` 줄 복붙해서 올려줘라
근데 오류에 님 컴 사용자 이름 같은 거 찍혀 있으면 그건 가리고 올려라

---

## 8. 알려진 문제

- `은(는)`, `이(가)` 이렇게 나오는 데 있음. 캐릭터 이름이 랜덤으로 들어가서 어쩔 수 없음
- 캐릭터 이름, 특성 이름 같은 건 일부러 영어로 둠. 게임이 이걸로 내부 판정해서 번역하면 게임 꼬임
- 캐릭터 이름 한글 입력은 아직 제대로 테스트 안 해봄
- 처음부터 엔딩까지 한 판 다 돌려본 건 아니라서 이상한 데 있으면 제보 좀

오역이나 어색한 문장 보이면 [Issues](../../issues)에 올려주셈. **어느 장면(이벤트)에서 나왔는지** 같이 적어주면 찾기 ㅈㄴ 편함

### 이런 건 어디에도 올리지 마라

- 게임 파일, 백업 폴더, 모드 로더 배포본 (저작권)
- 설치 기록 파일(`.drtc_ko_install.json`)이나 백업 안 기록 파일. 님 컴 폴더 경로 다 찍혀 있음

---

<details>
<summary><b>번역 고치고 싶은 사람 / 개발자용 (눌러서 펼치기)</b></summary>

### 번역 파일

- `translations/001.po` ~ `033.po`가 대사, `native-ko.po`가 UI
- `msgctxt`는 게임 안 파일 경로
- 비어 있는 번역이랑 fuzzy는 영어로 나오고, `<EMPTY>`는 빈 문자열로 바뀜
- 게임이 비교용으로 쓰는 문자열(캐릭터 이름, 특성 이름 등)이랑 native UI 키는 일부러 영어로 둠
- 빌드할 때 자리표시자, 제어문자, 줄바꿈, 조사 조각, 폰트에 없는 글자까지 다 검사해줌

PR 환영함

### 설치 없이 한글 모드만 뽑아보기

새 폴더 잡고 돌리면 됨 (게임/로더/패치 폴더랑 겹치면 안 됨)

```powershell
python build_ko.py --game-root "<게임 폴더>" --loader-root "<로더 폴더>" --output "<생성 폴더>"
```

### 설치 방식

- PC에 있는 영어 `.df` 스크립트 해시 검증하고 그걸로 한글판을 그 자리에서 생성함
- 원래 `deathforth/` 파일은 그대로 두고 `mods/DRTC_KO/`가 위에 덮어씌워지는 방식
- 로더 배포본에선 검증된 파일 8개만 읽어가고 일본어 대사나 `prog_Patch.exe`는 안 건드림. `prog.exe` 패치는 설치 프로그램이 직접 함 (pefile은 `vendor/`에 포함)
- `--check`는 임시 폴더에서 빌드+설치 검증만, `--apply`는 게임 폴더 전체 백업하고 해시 확인한 다음 설치
- 로더 원본 프로젝트는 [sevenshape/dr2c-mod-loader](https://github.com/sevenshape/dr2c-mod-loader). 옛날 `SDL2_mixer.dll` 프록시 방식이랑은 호환 안 됨

### 폰트

`fonts/hangul_12x12.png`는 Galmuri11로 만든 한글 전용 투명 오버레이임
설치할 때 로더 폰트 아틀라스의 한글 칸(U+AC00–D7A3, U+3131–318E)에만 합쳐지고 다른 글자랑 아이콘은 그대로임. 12×12 비트맵 폰트고 완성형 한글이랑 호환 자모 다 나옴. 다시 만들고 싶으면

```powershell
python make_hangul_atlas.py --bdf fonts/Galmuri11.bdf --output "<새 오버레이 PNG>"
```

생성된 `.df`, 게임 실행 파일, 백업, 로더 배포본은 공개 저장소에 올리지 마셈

</details>

---

## 크레딧 / 라이선스

- 번역이랑 도구: **DRTC Korean Patch contributors**
- [Galmuri / quiple](https://github.com/quiple/galmuri): 한글 폰트. SIL OFL 1.1 원문은 `licenses/Galmuri-OFL.txt`
- [sevenshape / dr2c-mod-loader](https://github.com/sevenshape/dr2c-mod-loader): 다국어 표시랑 resources-only 모드 방식. ISC 고지는 `licenses/sevenshape-ISC.txt`. 로더 배포본은 각자 받아야 함
- [ハム님 일본어 패치](https://arkwright1.blog.fc2.com/blog-entry-1576.html): V202.0 구조 참고함. 일본어 번역이나 배포본은 안 들어 있음
- [Frida](https://frida.re/): 로더가 쓰는 후킹 기반. Frida 바이너리는 여기 없음. 라이선스는 [원 프로젝트](https://github.com/frida/frida/blob/main/COPYING) 확인
- [pefile / Ero Carrera](https://github.com/erocarrera/pefile): 실행 파일 패치용. 고지는 `vendor/pefile-LICENSE.txt`

다른 분들 이름이랑 공개 연락처는 원래 라이선스 고지라 그대로 둠. 게임이랑 원문 권리는 원 저작권자한테 있음. 자세한 건 `THIRD_PARTY_NOTICES.md` 봐라

## 주의

Rocketcat Games, Madgarden이랑 아무 상관 없는 비공식 팬패치임. 게임은 꼭 사서 해라
쓰다가 문제 생기면 본인 책임임. 권리자분이 내려달라 하면 바로 내림
제보는 Issues로. 근데 게임 스크립트 통째로나 실행 파일, 백업, 본인 경로 찍힌 로그 같은 건 첨부하지 마셈
