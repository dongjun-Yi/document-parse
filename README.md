# RAG Document Parser

RAG(Retrieval-Augmented Generation) 아키텍처의 **Indexing 단계**에서 사용할 Document Parser의 성능을 검토하는 프로젝트입니다.
Upstage `document-parse` API를 활용해 PDF·이미지 문서에서 텍스트·표·이미지를 추출하고 결과를 분석합니다.

---

## 디렉토리 구조

```
rag_document_parser/
├── src/
│   ├── config/         # 환경 변수 및 파싱 옵션 설정
│   ├── parser/         # Upstage API 호출 및 결과 변환
│   ├── models/         # 파싱 결과 데이터 클래스
│   └── reporter/       # JSON/HTML 저장, 품질 통계 분석
├── outputs/            # 파싱 결과 출력 (자동 생성)
├── main.py             # CLI 진입점
└── requirements.txt
```

---

## 시작하기

### 1. 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. API 키 설정

```bash
# .env.example 을 복사하여 .env 파일 생성
copy .env.example .env
```

`.env` 파일을 열고 Upstage API 키를 입력하세요.
API 키는 [console.upstage.ai](https://console.upstage.ai) 에서 발급받을 수 있습니다.

```
UPSTAGE_API_KEY=your_api_key_here
```

### 3. 파서 실행

```bash
# 기본 실행 (ocr=auto, format=html, split=element)
python main.py --file demo_pdf_file.pdf

# OCR 강제 적용 (스캔 PDF)
python main.py --file demo_pdf_file.pdf --ocr force

# 마크다운 포맷으로 출력
python main.py --file demo_pdf_file.pdf --format markdown

# 페이지 단위 분할
python main.py --file demo_pdf_file.pdf --split page

# 출력 위치 지정
python main.py --file demo_pdf_file.pdf --output my_results/
```

---

## CLI 옵션

| 옵션 | 기본값 | 설명 |
|---|---|---|
| `--file` | (필수) | 파싱할 파일 경로 |
| `--ocr` | `auto` | OCR 모드: `auto` / `force` / `off` |
| `--format` | `html` | 출력 포맷: `html` / `text` / `markdown` |
| `--split` | `element` | 분할 단위: `element` / `page` / `none` |
| `--no-coords` | — | 좌표 추출 비활성화 |
| `--output` | `outputs/` | 결과 저장 디렉토리 |

---

## 출력 결과

실행 후 `outputs/` 디렉토리에 두 개의 파일이 생성됩니다.

- **`<파일명>_result.json`** — 구조화된 파싱 결과 (요소별 카테고리·내용·좌표)
- **`<파일명>_raw.html`** — API 원본 HTML 응답

콘솔에는 아래 통계가 출력됩니다.

```
┌─────────────────────────────┐
│     추출 결과 요약           │
├──────────────────┬──────────┤
│ 총 요소 수        │   42     │
│ 페이지 수         │    7     │
│ 처리 시간         │ 3.21s    │
│ 텍스트 요소       │   28     │
│ 표 (table)       │    5     │
│ 이미지            │    6     │
│ 수식 (equation)  │    3     │
└──────────────────┴──────────┘
```

---

## 테스트

```bash
pytest tests/ -v
```
