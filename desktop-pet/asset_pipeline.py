#!/usr/bin/env python3
"""
Desktop Pet - Asset Pipeline (Photo & Character Edition)
단일 캐릭터 이미지 또는 연예인/인물 실사 사진으로부터
AI 인물 누끼(Alpha Masking), 스티커 외곽선(Sticker Border),
얼굴 왜곡 없는 자연스러운 포즈 스프라이트를 자동 생성합니다.
"""

import os
import sys
import math
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageOps

DEFAULT_SIZE = (128, 128)


def detect_is_photo(image: Image.Image) -> bool:
    """
    이미지가 실사 사진(연예인, 인물, 사진)인지 판별합니다.
    색상 다양성(Unique colors) 및 그라디언트 텍스처를 분석합니다.
    """
    thumb = image.resize((80, 80)).convert("RGB")
    colors = thumb.getcolors(maxcolors=80 * 80)
    num_unique = len(colors) if colors else 5000
    # 80x80 썸네일 기준 450개 이상의 다양한 색상/그라디언트가 있으면 실사 사진으로 판별
    return num_unique > 450



def remove_background(image: Image.Image, is_photo: bool = False) -> Image.Image:
    """
    이미지의 배경을 감지하고 투명(RGBA)으로 변환합니다.
    1. rembg 모듈 시도 (실사 인물일 경우 u2net_human_seg 세션 활용)
    2. rembg 미설치 시: 사진/일러스트 맞춤형 외곽 시드 기반 누끼 및 알파 페더링 적용
    """
    # 1. rembg AI 인물 분리 시도
    try:
        import rembg
        print("🧠 AI 배경 제거 모델(rembg)을 사용하여 인물을 분리합니다...")
        if is_photo:
            try:
                session = rembg.new_session("u2net_human_seg")
                return rembg.remove(image, session=session)
            except Exception:
                return rembg.remove(image)
        else:
            return rembg.remove(image)
    except ImportError:
        pass

    # 2. 내장 고성능 누끼 알고리즘 (PIL)
    img = image.convert("RGBA")
    width, height = img.size
    pixels = img.load()

    # 이미 투명 픽셀이 상당수 있는 경우 원본 알파 채널 보존
    transparent_count = 0
    sample_step = max(1, width // 20)
    for y in range(0, height, sample_step):
        for x in range(0, width, sample_step):
            if pixels[x, y][3] < 180:
                transparent_count += 1
    if transparent_count > 15:
        print("💡 이미지에 기존 투명 배경이 감지되어 이를 유지합니다.")
        return img

    print("✂️ 내장 스마트 배경 분리 알고리즘을 적용합니다...")

    # 외곽 모퉁이 및 테두리 색상 샘플링
    corner_samples = [
        pixels[0, 0][:3],
        pixels[width - 1, 0][:3],
        pixels[0, height - 1][:3],
        pixels[width - 1, height - 1][:3],
        pixels[width // 2, 0][:3],
        pixels[0, height // 2][:3],
        pixels[width - 1, height // 2][:3],
    ]
    bg_color = corner_samples[0]

    def color_dist(c1, c2):
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))

    visited = bytearray(width * height)
    queue = []

    # 네 가장자리 픽셀을 큐에 삽입
    for x in range(width):
        queue.append((x, 0))
        queue.append((x, height - 1))
    for y in range(height):
        queue.append((0, y))
        queue.append((width - 1, y))

    # 실사 사진인 경우 더 부드러운 허용 오차 적용
    tolerance = 42.0 if is_photo else 36.0

    while queue:
        cx, cy = queue.pop(0)
        idx = cy * width + cx
        if visited[idx]:
            continue
        visited[idx] = 1

        curr_rgb = pixels[cx, cy][:3]
        if color_dist(curr_rgb, bg_color) <= tolerance:
            # 배경 투명화
            pixels[cx, cy] = (curr_rgb[0], curr_rgb[1], curr_rgb[2], 0)

            for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                if 0 <= nx < width and 0 <= ny < height:
                    nidx = ny * width + nx
                    if not visited[nidx]:
                        queue.append((nx, ny))

    # 부드러운 안티앨리어싱 및 페더링
    alpha = img.split()[3]
    radius = 1.0 if is_photo else 0.5
    alpha = alpha.filter(ImageFilter.GaussianBlur(radius=radius))
    img.putalpha(alpha)
    return img


def apply_sticker_border(
    image: Image.Image,
    stroke_width: int = 3,
    stroke_color: tuple = (255, 255, 255, 255),
    shadow: bool = True
) -> Image.Image:
    """
    실사 인물 사진이 어둡거나 밝은 바탕화면에서도 또렷하게 보이도록
    깔끔한 화이트 스티커 외곽선(Sticker Border)과 부드러운 그림자를 추가합니다.
    """
    if stroke_width <= 0:
        return image

    img = image.convert("RGBA")
    w, h = img.size
    alpha = img.split()[3]

    # 알파 채널 팽창(Dilation)으로 스티커 테두리 마스크 생성
    filter_size = max(3, 2 * stroke_width + 1)
    dilated_alpha = alpha.filter(ImageFilter.MaxFilter(filter_size))
    # 둥근 모서리 스무딩
    dilated_alpha = dilated_alpha.filter(ImageFilter.GaussianBlur(radius=0.7))

    # 스티커 테두리 레이어
    stroke_layer = Image.new("RGBA", (w, h), stroke_color)
    stroke_layer.putalpha(dilated_alpha)

    # 미세 그림자 레이어 (옵션)
    if shadow:
        shadow_alpha = dilated_alpha.filter(ImageFilter.GaussianBlur(radius=1.8))
        shadow_layer = Image.new("RGBA", (w, h), (0, 0, 0, 70))
        # 1px 아래로 오프셋
        shadow_offset = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        shadow_offset.paste(shadow_layer, (0, 1), shadow_alpha)
        # 그림자 + 테두리 + 원본 합성
        combined = Image.alpha_composite(shadow_offset, stroke_layer)
        return Image.alpha_composite(combined, img)
    else:
        return Image.alpha_composite(stroke_layer, img)


def normalize_sprite(image: Image.Image, target_size=DEFAULT_SIZE) -> Image.Image:
    """
    캐릭터 바운딩 박스를 계산하여 불필요한 여백을 자르고,
    바닥 정렬(Bottom-aligned)된 target_size 캔버스 중앙에 배치합니다.
    인물 실사 사진의 세로 비율을 완벽히 보존합니다.
    """
    img = image.convert("RGBA")
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)

    bw, bh = img.size
    tw, th = target_size

    # 캔버스 내 최대 점유 비율 (86%)
    max_w = int(tw * 0.86)
    max_h = int(th * 0.86)

    scale = min(max_w / bw, max_h / bh)
    new_w = max(1, int(bw * scale))
    new_h = max(1, int(bh * scale))

    scaled = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", target_size, (0, 0, 0, 0))
    pos_x = (tw - new_w) // 2
    pos_y = th - new_h - 4  # 바닥 4px 여유

    canvas.paste(scaled, (pos_x, pos_y), scaled)
    return canvas


def transform_pose(
    base: Image.Image,
    scale_x=1.0,
    scale_y=1.0,
    angle=0.0,
    dy=0,
    dx=0,
    flip_h=False,
    is_photo=False
) -> Image.Image:
    """
    스프라이트를 크기/각도/위치 변형합니다.
    실사 사진(is_photo=True)일 경우 얼굴이 찌그러지지 않도록 스케일 변형을 억제하고,
    자연스러운 보블(Bobble) 및 틸트(Tilt) 모션을 우선 적용합니다.
    """
    img = base.copy()
    w, h = img.size

    bbox = img.getbbox()
    if not bbox:
        return img
    char_crop = img.crop(bbox)
    cw, ch = char_crop.size

    # 실사 사진은 얼굴/체형 비율 보존을 위해 스케일 변형 폭을 미세화 (최대 1~2%)
    if is_photo:
        eff_scale_x = 1.0 + (scale_x - 1.0) * 0.25
        eff_scale_y = 1.0 + (scale_y - 1.0) * 0.25
    else:
        eff_scale_x = scale_x
        eff_scale_y = scale_y

    target_cw = max(4, int(cw * eff_scale_x))
    target_ch = max(4, int(ch * eff_scale_y))
    transformed = char_crop.resize((target_cw, target_ch), Image.Resampling.LANCZOS)

    # 회전
    if angle != 0:
        transformed = transformed.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)

    # 좌우 반전
    if flip_h:
        transformed = ImageOps.mirror(transformed)

    tw, th = transformed.size

    # 바닥/중심 기준 캔버스에 배치
    result = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    center_x = (bbox[0] + bbox[2]) // 2 + dx
    bottom_y = bbox[3] + dy

    paste_x = center_x - tw // 2
    paste_y = bottom_y - th

    result.paste(transformed, (paste_x, paste_y), transformed)
    return result


