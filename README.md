# 데스로드 투 캐나다 한글패치 (비공식)

스팀판 Death Road to Canada 대사랑 UI 한글로 나오게 해주는 팬패치임.
번역 파일(PO)이랑 설치 도구만 올려둠. 게임 스크립트나 실행 파일은 안 올렸으니까 게임은 각자 정품으로 갖고 있어야 함.
설치할 때 님들 PC에 있는 영어 `.df` 파일 검증하고 그걸로 한글판을 그 자리에서 만들어서 깔아주는 방식임.

## 준비물

- **윈도우 + 스팀 정품.** 지원 빌드는 **24936165**. 실행 파일이랑 영어 스크립트 해시가 안 맞으면 설치 안 됨 (다른 모드 깔려 있거나 업데이트로 바뀐 경우)
- **파이썬 3.10 이상.** 설치할 때 PATH에 추가 체크 꼭 해주셈
- `requirements.txt`에 있는 polib, Pillow (아래 명령어로 한 방에 깔림). pefile은 `vendor/`에 같이 들어 있음
- **V202.0 일본어 패치 배포본의 `1.MOD LOADER` 폴더.** 따로 받아서 게임 폴더 말고 아무 데나 풀어두셈

로더는 [ハム님 일본어 패치 배포 페이지](https://arkwright1.blog.fc2.com/blog-entry-1576.html)에서 받으면 됨.
`--loader-root`에는 `dr2c-gadget.dll`이랑 `mods`가 바로 보이는 `1.MOD LOADER` 폴더 넣으면 됨.
자동 압축해제 파일은 게임 폴더 밖에 풀고, 안에 있는 `prog_Patch.exe`는 **실행하지 마셈.** 그 패치는 이 설치 도구가 알아서 해줌.

그 배포본이 재배포 금지라서 로더, Frida DLL, 원래 폰트 아틀라스는 여기 안 올림. 설치 도구가 검증된 로더 파일 8개만 읽어가고 일본어 대사나 `prog_Patch.exe`는 안 건드림.
로더 원본 프로젝트는 [sevenshape/dr2c-mod-loader](https://github.com/sevenshape/dr2c-mod-loader) 참고. 옛날 `SDL2_mixer.dll` 프록시 방식이랑은 호환 안 됨.

## 설치 방법

게임 끄고, 이 저장소 폴더에서 터미널 열고 아래 순서대로 치면 됨.
`<게임 폴더>` 같은 건 본인 경로로 바꾸고 큰따옴표는 그대로 두셈. 게임 폴더 = `prog.exe` 있는 폴더임.

```powershell
python -m pip install -r requirements.txt
python install.py --game-root "<게임 폴더>" --loader-root "<로더 폴더>" --check
python install.py --game-root "<게임 폴더>" --loader-root "<로더 폴더>" --backup-root "<새 백업 폴더>" --apply
```

- `--check`는 임시 폴더에서 빌드+설치 테스트만 돌려봄. 게임 폴더는 안 건드리니까 먼저 이걸로 확인해보셈
- `--apply`가 진짜 설치임. 게임 폴더 통째로 새 백업 폴더에 복사하고 해시 다 확인한 다음에 깔아줌
- 이미 있는 폴더를 백업 폴더로 지정하면 멈춤. `--backup-root` 빼먹으면 게임 폴더 옆에 날짜 붙은 백업 폴더 알아서 만듦

설치 끝나면 스팀에서 평소처럼 켜면 한글로 나옴. 원래 `deathforth/` 파일은 그대로 두고 `mods/DRTC_KO/`가 위에 덮어씌워지는 방식이라 원본 손상 없음.

⚠️ 설치 기록이랑 백업에는 복구용으로 님들 실제 경로가 저장되니까 그거 어디 올리지 마셈.

예전 버전 깔려 있으면 아래 제거 먼저 하고 새로 까셈. 다른 모드가 `prog.exe`나 영어 스크립트 바꿔놨으면 설치 중단됨. 스팀 업데이트로 빌드 바뀌어도 마찬가지.

## 삭제 방법

게임 끄고 같은 폴더에서 이거 치면 됨. 삭제는 polib, Pillow 없어도 됨.

```powershell
python uninstall.py --game-root "<게임 폴더>" --check
python uninstall.py --game-root "<게임 폴더>" --apply
```

바뀐 파일은 백업에서 복구하고 패치가 추가한 파일만 지움.
설치 후에 패치 파일 손댔거나 백업이 깨져 있으면 안전하게 멈춤.
백업 폴더는 삭제 후에도 남겨두니까 복구 확인 끝날 때까지 지우지 마셈.

## 번역 수정하고 싶은 사람

- `translations/001.po` ~ `033.po`가 대사, `native-ko.po`가 UI 번역임
- `msgctxt`는 게임 안 파일 경로
- 비어 있는 번역이랑 fuzzy는 영어로 나오고, `<EMPTY>`는 빈 문자열로 바뀜
- 게임이 비교용으로 쓰는 문자열(캐릭터 이름, 특성 이름 등)이랑 native UI 키는 일부러 영어로 둠. 이거 번역하면 게임 로직 꼬임
- 빌드할 때 자리표시자, 제어문자, 줄바꿈, 조사 조각, 폰트에 없는 글자까지 다 검사해줌

오역이나 어색한 문장 보이면 Issues에 남겨주거나 PR 주셈. 어느 이벤트에서 나왔는지 같이 적어주면 찾기 편함.

설치 없이 한글 모드만 뽑아보고 싶으면 새 폴더 지정해서 이거 돌리면 됨 (게임/로더/저장소 폴더랑 겹치면 안 됨):

```powershell
python build_ko.py --game-root "<게임 폴더>" --loader-root "<로더 폴더>" --output "<생성 폴더>"
```

## 폰트

`fonts/hangul_12x12.png`는 Galmuri11로 만든 한글 전용 투명 오버레이임.
설치할 때 님들이 받은 아틀라스의 한글 칸(U+AC00–D7A3, U+3131–318E)에만 합쳐지고 다른 글자랑 아이콘은 그대로임. 다시 만들고 싶으면:

```powershell
python make_hangul_atlas.py --bdf fonts/Galmuri11.bdf --output "<새 오버레이 PNG>"
```

12×12 비트맵 폰트 씀. 완성형 한글이랑 호환 자모 다 나옴. 캐릭터 이름 한글 입력(IME)은 아직 제대로 테스트 안 해봄.

생성된 `.df`, 게임 실행 파일, 백업, 로더 배포본은 공개 저장소에 올리지 마셈.

## 알려진 점

- 조사가 `은(는)`, `이(가)`처럼 나오는 곳 있음. 캐릭터 이름이 게임 중에 랜덤으로 들어가서 어쩔 수 없음
- 캐릭터 이름은 영어 그대로 둠
- 키보드로 처음부터 끝까지 한 판 다 돌려본 건 아니라서 이상한 데 있으면 제보 부탁함

## 크레딧 / 라이선스

- 번역이랑 도구: **DRTC Korean Patch contributors**
- [Galmuri / quiple](https://github.com/quiple/galmuri): 한글 폰트. SIL OFL 1.1 원문은 `licenses/Galmuri-OFL.txt`
- [sevenshape / dr2c-mod-loader](https://github.com/sevenshape/dr2c-mod-loader): 다국어 표시랑 resources-only 모드 방식. ISC 고지는 `licenses/sevenshape-ISC.txt`. 로더 배포본은 각자 받아야 함
- [ハム님 일본어 패치](https://arkwright1.blog.fc2.com/blog-entry-1576.html): V202.0 구조 참고함. 일본어 번역이나 배포본은 안 들어 있음
- [Frida](https://frida.re/): 로더가 쓰는 후킹 기반. Frida 바이너리는 여기 없음. 라이선스는 [원 프로젝트](https://github.com/frida/frida/blob/main/COPYING) 확인
- [pefile / Ero Carrera](https://github.com/erocarrera/pefile): 실행 파일 패치용. 고지는 `vendor/pefile-LICENSE.txt`

다른 분들 이름이랑 공개 연락처는 원래 라이선스 고지라서 그대로 둠. 게임이랑 원문 권리는 원 저작권자한테 있음. 자세한 건 `THIRD_PARTY_NOTICES.md` 보셈.

## 주의

Rocketcat Games, Madgarden이랑 아무 관계 없는 비공식 팬패치임. 게임은 꼭 사서 하셈.
쓰다가 생기는 문제는 본인 책임임. 권리자분이 내려달라고 하면 바로 내림.
문제 제보는 Issues로 주셈. 근데 게임 스크립트 통째로나 실행 파일, 백업, 본인 경로 찍힌 로그 같은 건 첨부하지 마셈.
