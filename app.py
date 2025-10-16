import streamlit as st
import pandas as pd
import os
import random
from glob import glob
from natsort import natsorted

# --- 1. 설정 (Configuration) ---
IMAGE_DIR = './images'
OUTPUT_CSV_NAME = 'realism_study_results.csv'

# --- 2. 데이터 로딩 및 준비 ---
def load_and_prepare_data(directory):
    """
    새로운 파일 이름 규칙에 맞춰 이미지 경로를 로드하고,
    쌍으로 묶은 뒤 랜덤으로 섞어서 반환합니다.
    """
    image_pairs = []
    
    # HE 이미지 전체를 먼저 찾습니다.
    all_he_paths = natsorted(glob(os.path.join(directory, 'HE_*.png')))

    # 각 HE 이미지에 대해 짝이 되는 IHC 이미지를 찾습니다.
    for he_path in all_he_paths:
        # 'HE_brown_1.png' -> 'brown_1'
        base_name = os.path.basename(he_path).replace('HE_', '').replace('.png', '')
        
        # 'brown' 또는 'red' 구분
        stain_type = "brown" if "brown" in base_name else "red"

        # 해당 HE 이미지와 쌍을 이루는 Ground Truth 및 Fake IHC 경로 생성
        gt_ihc_path = os.path.join(directory, f"IHC_{base_name}_gt.png")
        fake_ihc_path = os.path.join(directory, f"IHC_{base_name}_fake.png")

        # 파일이 실제로 존재하면 리스트에 추가
        if os.path.exists(gt_ihc_path):
            image_pairs.append({'he': he_path, 'ihc': gt_ihc_path, 'type': 'ground_truth', 'stain': stain_type})
        if os.path.exists(fake_ihc_path):
            image_pairs.append({'he': he_path, 'ihc': fake_ihc_path, 'type': 'synthesized', 'stain': stain_type})
    
    if not image_pairs:
        st.error(f"이미지 폴더('{directory}')에서 유효한 이미지 쌍을 찾을 수 없습니다. 파일 이름을 확인해주세요. (예: HE_brown_1.png, IHC_brown_1_gt.png)")

    # 각 사용자의 세션마다 순서를 무작위로 섞음 (핵심 기능)
    random.shuffle(image_pairs)
    st.session_state.image_pairs = image_pairs

# --- 3. 세션 상태 초기화 ---
if 'image_pairs' not in st.session_state:
    load_and_prepare_data(IMAGE_DIR)

if 'current_index' not in st.session_state:
    st.session_state.current_index = 0

if 'results' not in st.session_state:
    st.session_state.results = []

# --- 4. 메인 UI 구성 ---
st.set_page_config(layout="wide")
st.title("🔬 Realism Evaluation of Synthesized IHC Images")

# 모든 평가가 끝났는지 확인
if not st.session_state.image_pairs and 'error_message_shown' not in st.session_state:
     # load_and_prepare_data 함수에서 에러 메시지를 이미 표시했으므로 여기서는 아무것도 안 함
     # 무한 루프 방지를 위해 플래그 사용
     st.session_state.error_message_shown = True

elif st.session_state.current_index >= len(st.session_state.image_pairs):
    st.success("🎉 모든 평가가 완료되었습니다. 수고하셨습니다!")
    st.info("아래 버튼을 눌러 결과 파일을 다운로드하세요.")
    
    final_df = pd.DataFrame(st.session_state.results)
    st.dataframe(final_df)
    
    csv = final_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Results as CSV",
        data=csv,
        file_name=OUTPUT_CSV_NAME,
        mime="text/csv",
    )
else:
    total_images = len(st.session_state.image_pairs)
    current_image_num = st.session_state.current_index + 1
    
    st.sidebar.title("Reader Study")
    st.sidebar.write(f"**Image Pair: {current_image_num} / {total_images}**")
    st.sidebar.progress(current_image_num / total_images)
    st.sidebar.markdown("---")
    st.sidebar.info("오른쪽 IHC 이미지의 현실성을 1점에서 5점까지 평가해주세요.")

    current_pair = st.session_state.image_pairs[st.session_state.current_index]
    he_path = current_pair['he']
    ihc_path = current_pair['ihc']

    col1, col2 = st.columns(2)

    with col1:
        st.header("H&E Image")
        st.image(he_path, use_container_width=True)

    with col2:
        st.header("IHC Image")
        st.image(ihc_path, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    realism_score = st.radio(
        "**How realistic is the IHC image?** (1 = Completely unrealistic, 5 = Indistinguishable from real)",
        options=[1, 2, 3, 4, 5],
        index=2,
        horizontal=True,
        key=f"score_{st.session_state.current_index}"
    )

    if st.button("Save and Next Image", key="next_button", use_container_width=True):
        st.session_state.results.append({
            'pair_order_for_user': current_image_num,
            'he_image': os.path.basename(he_path),
            'ihc_image': os.path.basename(ihc_path),
            'image_type': current_pair['type'],
            'stain_type': current_pair['stain'],
            'realism_score': realism_score
        })
        
        st.session_state.current_index += 1
        st.rerun()
