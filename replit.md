# Spanish-Czech Audio Generator

## Overview

A Streamlit-based web application that generates bilingual audio files combining Czech and Spanish speech. The app allows users to input Spanish text, automatically translates it to Czech using OpenAI's API, and creates an MP3 file with alternating Czech-Spanish audio pairs with configurable pauses between segments.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Framework
**Decision:** Streamlit  
**Rationale:** Provides rapid development of interactive web interfaces with minimal boilerplate code. Ideal for data-focused applications with built-in progress indicators and file handling.

**Alternatives Considered:**
- Flask (mentioned in attached requirements) - More verbose setup required
- Pros: Simple deployment, built-in UI components, reactive state management
- Cons: Less customization than traditional web frameworks

### Audio Processing Pipeline
**Decision:** gTTS (Google Text-to-Speech) + pydub for audio manipulation  
**Rationale:** gTTS provides free, reliable text-to-speech conversion for multiple languages. Pydub enables audio manipulation (speed adjustment, concatenation, silence insertion) with simple API.

**Architecture:**
1. Czech text generated at 1.15× speed using AudioSegment.speedup()
2. Spanish text played at normal speed
3. 3200ms pause inserted between sentence pairs
4. All segments concatenated into single MP3 file

**Pros:** Free, no API quotas, cross-platform compatibility  
**Cons:** Requires ffmpeg dependency, limited voice customization

### Translation Service
**Decision:** OpenAI GPT-4o-mini API for Spanish-to-Czech translation  
**Rationale:** Provides high-quality contextual translations with simple API integration. Model selected for cost efficiency while maintaining translation quality.

**Implementation:**
- Prompt-based translation with system role specifying output format
- Error handling with fallback messages
- Per-sentence translation with progress tracking

**Pros:** High translation quality, handles context and idioms well  
**Cons:** Requires API key and incurs costs, needs internet connectivity

### State Management
**Decision:** Streamlit's native session state and reactive rendering  
**Rationale:** Built-in progress indicators and status updates align with audio generation workflow requirements.

**Features:**
- Progress bars for translation and audio generation phases
- Status text showing current processing step
- Automatic cleanup of UI elements after completion

### File Handling
**Decision:** tempfile module for intermediate audio files  
**Rationale:** Ensures cleanup of temporary Czech/Spanish MP3 files during processing. Final output provided to user via Streamlit download button.

## External Dependencies

### Core Services
- **OpenAI API** - GPT-4o-mini model for Spanish-to-Czech translation
  - Requires: OPENAI_API_KEY environment variable
  - Usage: Chat completions endpoint for translation requests

### Python Libraries
- **streamlit** - Web application framework and UI components
- **gtts** (Google Text-to-Speech) - Speech synthesis for Czech and Spanish
- **pydub** - Audio manipulation (speed control, concatenation, silence generation)
  - Requires: ffmpeg system dependency
- **openai** - Official OpenAI Python client library

### System Dependencies
- **ffmpeg** - Required by pydub for audio format conversion and manipulation
- Temporary file system access for intermediate audio storage

### Configuration
- Environment variables: `OPENAI_API_KEY` (required for translation functionality)
- Constants: `PAUSE = 3200` (milliseconds), `SPEEDUP = 1.15` (Czech playback speed multiplier)