def draw_sleep_particles(image: Image.Image, stage: int) -> Image.Image:
    """수면(Sleep/Sit) 상태일 때 'z' 이펙트 파티클을 렌더링합니다."""
    img = image.copy()
    draw = ImageDraw.Draw(img)
    w, h = img.size
    
    z_color = (130, 180, 255, 230)
    if stage == 0:
        draw.text((w - 38, 14), "z", fill=z_color)
    else:
        draw.text((w - 44, 20), "z", fill=z_color)
        draw.text((w - 32, 8), "Z", fill=(100, 160, 255, 250))
    return img


def generate_all_states(base_sprite: Image.Image, output_dir: Path, is_photo: bool = False):
    """
    표준 5개 상태(idle, walk, fall, drag, sit)의 스프라이트 프레임 파일들을 생성합니다.
    """
    norm = normalize_sprite(base_sprite, DEFAULT_SIZE)

    # 1. IDLE (4 frames)
    idle_dir = output_dir / "idle"
    idle_dir.mkdir(parents=True, exist_ok=True)
    if is_photo:
        # 실사 사진: 얼굴 왜곡 없이 부드러운 상하 부유 및 미세 갸우뚱
        idle_frames = [
            transform_pose(norm, angle=0.0, dy=0, is_photo=True),
            transform_pose(norm, angle=1.5, dy=1, is_photo=True),
            transform_pose(norm, angle=0.0, dy=0, is_photo=True),
            transform_pose(norm, angle=-1.5, dy=-1, is_photo=True),
        ]
    else:
        idle_frames = [
            transform_pose(norm, scale_x=1.00, scale_y=1.00, dy=0),
            transform_pose(norm, scale_x=1.03, scale_y=0.97, dy=1),
            transform_pose(norm, scale_x=1.00, scale_y=1.00, dy=0),
            transform_pose(norm, scale_x=0.98, scale_y=1.02, dy=-1),
        ]
    for i, frame in enumerate(idle_frames):
        frame.save(idle_dir / f"idle_{i}.png")

    # 2. WALK (8 frames: walk_left 4 frames, walk_right 4 frames)
    walk_dir = output_dir / "walk"
    walk_dir.mkdir(parents=True, exist_ok=True)
    walk_angle = 6.0 if is_photo else 8.0
    walk_right_frames = [
        transform_pose(norm, angle=-walk_angle * 0.5, dy=-2, dx=2, is_photo=is_photo),
        transform_pose(norm, angle=-walk_angle, dy=1, dx=4, is_photo=is_photo),
        transform_pose(norm, angle=-walk_angle * 0.5, dy=-2, dx=2, is_photo=is_photo),
        transform_pose(norm, angle=0.0, dy=0, dx=0, is_photo=is_photo),
    ]
    for i, frame in enumerate(walk_right_frames):
        frame.save(walk_dir / f"walk_right_{i}.png")
        # 왼쪽 걷기 (수평 반전)
        left_frame = transform_pose(norm, angle=-walk_angle * 0.5, dy=-2, dx=2, flip_h=True, is_photo=is_photo) if i % 2 == 0 \
            else transform_pose(norm, angle=-walk_angle, dy=1, dx=4, flip_h=True, is_photo=is_photo)
        left_frame.save(walk_dir / f"walk_left_{i}.png")

    # 3. FALL (2 frames): 공중 낙하 시 회전 및 체공
    fall_dir = output_dir / "fall"
    fall_dir.mkdir(parents=True, exist_ok=True)
    fall_frames = [
        transform_pose(norm, scale_x=0.94, scale_y=1.06, angle=-4, dy=-3, is_photo=is_photo),
        transform_pose(norm, scale_x=0.94, scale_y=1.06, angle=4, dy=-1, is_photo=is_photo),
    ]
    for i, frame in enumerate(fall_frames):
        frame.save(fall_dir / f"fall_{i}.png")

    # 4. DRAG (2 frames): 마우스에 매달려 덜렁거리는 상태
    drag_dir = output_dir / "drag"
    drag_dir.mkdir(parents=True, exist_ok=True)
    drag_frames = [
        transform_pose(norm, angle=-10, dy=-5, is_photo=is_photo),
        transform_pose(norm, angle=10, dy=-5, is_photo=is_photo),
    ]
    for i, frame in enumerate(drag_frames):
        frame.save(drag_dir / f"drag_{i}.png")

    # 5. SIT (2 frames): 바닥에 착지한 휴식 포즈
    sit_dir = output_dir / "sit"
    sit_dir.mkdir(parents=True, exist_ok=True)
    sit_frame_0 = transform_pose(norm, dy=3, is_photo=is_photo)
    sit_frame_1 = transform_pose(norm, dy=4, is_photo=is_photo)
    sit_frame_0 = draw_sleep_particles(sit_frame_0, 0)
    sit_frame_1 = draw_sleep_particles(sit_frame_1, 1)

    sit_frame_0.save(sit_dir / "sit_0.png")
    sit_frame_1.save(sit_dir / "sit_1.png")

    mode_label = "🌟 실사 사진(Celebrity Photo) 모드" if is_photo else "🎨 일반 캐릭터 모드"
    print(f"✨ [{mode_label}] 모든 스프라이트 프레임 생성이 완료되었습니다: {output_dir.resolve()}")


