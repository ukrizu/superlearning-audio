import streamlit as st
from gtts import gTTS
from pydub import AudioSegment
import os
import tempfile
from openai import OpenAI
import re

st.set_page_config(page_title="Spanish-Czech Audio Generator", page_icon="🇪🇸", layout="wide")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

with st.sidebar:
    st.header("⚙️ Settings")
    
    pause_duration = st.slider(
        "Pause between pairs (ms)",
        min_value=1000,
        max_value=5000,
        value=3200,
        step=100,
        help="Duration of silence between Czech-Spanish pairs"
    )
    
    czech_speedup = st.slider(
        "Czech playback speed",
        min_value=1.0,
        max_value=1.5,
        value=1.15,
        step=0.05,
        help="Speed multiplier for Czech audio (1.0 = normal speed)"
    )
    
    st.markdown("---")
    st.caption("💡 Tip: Adjust settings before generating audio")

def detect_delimiter(line):
    """Auto-detect delimiter in a line."""
    delimiters = ['\t', '|', ';', ',']
    for delimiter in delimiters:
        if delimiter in line:
            parts = [p.strip() for p in line.split(delimiter)]
            if len(parts) == 2 and parts[0] and parts[1]:
                return delimiter
    return None

def translate_to_czech(spanish_texts):
    """Translate Spanish to Czech using OpenAI."""
    translated = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, text in enumerate(spanish_texts):
        status_text.text(f"Translating {i+1}/{len(spanish_texts)}: {text[:50]}...")
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Translate the following Spanish text to Czech. Return only the translation."},
                    {"role": "user", "content": text}
                ],
            )
            cz = (resp.choices[0].message.content or "").strip()
        except Exception as e:
            cz = f"[Translation error: {e}]"
            st.warning(f"Translation failed for: {text}")
        translated.append(cz)
        progress_bar.progress((i + 1) / len(spanish_texts))
    
    progress_bar.empty()
    status_text.empty()
    return translated

def generate_audio(sentences, output_path, pause_ms, speedup):
    """Generate combined MP3 from Czech-Spanish sentence pairs."""
    final_audio = AudioSegment.silent(0)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, (cz, es) in enumerate(sentences, 1):
        status_text.text(f"Generating audio {i}/{len(sentences)}: {es[:50]}...")
        
        cz_tts = gTTS(text=cz, lang="cs")
        cz_path = os.path.join(tempfile.gettempdir(), f"cz_{i}.mp3")
        cz_tts.save(cz_path)
        cz_audio = AudioSegment.from_mp3(cz_path).speedup(playback_speed=speedup)
        
        es_tts = gTTS(text=es, lang="es")
        es_path = os.path.join(tempfile.gettempdir(), f"es_{i}.mp3")
        es_tts.save(es_path)
        es_audio = AudioSegment.from_mp3(es_path)
        
        final_audio += cz_audio + es_audio + AudioSegment.silent(pause_ms)
        
        os.remove(cz_path)
        os.remove(es_path)
        
        progress_bar.progress(i / len(sentences))
    
    progress_bar.empty()
    status_text.empty()
    
    final_audio.export(output_path, format="mp3")

def parse_file(uploaded_file):
    """Parse uploaded file and detect format."""
    text = uploaded_file.read().decode("utf-8").strip()
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    
    if not lines:
        return None, "File is empty", None
    
    delimiter = detect_delimiter(lines[0])
    
    if delimiter:
        delimiter_name = {'\t': 'tab', '|': 'pipe', ';': 'semicolon', ',': 'comma'}.get(delimiter, delimiter)
        sentences = []
        for l in lines:
            parts = [p.strip() for p in l.split(delimiter)]
            if len(parts) == 2 and parts[0] and parts[1]:
                cz, es = parts
                sentences.append([cz, es])
            else:
                return None, f"Invalid format in line: {l}", None
        return sentences, f"Detected {len(sentences)} Czech-Spanish pairs (delimiter: {delimiter_name})", False
    else:
        spanish_only = lines
        return spanish_only, f"Detected {len(spanish_only)} Spanish-only phrases", True

st.title("🇪🇸→🇨🇿 Spanish Audio Generator")
st.write("Upload text files with Spanish phrases or Spanish-Czech pairs to generate language learning audio.")

