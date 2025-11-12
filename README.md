# 주소 처리 모듈

이 모듈은 LLM 추출 및 퍼지 매칭을 포함한 다양한 기술을 사용하여 텍스트 콘텐츠에서 주소 정보를 처리하고 일치시키는 도구를 제공합니다.

## 목차
- [프로젝트 개요](#프로젝트-개요)
- [설정](#설정)
- [사용법](#사용법)
- [파일 구조](#파일-구조)
- [구성](#구성)
- [출력](#출력)

## 프로젝트 개요

`address_processor` 모듈은 비정형 텍스트에서 주소 정보를 추출하고 표준화하도록 설계되었습니다. 다음을 포함하는 파이프라인을 활용합니다.
-   **LLM 추출:** 언어 모델(LLM)을 사용하여 텍스트에서 주소 관련 엔티티를 식별하고 추출합니다.
-   **주소 매칭:** 추출된 주소를 알려진 주소 데이터베이스(`df_addr.parquet.gzip`)와 비교하여 가장 일치하는 항목을 찾습니다.
-   **지오코딩:** 일치하는 주소에 대한 위도 및 경도를 얻습니다.

이 프로세스를 실행하는 기본 스크립트는 `run_address_processing.py`입니다.

## 설정

이 프로젝트는 의존성 관리를 위해 `Poetry`를 사용합니다.

1.  **Poetry 설치:**
    Poetry가 설치되어 있지 않다면, [공식 Poetry 웹사이트](https://python-poetry.org/docs/#installation)의 지침에 따라 설치하십시오.

2.  **프로젝트 루트로 이동:**
    ```bash
    cd /Users/salgu/Workspace/2_area/civic-hacking/scrape
    ```

3.  **의존성 설치:**
    Poetry 관리 가상 환경에 필요한 모든 패키지가 설치되었는지 확인하십시오.
    ```bash
    poetry install
    ```
    이 명령은 가상 환경을 생성하고(`pyproject.toml` 및 `poetry.lock`에 나열된 모든 의존성을 설치합니다.

## 사용법

주소 처리 파이프라인을 실행하려면 프로젝트 루트 디렉토리에서 `run_address_processing.py` 스크립트를 Python 모듈로 실행하십시오.

```bash
poetry run python -m address_processor.run_address_processing
```

스크립트는 다음을 수행합니다.
1.  `address_processor/address/df_addr.parquet.gzip`에서 주소 데이터를 로드합니다.
2.  `address_processor/dataframe/flasher_hk_20130101_20220307_loc.parquet.gzip`에서 처리할 텍스트 콘텐츠를 로드합니다.
3.  정의된 텍스트 항목 범위(기본값: `start_index = 11`, `end_index = 20`)를 처리합니다.
4.  `address_processor/log/`에 타임스탬프가 찍힌 파일에 활동을 기록합니다.
5.  처리 결과를 `address_processor/address/matched_addresses.parquet.gzip`에 저장합니다.

## 파일 구조

-   `address_processor/`: 메인 패키지 디렉토리.
    -   `__init__.py`: `address_processor`를 Python 패키지로 만듭니다.
    -   `run_address_processing.py`: 주소 처리 파이프라인을 실행하는 메인 스크립트.
    -   `address_processor.py`: LLM 추출, 매칭 및 지오코딩을 조정하는 `AddressProcessor` 클래스를 포함합니다.
    -   `address_utils.py`: 주소 정규화 및 조작을 위한 유틸리티 함수.
    -   `llm_extractor.py`: 정보 추출을 위해 언어 모델과 상호 작용합니다.
    -   `address_matcher.py`: 데이터베이스에 대해 주소를 퍼지 매칭하는 로직을 구현합니다.
    -   `utils/`: 일반 유틸리티 함수를 위한 하위 패키지.
        -   `__init__.py`: `utils`를 Python 하위 패키지로 만듭니다.
        -   `custom_utils.py`: `load_var` 및 `save_var` 함수를 포함합니다.
        -   `search_address.py`: 주소 검색과 관련된 함수(예: `find_keyword_with_postfix`)를 포함합니다.
        -   `text_utils.py`: 텍스트 전처리를 위한 `clean_text` 함수를 포함합니다.
    -   `address/`: 입력 및 출력 주소 관련 데이터 파일을 위한 디렉토리.
        -   `df_addr.parquet.gzip`: 알려진 주소의 입력 데이터베이스.
        -   `matched_addresses.parquet.gzip`: 처리되고 일치된 주소를 포함하는 출력 파일.
    -   `dataframe/`: 입력 텍스트 데이터를 위한 디렉토리.
        -   `flasher_hk_20130101_20220307_loc.parquet.gzip`: 주소 추출을 위한 입력 텍스트 콘텐츠.
    -   `log/`: 스크립트 실행 중 생성된 로그 파일을 위한 디렉토리.

## 구성

`run_address_processing.py` 스크립트는 스크립트 내에서 다음 변수를 수정하여 구성할 수 있습니다.

-   `llm_model`: `AddressProcessor`에서 사용할 LLM 모델(예: `'gemma3:1b'`).
-   `start_index`, `end_index`: `df_text`에서 처리할 텍스트 항목의 범위.

## 출력

성공적으로 실행되면 스크립트는 다음을 생성합니다.
-   `address_processor/log/`에 로그 파일(예: `address_matching_YYYYMMDD_HHMMSS.log`)이 처리 단계를 자세히 설명합니다.
-   추출된 RAG 정보, 일치하는 주소, 점수 및 지오코딩된 좌표를 포함하는 DataFrame이 있는 Parquet 파일 `address_processor/address/matched_addresses.parquet.gzip`.