def create_default_mascot() -> Image.Image:
    """기본 마스코트(귀여운 아기 고양이 캐릭터)를 생성합니다."""
    img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    draw.ellipse([34, 108, 94, 122], fill=(0, 0, 0, 45))
    draw.polygon([(40, 60), (48, 32), (62, 54)], fill=(120, 190, 255, 255), outline=(60, 120, 210, 255))
    draw.polygon([(46, 56), (50, 40), (58, 52)], fill=(255, 175, 200, 255))
    draw.polygon([(88, 60), (80, 32), (66, 54)], fill=(120, 190, 255, 255), outline=(60, 120, 210, 255))
    draw.polygon([(82, 56), (78, 40), (70, 52)], fill=(255, 175, 200, 255))

    draw.ellipse([32, 48, 96, 114], fill=(135, 206, 250, 255), outline=(70, 130, 210, 255), width=2)
    draw.ellipse([42, 54, 60, 70], fill=(210, 240, 255, 220))

    draw.ellipse([46, 70, 56, 84], fill=(30, 40, 60, 255))
    draw.ellipse([72, 70, 82, 84], fill=(30, 40, 60, 255))
    draw.ellipse([48, 72, 52, 76], fill=(255, 255, 255, 255))
    draw.ellipse([74, 72, 78, 76], fill=(255, 255, 255, 255))
    draw.ellipse([52, 78, 54, 80], fill=(255, 255, 255, 200))
    draw.ellipse([78, 78, 80, 80], fill=(255, 255, 255, 200))

    draw.ellipse([38, 82, 48, 89], fill=(255, 140, 170, 150))
    draw.ellipse([80, 82, 90, 89], fill=(255, 140, 170, 150))
    draw.arc([58, 80, 64, 88], start=0, end=180, fill=(40, 50, 70, 255), width=2)
    draw.arc([64, 80, 70, 88], start=0, end=180, fill=(40, 50, 70, 255), width=2)

    draw.ellipse([50, 98, 62, 112], fill=(255, 255, 255, 255), outline=(70, 130, 210, 255), width=1)
    draw.ellipse([66, 98, 78, 112], fill=(255, 255, 255, 255), outline=(70, 130, 210, 255), width=1)
    return img