col1, col2 = st.columns([2, 1])

with col2:
    st.markdown("""
    ### 📄 File Format
    
    **Czech-Spanish pairs** (any delimiter):
    ```
    Dobrý den|Buenos días
    Jak se máš?;¿Cómo estás?
    Děkuji,Gracias
    ```
    
    **Spanish only** (auto-translate):
    ```
    Buenos días
    ¿Cómo estás?
    Gracias
    ```
    
    Supported delimiters: `|` `;` `,` `tab`
    """)

with col1:
    uploaded_files = st.file_uploader(
        "Upload your phrases file(s) (.txt)", 
        type=["txt"],
        accept_multiple_files=True
    )

if uploaded_files:
    if len(uploaded_files) > 1:
        st.info(f"📦 Processing {len(uploaded_files)} files in batch mode")
    
    all_sentences = []
    needs_translation = False
    spanish_only_texts = []
    
    for uploaded_file in uploaded_files:
        st.subheader(f"📄 {uploaded_file.name}")
        
        result, message, is_spanish_only = parse_file(uploaded_file)
        
        if result is None:
            st.error(f"Error: {message}")
            continue
        
        st.success(message)
        
        if is_spanish_only:
            needs_translation = True
            spanish_only_texts.extend(result)
        else:
            all_sentences.extend(result)
    
    if needs_translation and spanish_only_texts:
        st.info(f"Translating {len(spanish_only_texts)} Spanish phrases to Czech...")
        czech = translate_to_czech(spanish_only_texts)
        translated_pairs = [[cz, es] for cz, es in zip(czech, spanish_only_texts)]
        all_sentences.extend(translated_pairs)
    
    if all_sentences:
        st.success(f"✅ Total: {len(all_sentences)} phrase pairs ready")
        
        import hashlib
        content_hash = hashlib.md5(str(all_sentences).encode()).hexdigest()
        
        if 'content_hash' not in st.session_state or st.session_state.content_hash != content_hash:
            st.session_state.content_hash = content_hash
            st.session_state.current_sentences = all_sentences.copy()
            for key in list(st.session_state.keys()):
                if isinstance(key, str) and (key.startswith('cz_') or key.startswith('es_')):
                    del st.session_state[key]
        
        with st.expander("📝 Preview & Edit Translations", expanded=False):
            st.write("You can edit the Czech translations before generating audio:")
            
            for i, (cz, es) in enumerate(st.session_state.current_sentences[:20], 1):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.text_input(
                        f"Czech #{i}",
                        value=cz,
                        key=f"cz_{i}",
                        label_visibility="collapsed"
                    )
                with col_b:
                    st.text_input(
                        f"Spanish #{i}",
                        value=es,
                        key=f"es_{i}",
                        disabled=True,
                        label_visibility="collapsed"
                    )
            
            if len(st.session_state.current_sentences) > 20:
                st.info(f"Showing first 20 of {len(st.session_state.current_sentences)} pairs. All pairs will be included in audio.")
        
        sentences_to_use = []
        for i, (cz, es) in enumerate(st.session_state.current_sentences, 1):
            edited_cz = st.session_state.get(f"cz_{i}", cz) if i <= 20 else cz
            sentences_to_use.append([edited_cz, es])
        
        if st.button("🎵 Generate Audio", type="primary", use_container_width=True):
            with st.spinner("Generating audio file..."):
                output_path = os.path.join(tempfile.gettempdir(), "spanish_audio.mp3")
                
                try:
                    generate_audio(sentences_to_use, output_path, pause_duration, czech_speedup)
                    st.success("🎉 Audio generated successfully!")
                    
                    with open(output_path, "rb") as audio_file:
                        audio_bytes = audio_file.read()
                    
                    st.audio(audio_bytes, format="audio/mp3")
                    
                    st.download_button(
                        label="⬇️ Download MP3",
                        data=audio_bytes,
                        file_name=f"spanish_czech_audio_{len(sentences_to_use)}_phrases.mp3",
                        mime="audio/mp3",
                        use_container_width=True
                    )
                    
                except Exception as e:
                    st.error(f"Error generating audio: {e}")

st.markdown("---")
st.caption(f"Audio format: Czech ({czech_speedup}x speed) → Spanish → {pause_duration}ms pause")
