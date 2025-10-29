import streamlit as st
from gtts import gTTS
from pydub import AudioSegment
import os
import tempfile
from openai import OpenAI
import hashlib

st.set_page_config(page_title="Superlearning Audio Generator", page_icon="🎧", layout="wide")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

LANGUAGE_OPTIONS = {
    "Czech": {"code": "cs", "flag": "🇨🇿"},
    "Spanish": {"code": "es", "flag": "🇪🇸"},
    "German": {"code": "de", "flag": "🇩🇪"}
}

with st.sidebar:
    st.header("⚙️ Settings")
    
    st.subheader("🌍 Languages")
    native_lang = st.selectbox(
        "Native language (plays faster)",
        options=list(LANGUAGE_OPTIONS.keys()),
        index=0,
        help="The language you're learning - plays at higher speed"
    )
    
    foreign_lang = st.selectbox(
        "Foreign language (reference)",
        options=list(LANGUAGE_OPTIONS.keys()),
        index=1,
        help="The language you already know - plays at normal speed"
    )
    
    if native_lang == foreign_lang:
        st.warning("⚠️ Please select different languages")
    
    st.markdown("---")
    st.subheader("🎚️ Playback Speed")
    
    native_speedup = st.slider(
        f"{native_lang} playback speed",
        min_value=1.0,
        max_value=1.5,
        value=1.15,
        step=0.05,
        help=f"Speed multiplier for {native_lang} audio (1.0 = normal speed)"
    )
    
    foreign_speedup = st.slider(
        f"{foreign_lang} playback speed",
        min_value=0.8,
        max_value=1.2,
        value=1.0,
        step=0.05,
        help=f"Speed multiplier for {foreign_lang} audio (1.0 = normal speed)"
    )
    
    st.markdown("---")
    st.subheader("⏸️ Timing")
    
    pause_duration = st.slider(
        "Pause between pairs (ms)",
        min_value=1000,
        max_value=5000,
        value=3200,
        step=100,
        help="Duration of silence between language pairs"
    )
    
    st.markdown("---")
    st.caption("💡 Tip: Adjust settings before generating audio")

def detect_delimiter(line):
    """Auto-detect delimiter in a line. Only supports | and ;"""
    delimiters = ['|', ';']
    
    # Check for multiple delimiters on the same line
    found_delimiters = [d for d in delimiters if d in line]
    if len(found_delimiters) > 1:
        return "ERROR_MULTIPLE"
    
    # Check for single delimiter
    for delimiter in delimiters:
        if delimiter in line:
            parts = [p.strip() for p in line.split(delimiter)]
            if len(parts) == 2 and parts[0] and parts[1]:
                return delimiter
    return None

def translate_text(texts, source_lang, target_lang):
    """Translate texts from source language to target language using OpenAI."""
    translated = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, text in enumerate(texts):
        status_text.text(f"Translating {i+1}/{len(texts)}: {text[:50]}...")
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"Translate the following {source_lang} text to {target_lang}. Return only the translation."},
                    {"role": "user", "content": text}
                ],
            )
            translation = (resp.choices[0].message.content or "").strip()
        except Exception as e:
            translation = f"[Translation error: {e}]"
            st.warning(f"Translation failed for: {text}")
        translated.append(translation)
        progress_bar.progress((i + 1) / len(texts))
    
    progress_bar.empty()
    status_text.empty()
    return translated

def generate_audio(sentences, output_path, pause_ms, native_speed, foreign_speed, native_code, foreign_code):
    """Generate combined MP3 from language pairs."""
    final_audio = AudioSegment.silent(0)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, (native_text, foreign_text) in enumerate(sentences, 1):
        status_text.text(f"Generating audio {i}/{len(sentences)}: {foreign_text[:50]}...")
        
        # Generate native language audio (plays first, at higher speed)
        native_tts = gTTS(text=native_text, lang=native_code)
        native_path = os.path.join(tempfile.gettempdir(), f"native_{i}.mp3")
        native_tts.save(native_path)
        native_audio = AudioSegment.from_mp3(native_path).speedup(playback_speed=native_speed)
        
        # Generate foreign language audio (plays second, reference)
        foreign_tts = gTTS(text=foreign_text, lang=foreign_code)
        foreign_path = os.path.join(tempfile.gettempdir(), f"foreign_{i}.mp3")
        foreign_tts.save(foreign_path)
        foreign_audio = AudioSegment.from_mp3(foreign_path).speedup(playback_speed=foreign_speed)
        
        # Combine: Native (fast) → Foreign (reference) → Pause
        final_audio += native_audio + foreign_audio + AudioSegment.silent(pause_ms)
        
        # Cleanup
        os.remove(native_path)
        os.remove(foreign_path)
        
        progress_bar.progress(i / len(sentences))
    
    progress_bar.empty()
    status_text.empty()
    
    final_audio.export(output_path, format="mp3")

def parse_file(uploaded_file, native_lang, foreign_lang):
    """Parse uploaded file and detect format."""
    text = uploaded_file.read().decode("utf-8").strip()
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    
    if not lines:
        return None, "File is empty", None
    
    delimiter = detect_delimiter(lines[0])
    
    if delimiter == "ERROR_MULTIPLE":
        return None, "Error: Multiple delimiters (| and ;) found on the same line. Please use only one delimiter type.", None
    
    if delimiter:
        delimiter_name = {'|': 'pipe', ';': 'semicolon'}.get(delimiter, delimiter)
        sentences = []
        for l in lines:
            # Check for multiple delimiters on each line
            line_delimiter = detect_delimiter(l)
            if line_delimiter == "ERROR_MULTIPLE":
                return None, f"Error: Multiple delimiters found on line: {l}", None
            
            parts = [p.strip() for p in l.split(delimiter)]
            if len(parts) == 2 and parts[0] and parts[1]:
                native_text, foreign_text = parts
                sentences.append([native_text, foreign_text])
            else:
                return None, f"Invalid format in line: {l}", None
        return sentences, f"Detected {len(sentences)} {native_lang}-{foreign_lang} pairs (delimiter: {delimiter_name})", False
    else:
        # Foreign language only - needs translation
        foreign_only = lines
        return foreign_only, f"Detected {len(foreign_only)} {foreign_lang}-only phrases", True

