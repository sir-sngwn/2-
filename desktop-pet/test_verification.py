#!/usr/bin/env python3
"""
Desktop Pet - Verification Test Script (Photo & Character Edition)
에셋 파이프라인 및 런타임 엔진 정적/동적 검증 스크립트.
일반 캐릭터 및 연예인/실사 인물 사진 모드를 포괄 검증합니다.
"""

import sys
import os
import random
import py_compile
from pathlib import Path
from PIL import Image, ImageDraw

def test_py_compile():
    print("1️⃣ 파이썬 스크립트 구문 컴파일 검증 중...")
    base_dir = Path(__file__).parent
    py_compile.compile(str(base_dir / "asset_pipeline.py"), doraise=True)
    py_compile.compile(str(base_dir / "pet.py"), doraise=True)
    print("  ✅ asset_pipeline.py 및 pet.py 컴파일 성공!")

def test_assets():
    print("2️⃣ 생성된 스프라이트 에셋 규격 검증 중...")
    assets_dir = Path(__file__).parent / "assets"
    
    expected_categories = {
        "idle": 4,
        "walk": 8,
        "fall": 2,
        "drag": 2,
        "sit": 2,
    }
    
    for category, expected_count in expected_categories.items():
        cat_dir = assets_dir / category
        assert cat_dir.exists(), f"디렉터리 누락: {cat_dir}"
        pngs = list(cat_dir.glob("*.png"))
        assert len(pngs) >= expected_count, f"{category} 프레임 수 부족: {len(pngs)} < {expected_count}"
        
        sample_img = Image.open(pngs[0])
        assert sample_img.size == (128, 128), f"크기 불일치: {sample_img.size} != (128, 128)"
        assert sample_img.mode == "RGBA", f"모드 불일치: {sample_img.mode} != RGBA"
        
        print(f"  ✅ {category} ({len(pngs)} frames, 128x128 RGBA) 검증 완료")

def test_celebrity_photo_pipeline():
    print("3️⃣ 연예인/실사 인물 사진 처리 및 스티커 테두리 검증 중...")
    from asset_pipeline import process_image, detect_is_photo, apply_sticker_border
    
    # 1. 다양한 색상 그라디언트 및 피부톤을 가진 가상의 실사 인물 사진 생성 (250x350)
    photo_w, photo_h = 240, 320
    test_photo = Image.new("RGB", (photo_w, photo_h), (240, 240, 245))
    draw = ImageDraw.Draw(test_photo)
    
    # 배경 그라디언트 노이즈 (실제 사진 시뮬레이션)
    for y in range(photo_h):
        for x in range(photo_w):
            r = (180 + (x * 70 // photo_w) + (y * 20 // photo_h)) % 256
            g = (190 + (y * 60 // photo_h)) % 256
            b = (200 + (x * 40 // photo_w)) % 256
            draw.point((x, y), fill=(r, g, b))
            
    # 인물 얼굴 및 상반신 (피부톤 & 의류)
    draw.ellipse([80, 50, 160, 150], fill=(255, 218, 185))  # 얼굴
    draw.polygon([(60, 140), (180, 140), (210, 310), (30, 310)], fill=(40, 45, 60)) # 의류
    
    photo_path = Path("/tmp/test_celebrity_photo.jpg")
    test_photo.save(photo_path)
    
    # 실사 사진 판별 함수 테스트
    is_photo = detect_is_photo(test_photo)
    print(f"  🔍 실사 사진 자동 감지 여부: {is_photo}")
    
    # 스티커 테두리 함수 테스트
    test_rgba = test_photo.convert("RGBA")
    bordered = apply_sticker_border(test_rgba, stroke_width=4)
    assert bordered.size == test_photo.size, "스티커 테두리 크기 불일치"
    
    # 에셋 파이프라인 실사 모드 실행 테스트
    photo_out_dir = Path("/tmp/test_photo_assets")
    process_image(str(photo_path), str(photo_out_dir), mode="photo", stroke_width=3)
    
    # 생성된 프레임 무결성 확인
    for state in ["idle", "walk", "fall", "drag", "sit"]:
        state_dir = photo_out_dir / state
        assert state_dir.exists(), f"실사 모드 {state} 디렉터리 누락"
        frames = list(state_dir.glob("*.png"))
        assert len(frames) > 0, f"실사 모드 {state} 프레임 없음"
        sample = Image.open(frames[0])
        assert sample.mode == "RGBA", "실사 모드 RGBA 누락"
        assert sample.size == (128, 128), "실사 모드 규격 불일치"
        
    print("  ✅ 연예인/실사 인물 사진 파이프라인 검증 완료!")

if __name__ == "__main__":
    try:
        test_py_compile()
        test_assets()
        test_celebrity_photo_pipeline()
        print("\n🎉 모든 자동화 검증 테스트를 성공적으로 통과했습니다!")
    except Exception as e:
        print(f"\n❌ 검증 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
