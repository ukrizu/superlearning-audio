import streamlit as st
from gtts import gTTS
from pydub import AudioSegment
import os
import tempfile
from openai import OpenAI

st.set_page_config(page_title="Spanish-Czech Audio Generator", page_icon="🇪🇸")

PAUSE = 3200
SPEEDUP = 1.15

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
            cz = resp.choices[0].message.content.strip()
        except Exception as e:
            cz = f"[Translation error: {e}]"
            st.warning(f"Translation failed for: {text}")
        translated.append(cz)
        progress_bar.progress((i + 1) / len(spanish_texts))
    
    progress_bar.empty()
    status_text.empty()
    return translated

def generate_audio(sentences, output_path):
    """Generate combined MP3 from Czech-Spanish sentence pairs."""
    final_audio = AudioSegment.silent(0)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, (cz, es) in enumerate(sentences, 1):
        status_text.text(f"Generating audio {i}/{len(sentences)}: {es[:50]}...")
        
        cz_tts = gTTS(text=cz, lang="cs")
        cz_path = os.path.join(tempfile.gettempdir(), f"cz_{i}.mp3")
        cz_tts.save(cz_path)
        cz_audio = AudioSegment.from_mp3(cz_path).speedup(playback_speed=SPEEDUP)
        
        es_tts = gTTS(text=es, lang="es")
        es_path = os.path.join(tempfile.gettempdir(), f"es_{i}.mp3")
        es_tts.save(es_path)
        es_audio = AudioSegment.from_mp3(es_path)
        
        final_audio += cz_audio + es_audio + AudioSegment.silent(PAUSE)
        
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
        return None, "File is empty"
    
    sentences = []
    
    if "|" in lines[0] or ";" in lines[0]:
        delimiter = "|" if "|" in lines[0] else ";"
        for l in lines:
            parts = [p.strip() for p in l.split(delimiter)]
            if len(parts) == 2:
                cz, es = parts
                sentences.append((cz, es))
            else:
                return None, f"Invalid format in line: {l}"
        return sentences, f"Detected {len(sentences)} Czech-Spanish pairs"
    else:
        spanish_only = lines
        st.info(f"Detected {len(spanish_only)} Spanish-only phrases. Will translate to Czech...")
        czech = translate_to_czech(spanish_only)
        sentences = list(zip(czech, spanish_only))
        return sentences, f"Translated {len(sentences)} phrases"

st.title("🇪🇸→🇨🇿 Spanish Audio Generator")
st.write("Upload a text file with Spanish phrases or Spanish-Czech pairs to generate language learning audio.")

st.markdown("""
### File Format
- **Spanish-Czech pairs**: Use `|` or `;` as delimiter
  ```
  Dobrý den|Buenos días
  Jak se máš?|¿Cómo estás?
  ```
- **Spanish only**: One phrase per line (will be auto-translated)
  ```
  Buenos días
  ¿Cómo estás?
  ```
""")

uploaded_file = st.file_uploader("Upload your phrases file (.txt)", type=["txt"])

if uploaded_file:
    sentences, message = parse_file(uploaded_file)
    
    if sentences is None:
        st.error(f"Error: {message}")
    else:
        st.success(message)
        
        with st.expander("Preview phrases"):
            for i, (cz, es) in enumerate(sentences[:10], 1):
                st.write(f"{i}. **CZ:** {cz}")
                st.write(f"   **ES:** {es}")
            if len(sentences) > 10:
                st.write(f"... and {len(sentences) - 10} more")
        
        if st.button("🎵 Generate Audio", type="primary"):
            with st.spinner("Generating audio file..."):
                output_path = os.path.join(tempfile.gettempdir(), "spanish_audio.mp3")
                
                try:
                    generate_audio(sentences, output_path)
                    st.success("Audio generated successfully!")
                    
                    with open(output_path, "rb") as audio_file:
                        audio_bytes = audio_file.read()
                    
                    st.audio(audio_bytes, format="audio/mp3")
                    
                    st.download_button(
                        label="⬇️ Download MP3",
                        data=audio_bytes,
                        file_name="spanish_czech_audio.mp3",
                        mime="audio/mp3"
                    )
                except Exception as e:
                    st.error(f"Error generating audio: {e}")

st.markdown("---")
st.caption("Audio format: Czech (1.15x speed) → Spanish → 3.2s pause")