st.title("🎧 Superlearning Audio Generator")
st.write("Upload text files to generate spaced repetition audio for language learning.")

col1, col2 = st.columns([2, 1])

with col2:
    st.markdown(f"""
    ### 📄 File Format
    
    **Language pairs** (use `|` or `;`):
    ```
    Dobrý den|Buenos días
    Guten Tag;Buenos días
    Děkuji|Gracias
    ```
    
    **Foreign language only** (auto-translate):
    ```
    Buenos días
    ¿Cómo estás?
    Gracias
    ```
    
    Supported delimiters: `|` or `;` only
    
    ⚠️ Use only one delimiter type per file
    
    ℹ️ Format: First column = {native_lang}, Second column = {foreign_lang}
    """)

with col1:
    uploaded_files = st.file_uploader(
        "Upload your phrases file(s) (.txt)", 
        type=["txt"],
        accept_multiple_files=True
    )

if uploaded_files and native_lang != foreign_lang:
    if len(uploaded_files) > 1:
        st.info(f"📦 Processing {len(uploaded_files)} files in batch mode")
    
    all_sentences = []
    needs_translation = False
    foreign_only_texts = []
    
    for uploaded_file in uploaded_files:
        st.subheader(f"📄 {uploaded_file.name}")
        
        result, message, is_foreign_only = parse_file(uploaded_file, native_lang, foreign_lang)
        
        if result is None:
            st.error(f"Error: {message}")
            continue
        
        st.success(message)
        
        if is_foreign_only:
            needs_translation = True
            foreign_only_texts.extend(result)
        else:
            all_sentences.extend(result)
    
    if needs_translation and foreign_only_texts:
        st.info(f"Translating {len(foreign_only_texts)} {foreign_lang} phrases to {native_lang}...")
        native_translations = translate_text(foreign_only_texts, foreign_lang, native_lang)
        translated_pairs = [[native, foreign] for native, foreign in zip(native_translations, foreign_only_texts)]
        all_sentences.extend(translated_pairs)
    
    if all_sentences:
        st.success(f"✅ Total: {len(all_sentences)} phrase pairs ready")
        
        content_hash = hashlib.md5(str(all_sentences).encode()).hexdigest()
        
        if 'content_hash' not in st.session_state or st.session_state.content_hash != content_hash:
            st.session_state.content_hash = content_hash
            st.session_state.current_sentences = all_sentences.copy()
            for key in list(st.session_state.keys()):
                if isinstance(key, str) and (key.startswith('native_') or key.startswith('foreign_')):
                    del st.session_state[key]
        
        with st.expander("📝 Preview & Edit Translations", expanded=False):
            st.write(f"You can edit the {native_lang} translations before generating audio:")
            
            for i, (native_text, foreign_text) in enumerate(st.session_state.current_sentences[:20], 1):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.text_input(
                        f"{LANGUAGE_OPTIONS[native_lang]['flag']} {native_lang} #{i}",
                        value=native_text,
                        key=f"native_{i}",
                        label_visibility="collapsed"
                    )
                with col_b:
                    st.text_input(
                        f"{LANGUAGE_OPTIONS[foreign_lang]['flag']} {foreign_lang} #{i}",
                        value=foreign_text,
                        key=f"foreign_{i}",
                        disabled=True,
                        label_visibility="collapsed"
                    )
            
            if len(st.session_state.current_sentences) > 20:
                st.info(f"Showing first 20 of {len(st.session_state.current_sentences)} pairs. All pairs will be included in audio.")
        
        sentences_to_use = []
        for i, (native_text, foreign_text) in enumerate(st.session_state.current_sentences, 1):
            edited_native = st.session_state.get(f"native_{i}", native_text) if i <= 20 else native_text
            sentences_to_use.append([edited_native, foreign_text])
        
        if st.button("🎵 Generate Audio", type="primary", use_container_width=True):
            with st.spinner("Generating audio file..."):
                output_path = os.path.join(tempfile.gettempdir(), "superlearning_audio.mp3")
                
                try:
                    generate_audio(
                        sentences_to_use, 
                        output_path, 
                        pause_duration, 
                        native_speedup,
                        foreign_speedup,
                        LANGUAGE_OPTIONS[native_lang]["code"],
                        LANGUAGE_OPTIONS[foreign_lang]["code"]
                    )
                    st.success("🎉 Audio generated successfully!")
                    
                    with open(output_path, "rb") as audio_file:
                        audio_bytes = audio_file.read()
                    
                    st.audio(audio_bytes, format="audio/mp3")
                    
                    st.download_button(
                        label="⬇️ Download MP3",
                        data=audio_bytes,
                        file_name=f"superlearning_{native_lang}_{foreign_lang}_{len(sentences_to_use)}_phrases.mp3",
                        mime="audio/mp3",
                        use_container_width=True
                    )
                    
                except Exception as e:
                    st.error(f"Error generating audio: {e}")

st.markdown("---")
st.caption(f"Audio format: {native_lang} ({native_speedup}x) → {foreign_lang} ({foreign_speedup}x) → {pause_duration}ms pause")
