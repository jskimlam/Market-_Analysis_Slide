# pip install Pillow
# ────────────────────────────────────────────────────────────
# convert.py  ·  슬라이드 다수페이지 아카이브 변환기
# 파일명 규칙: YYMMDD_이름_페이지번호.png
#   예) 260206_SM_01.png  260206_SM_02.png  260207_WTI_01.png
# ────────────────────────────────────────────────────────────

import os
import glob
import shutil
import json
from datetime import datetime
from PIL import Image

# ── 경로 상수 ──────────────────────────────────────────────
SOURCE_DIR  = 'images'          # 사용자가 PNG를 올리는 폴더
ARCHIVE_DIR = 'images/archive'  # webp 변환본 보관 폴더
LIST_JSON   = 'images/list.json'  # 뷰어가 읽는 목록 파일
WEBP_QUALITY = 80               # webp 압축 품질 (0~100)


def ensure_dirs():
    """필요한 폴더가 없으면 생성"""
    os.makedirs(ARCHIVE_DIR, exist_ok=True)


def find_slide_pngs():
    """
    images/ 폴더에서 슬라이드 형식 PNG만 골라냄
    파일명 패턴: YYMMDD_이름_페이지번호.png  (언더스코어 2개)
    일반 단일 이미지(260206.png 등)는 건드리지 않음
    """
    all_pngs = glob.glob(f'{SOURCE_DIR}/*.png')
    slide_pngs = []
    for path in all_pngs:
        name = os.path.splitext(os.path.basename(path))[0]  # 확장자 제거
        parts = name.split('_')
        # 언더스코어가 2개 이상 → 날짜_이름_페이지 구조로 판단
        if len(parts) >= 3:
            slide_pngs.append(path)
    return slide_pngs


def convert_to_webp(png_path):
    """
    PNG → WebP 변환 후 archive/ 에 저장
    반환값: 저장된 webp 파일명 (경로 제외)
    """
    basename = os.path.basename(png_path)                  # 260206_SM_01.png
    name_no_ext = os.path.splitext(basename)[0]            # 260206_SM_01
    webp_name = name_no_ext + '.webp'                      # 260206_SM_01.webp
    webp_path = os.path.join(ARCHIVE_DIR, webp_name)      # images/archive/260206_SM_01.webp

    # 이미 변환된 파일이면 스킵 (중복 처리 방지)
    if os.path.exists(webp_path):
        print(f"  [스킵] 이미 존재: {webp_name}")
        return webp_name

    with Image.open(png_path) as img:
        img = img.convert('RGB')  # PNG 투명도(RGBA) → RGB 변환
        img.save(webp_path, 'WEBP', quality=WEBP_QUALITY)

    print(f"  [변환] {basename} → {webp_name}")
    return webp_name


def archive_original(png_path):
    """원본 PNG를 archive/ 로 이동 (webp와 같은 폴더, 원본 보존)"""
    basename = os.path.basename(png_path)
    dest = os.path.join(ARCHIVE_DIR, basename)

    # 동일 파일명이 이미 있으면 시간 suffix 추가
    if os.path.exists(dest):
        name, ext = os.path.splitext(basename)
        ts = datetime.now().strftime('%H%M%S')
        dest = os.path.join(ARCHIVE_DIR, f'{name}_{ts}{ext}')

    shutil.move(png_path, dest)
    print(f"  [이동] {basename} → archive/")


def parse_filename(webp_name):
    """
    260206_SM_01.webp → (date='260206', label='SM', page=1)
    페이지 번호는 정렬용 int로 반환
    """
    name = os.path.splitext(webp_name)[0]   # 260206_SM_01
    parts = name.split('_')
    date  = parts[0]                          # 260206
    page  = parts[-1]                         # 01
    label = '_'.join(parts[1:-1])             # SM  (중간 전부, 이름에 _ 포함 허용)
    return date, label, int(page) if page.isdigit() else 0


def build_list_json():
    """
    archive/ 폴더의 webp 파일 전체를 스캔하여 list.json 재생성
    결과 구조:
    {
      "260207": { "WTI": ["260207_WTI_01.webp", "260207_WTI_02.webp"] },
      "260206": { "SM":  ["260206_SM_01.webp",  "260206_SM_02.webp"]  }
    }
    날짜 내림차순 정렬 (최신이 위)
    """
    # archive/ 폴더의 webp 파일 전체 수집
    all_webps = [
        f for f in os.listdir(ARCHIVE_DIR)
        if f.endswith('.webp') and len(f.split('_')) >= 3  # 슬라이드 파일만
    ]

    data = {}  # {날짜: {이름: [파일목록]}}

    for webp_name in all_webps:
        try:
            date, label, page_num = parse_filename(webp_name)
        except Exception:
            continue  # 파싱 실패 파일 무시

        if date not in data:
            data[date] = {}
        if label not in data[date]:
            data[date][label] = []
        data[date][label].append((page_num, webp_name))

    # 각 라벨 내 페이지번호 오름차순 정렬 후 파일명만 추출
    result = {}
    for date in sorted(data.keys(), reverse=True):  # 날짜 내림차순
        result[date] = {}
        for label in sorted(data[date].keys()):      # 이름 알파벳순
            pages = sorted(data[date][label], key=lambda x: x[0])  # 페이지 오름차순
            result[date][label] = [p[1] for p in pages]

    with open(LIST_JSON, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n[list.json 갱신] 총 {len(result)}개 날짜 기록됨")
    return result


def process():
    """메인 실행 함수"""
    print("=" * 50)
    print("슬라이드 아카이브 변환 시작")
    print("=" * 50)

    ensure_dirs()

    # 1. 슬라이드 PNG 탐지
    slide_pngs = find_slide_pngs()
    if slide_pngs:
        print(f"\n[발견] 슬라이드 PNG {len(slide_pngs)}개")
        for png_path in sorted(slide_pngs):
            convert_to_webp(png_path)   # webp 변환
            archive_original(png_path)  # 원본 이동
    else:
        print("\n[알림] 새로운 슬라이드 PNG 없음")

    # 2. list.json 재생성 (항상 실행)
    build_list_json()

    print("\n완료!")


if __name__ == '__main__':
    process()