def find_input_image(input_path: str = None) -> str:
    """
    지정된 경로가 없으면 input/ 폴더 또는 현재 폴더에서 이미지 파일을 자동으로 탐색합니다.
    """
    if input_path and os.path.exists(input_path):
        return input_path

    search_dirs = [
        Path("input"),
        Path("desktop-pet/input"),
        Path(__file__).resolve().parent / "input",
        Path("."),
        Path("desktop-pet"),
    ]
    exts = ("*.png", "*.jpg", "*.jpeg", "*.webp", "*.PNG", "*.JPG", "*.JPEG", "*.WEBP")
    for d in search_dirs:
        if d.exists() and d.is_dir():
            for ext in exts:
                matches = sorted(list(d.glob(ext)), key=os.path.getmtime, reverse=True)
                # assets, .venv, test 파일 제외
                matches = [m for m in matches if "assets" not in str(m) and ".venv" not in str(m) and not m.name.startswith("test_")]
                if matches:
                    found = str(matches[0])
                    print(f"📁 [{d}] 폴더에서 이미지를 자동으로 감지했습니다: {found}")
                    return found
    return None


def process_image(
    input_path: str = None,
    output_dir: str = None,
    mode: str = "auto",
    stroke_width: int = 3,
    no_stroke: bool = False
):
    if output_dir is None:
        out_path = Path(__file__).resolve().parent / "assets"
    else:
        out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    resolved_input = find_input_image(input_path)

    if resolved_input and os.path.exists(resolved_input):
        print(f"📷 입력 이미지 로드: {resolved_input}")
        raw = Image.open(resolved_input)

        # 모드 판별 (auto, photo, character)
        if mode == "photo":
            is_photo = True
        elif mode == "character":
            is_photo = False
        else:
            is_photo = detect_is_photo(raw)

        print(f"🔍 이미지 분석 결과: {'[실사/인물 사진]' if is_photo else '[일반 캐릭터/일러스트]'}")
        print("✂️ 배경 누끼(Alpha Masking) 처리 중...")
        sprite = remove_background(raw, is_photo=is_photo)

        # 실사 사진이거나 사용자가 요청한 경우 스티커 테두리 적용
        if not no_stroke and (is_photo or stroke_width > 0):
            print(f"🏷️ 윈도우 바탕화면 시인성을 위한 스티커 외곽선(Stroke {stroke_width}px) 적용 중...")
            sprite = apply_sticker_border(sprite, stroke_width=stroke_width)
    else:
        print("💡 입력 이미지가 지정되지 않아 고품질 기본 마스코트를 생성합니다.")
        print("👉 나만의 사진을 쓰시려면 'input' 폴더에 사진을 넣고 다시 실행해 주세요!")
        sprite = create_default_mascot()
        is_photo = False

    generate_all_states(sprite, out_path, is_photo=is_photo)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Desktop Pet - Asset Pipeline (Photo & Character Edition)")
    parser.add_argument("input_image", nargs="?", default=None, help="단일 캐릭터 또는 연예인/인물 사진 경로")
    parser.add_argument("--output", "-o", default=None, help="에셋 출력 디렉터리 (기본값: desktop-pet/assets)")
    parser.add_argument("--mode", choices=["auto", "photo", "character"], default="auto", help="처리 모드 (auto: 자동 판별, photo: 실사 인물, character: 캐릭터)")
    parser.add_argument("--stroke-width", type=int, default=3, help="스티커 테두리 두께 (기본값: 3px)")
    parser.add_argument("--no-stroke", action="store_true", help="스티커 테두리 효과 비활성화")
    args = parser.parse_args()

    process_image(
        input_path=args.input_image,
        output_dir=args.output,
        mode=args.mode,
        stroke_width=args.stroke_width,
        no_stroke=args.no_stroke
    )
