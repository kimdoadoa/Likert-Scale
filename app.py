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
    이미지 경로를 로드하고, 쌍으로 묶은 뒤 랜덤으로 섞어서 반환합니다.
    """
    st.session_state.image_pairs = []
    
    # DAB 이미지 쌍 찾기
    dab_he_paths = natsorted(glob(os.path.join(directory, 'HE_DAB_*.png')))
    for he_path in dab_he_paths:
        base_name = os.path.basename(he_path).replace('HE_', '')
        # Ground Truth와 Synthesized IHC 경로 찾기
        gt_ihc_path = os.path.join(directory, f"IHC_GT_{base_name}")
        synth_ihc_path = os.path.join(directory, f"IHC_Synth_{base_name}")
        
        if os.path.exists(gt_ihc_path):
            st.session_state.image_pairs.append({'he': he_path, 'ihc': gt_ihc_path, 'type': 'ground_truth', 'stain': 'DAB'})
        if os.path.exists(synth_ihc_path):
            st.session_state.image_pairs.append({'he': he_path, 'ihc': synth_ihc_path, 'type': 'synthesized', 'stain': 'DAB'})

    # Fast Red 이미지 쌍 찾기
    fastred_he_paths = natsorted(glob(os.path.join(directory, 'HE_FastRed_*.png')))
    for he_path in fastred_he_paths:
        base_name = os.path.basename(he_path).replace('HE_', '')
        gt_ihc_path = os.path.join(directory, f"IHC_GT_{base_name}")
        synth_ihc_path = os.path.join(directory, f"IHC_Synth_{base_name}")

        if os.path.exists(gt_ihc_path):
            st.session_state.image_pairs.append({'he': he_path, 'ihc': gt_ihc_path, 'type': 'ground_truth', 'stain': 'FastRed'})
        if os.path.exists(synth_ihc_path):
            st.session_state.image_pairs.append({'he': he_path, 'ihc': synth_ihc_path, 'type': 'synthesized', 'stain': 'FastRed'})

    # 각 사용자의 세션마다 순서를 무작위로 섞음 (핵심 기능)
    random.shuffle(st.session_state.image_pairs)

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
if not st.session_state.image_pairs:
    st.error("이미지를 찾을 수 없습니다. GitHub 저장소의 `images` 폴더 구조를 확인해주세요.")
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
    
    # 사이드바에 진행 상황 및 안내 표시
    st.sidebar.title("Reader Study")
    st.sidebar.write(f"**Image Pair: {current_image_num} / {total_images}**")
    st.sidebar.progress(current_image_num / total_images)
    st.sidebar.markdown("---")
    st.sidebar.info("오른쪽 IHC 이미지의 현실성을 1점에서 5점까지 평가해주세요.")

    # 현재 평가할 이미지 쌍 정보
    current_pair = st.session_state.image_pairs[st.session_state.current_index]
    he_path = current_pair['he']
    ihc_path = current_pair['ihc']

    # 화면을 두 개의 컬럼으로 분할
    col1, col2 = st.columns(2)

    with col1:
        st.header("H&E Image")
        st.image(he_path, use_container_width=True)

    with col2:
        st.header("IHC Image")
        st.image(ihc_path, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True) # 줄바꿈

    # 5점 리커트 척도 입력
    realism_score = st.radio(
        "**How realistic is the IHC image?** (1 = Completely unrealistic, 5 = Indistinguishable from real)",
        options=[1, 2, 3, 4, 5],
        index=2, # 기본값을 3으로 설정
        horizontal=True,
        key=f"score_{st.session_state.current_index}"
    )

    # 저장 및 다음 버튼
    if st.button("Save and Next Image", key="next_button", use_container_width=True):
        st.session_state.results.append({
            'pair_order': current_image_num,
            'he_image': os.path.basename(he_path),
            'ihc_image': os.path.basename(ihc_path),
            'image_type': current_pair['type'],
            'stain_type': current_pair['stain'],
            'realism_score': realism_score
        })
        
        st.session_state.current_index += 1
        st.rerun()
